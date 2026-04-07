from mido import MidiFile
import time
import threading
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - running in simulation mode")
    GPIO_AVAILABLE = False

class BagpipeController:
    def __init__(self):
        # GPIO pin mapping for bagpipe holes/keys
        # Adjust these pin numbers
        """
        self.hole_to_gpio = { #change as needed (outdated)
            1: 18,
            2: 19,
            3: 20,
            4: 21,
            5: 22,
            6: 23,
            7: 24,
            8: 25,
        }
        """
        self.note_to_gpio = {
        #regular notes on the scale
            67: [26, 19, 20, 21, 16, 6, 5, 7],   # low G
            69: [26, 19, 20, 21, 16, 6, 5],      # A
            71: [26, 19, 20, 21, 16, 6],          # B
            72: [26, 19, 20, 21, 16, 7],         # C
            73: [26, 19, 20, 21, 16],            # C sharp
            74: [26, 19, 20, 21, 7],            # D
            76: [26, 19, 20, 16, 6, 5],         # E
            78: [26, 19, 20, 6, 5],            # F sharp
            79: [26, 20, 6, 5, 7],         # high G
            81: [20, 16, 6, 5],       # high A

            68: [26, 20, 6, 5, 7],      #low G grace -> high G
            70: [26, 20, 6, 5, 7],      #A grace -> high G
            75: [26, 20, 6, 5, 7],      #D grace -> high G
            77: [26, 20, 6, 5, 7],      #E grace -> high G
            80: [26, 16, 6, 5],     #high G grace -> high A
            82: [26, 20, 6, 5, 7]       #high A grace -> high G

        }
        # Bellows/air pressure control
        self.bellows_pin = 23

        self.setup_gpio()
        self.active_notes = set()
        self.active_pins = set()

    def setup_gpio(self):
        if not GPIO_AVAILABLE:
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in self.note_to_gpio.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        GPIO.setup(self.bellows_pin, GPIO.OUT)
        GPIO.output(self.bellows_pin, GPIO.LOW)

    def start_bellows(self):
        """Start the bellows/air supply"""
        if GPIO_AVAILABLE:
            GPIO.output(self.bellows_pin, GPIO.HIGH)
        print("Bellows started")

    def stop_bellows(self):
        """Stop the bellows/air supply"""
        if GPIO_AVAILABLE:
            GPIO.output(self.bellows_pin, GPIO.LOW)
        print("Bellows stopped")

    def note_on(self, note_number, velocity):
        if note_number not in self.note_to_gpio:
            print(f"Note {note_number} not in GPIO map")
            return

        target_pins = set(self.note_to_gpio[note_number])
        pins_to_raise = target_pins - self.active_pins
        pins_to_lower = self.active_pins - target_pins

        if GPIO_AVAILABLE:
            if pins_to_lower:
                GPIO.output(list(pins_to_lower), GPIO.LOW)
            if pins_to_raise:
                GPIO.output(list(pins_to_raise), GPIO.HIGH)

        self.active_pins = target_pins
        self.active_notes.add(note_number)
        print(f"Note ON: {note_number} | raised={pins_to_raise} lowered={pins_to_lower}")

    def note_off(self, note_number):
        if note_number not in self.note_to_gpio:
            print(f"Note {note_number} not in GPIO map")
            return

        pins_this_note = set(self.note_to_gpio[note_number])
        pins_still_needed = set()
        for other_note in self.active_notes:
            if other_note != note_number:
                pins_still_needed.update(self.note_to_gpio[other_note])

        pins_to_lower = pins_this_note - pins_still_needed
        if GPIO_AVAILABLE and pins_to_lower:
            GPIO.output(list(pins_to_lower), GPIO.LOW)

        self.active_pins -= pins_to_lower
        self.active_notes.discard(note_number)
        print(f"Note OFF: {note_number} | lowered={pins_to_lower} kept={pins_this_note & pins_still_needed}")

    def all_notes_off(self):
        if GPIO_AVAILABLE and self.active_pins:
            GPIO.output(list(self.active_pins), GPIO.LOW)
        self.active_pins.clear()
        self.active_notes.clear()

    def cleanup(self):
        self.all_notes_off()
        self.stop_bellows()
        if GPIO_AVAILABLE:
            GPIO.cleanup()

class MIDIBagpipePlayer:
    def __init__(self, midi_file_path):
        self.midi_file_path = midi_file_path
        self.bagpipe = BagpipeController()
        self.tempo = 500000  # Default tempo (500,000 microseconds per beat)
        self.ticks_per_beat = 480  # Default MIDI resolution
        self.playing = False

    def load_midi_file(self):
        try:
            self.midi_data = MidiFile(self.midi_file_path)
            self.ticks_per_beat = self.midi_data.ticks_per_beat
            print(f"Loaded MIDI file: {self.midi_file_path}")
            print(f"Ticks per beat: {self.ticks_per_beat}")
            print(f"Number of tracks: {len(self.midi_data.tracks)}")

            # Print track information
            for i, track in enumerate(self.midi_data.tracks):
                print(f"Track {i}: {track.name}")

        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            return False
        return True

    def ticks_to_seconds(self, ticks):
        # tempo is in microseconds per beat
        # ticks_per_beat is the MIDI resolution
        seconds_per_tick = (self.tempo / 1000000.0) / self.ticks_per_beat
        return ticks * seconds_per_tick

    def play_track(self, track_index=1, lcd=None, progress_callback=None):
        if not hasattr(self, 'midi_data'):
            print("No MIDI file loaded")
            return

        if track_index >= len(self.midi_data.tracks):
            print(f"Track {track_index} does not exist")
            return

        track = self.midi_data.tracks[track_index]
        print(f"Playing track {track_index}: {track.name}")

        # Start bagpipe systems
        self.bagpipe.start_bellows()
        self.playing = True

        time.sleep(5)  # Give bellows time to build pressure (change this as needed)

        total_time = 0
        for msg in track:
            if msg.time > 0:
                total_time += self.ticks_to_seconds(msg.time)

        current_time = 0
        last_update = 0

        try:
            for msg in track:
                if not self.playing:
                    break

                # Handle timing
                if msg.time > 0:
                    sleep_time = self.ticks_to_seconds(msg.time)
                    time.sleep(sleep_time)
                    current_time += sleep_time

                if lcd and progress_callback and (current_time - last_update) >= 0.5:
                    progress_callback(current_time, total_time)
                    last_update = current_time

                # Handle different message types
                if msg.type == 'set_tempo':
                    self.tempo = msg.tempo
                    print(f"Tempo changed to: {msg.tempo} microseconds per beat")

                elif msg.type == 'note_on' and msg.velocity > 0:
                    self.bagpipe.note_on(msg.note, msg.velocity)

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    self.bagpipe.note_off(msg.note)

                elif msg.type == 'program_change':
                    print(f"Program change: {msg.program}")

        except KeyboardInterrupt:
            print("\nPlayback interrupted by user")
        except Exception as e:
            print(f"Error during playback: {e}")
        finally:
            self.stop_playback()

    def stop_playback(self):
        self.playing = False
        self.bagpipe.all_notes_off()
        self.bagpipe.stop_bellows()

    def cleanup(self):
        self.stop_playback()
        self.bagpipe.cleanup()

# Main execution
if __name__ == "__main__":
    # Configuration
    midi_file_path = 'MIDIFiles/scottish_1_(c)taylor.mid'

    player = MIDIBagpipePlayer(midi_file_path)

    try:
        # Load the MIDI file
        if player.load_midi_file():
            print("\nStarting playback in 3 seconds...")
            time.sleep(3)

            # Play the track (change track index as needed)
            player.play_track(track_index=1)
        else:
            print("Failed to load MIDI file")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        player.cleanup()
        print("Cleanup complete")