import tkinter as tk
from tkinter import ttk, filedialog
from mido import MidiFile
import time
import threading
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("GPIO not available - running in simulation mode")
    GPIO_AVAILABLE = False


class BagpipeController:
    def __init__(self, pin_status_callback=None):
        # GPIO pin mapping for bagpipe holes/keys
        self.note_to_gpio = {
            67: [18, 19, 20, 21, 22, 23, 24, 25],   # low G
            69: [18, 19, 20, 21, 22, 23, 24],       # A
            71: [18, 19, 20, 21, 22, 23],           # B
            72: [18, 19, 20, 21, 22, 25],          # C
            73: [18, 19, 20, 21, 22],              # C sharp
            74: [18, 19, 20, 21, 25],              # D
            76: [18, 19, 20, 22, 23, 24],          # E
            78: [18, 19, 20, 23, 24],              # F sharp
            79: [18, 20, 23, 24, 25],              # high G
            81: [20, 22, 23, 24]                   # high A
        }
        
        # All unique pins used (10 pins)
        self.all_pins = sorted(set(pin for pins in self.note_to_gpio.values() for pin in pins))
        
        # Bellows/air pressure control
        self.bellows_pin = 17
        
        # Callback to update GUI
        self.pin_status_callback = pin_status_callback
        
        self.setup_gpio()
        self.active_notes = set()
        self.pin_states = {pin: False for pin in self.all_pins}
        
    def setup_gpio(self):
        if not GPIO_AVAILABLE:
            return
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pins in self.note_to_gpio.values():
            for pin in pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
        GPIO.setup(self.bellows_pin, GPIO.OUT)
        GPIO.output(self.bellows_pin, GPIO.LOW)
        
    def start_bellows(self):
        if GPIO_AVAILABLE:
            GPIO.output(self.bellows_pin, GPIO.HIGH)
        print("Bellows started")
        
    def stop_bellows(self):
        if GPIO_AVAILABLE:
            GPIO.output(self.bellows_pin, GPIO.LOW)
        print("Bellows stopped")
        
    def note_on(self, note_number, velocity):
        if note_number in self.note_to_gpio:
            pins = self.note_to_gpio[note_number]
            if GPIO_AVAILABLE:
                for pin in pins:
                    GPIO.output(pin, GPIO.HIGH)
            
            # Update pin states
            for pin in pins:
                self.pin_states[pin] = True
            
            self.active_notes.add(note_number)
            print(f"Note ON: {note_number} Velocity: {velocity}")
            
            # Update GUI
            if self.pin_status_callback:
                self.pin_status_callback(self.pin_states.copy())
        else:
            print(f"Note {note_number} not mapped to GPIO")

    def note_off(self, note_number):
        if note_number in self.note_to_gpio:
            pins = self.note_to_gpio[note_number]
            
            # Remove this note from active notes
            self.active_notes.discard(note_number)
            
            # Recalculate which pins should be active based on remaining active notes
            active_pins = set()
            for active_note in self.active_notes:
                active_pins.update(self.note_to_gpio[active_note])
            
            # Update pins that are no longer needed
            for pin in pins:
                if pin not in active_pins:
                    if GPIO_AVAILABLE:
                        GPIO.output(pin, GPIO.LOW)
                    self.pin_states[pin] = False
                    
            print(f"Note OFF: {note_number}")
            
            # Update GUI
            if self.pin_status_callback:
                self.pin_status_callback(self.pin_states.copy())
        else:
            print(f"Note {note_number} not mapped to GPIO")
            
    def all_notes_off(self):
        for note in list(self.active_notes):
            self.note_off(note)
            
    def cleanup(self):
        self.all_notes_off()
        self.stop_bellows()
        if GPIO_AVAILABLE:
            GPIO.cleanup()


class MIDIBagpipePlayer:
    def __init__(self, pin_status_callback=None):
        self.bagpipe = BagpipeController(pin_status_callback)
        self.tempo = 500000
        self.ticks_per_beat = 480
        self.playing = False
        self.play_thread = None
        self.midi_file_path = None
        
    def load_midi_file(self, midi_file_path):
        try:
            self.midi_file_path = midi_file_path
            self.midi_data = MidiFile(midi_file_path)
            self.ticks_per_beat = self.midi_data.ticks_per_beat
            print(f"Loaded MIDI file: {midi_file_path}")
            print(f"Ticks per beat: {self.ticks_per_beat}")
            print(f"Number of tracks: {len(self.midi_data.tracks)}")
            
            for i, track in enumerate(self.midi_data.tracks):
                print(f"Track {i}: {track.name}")
                
        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            return False
        return True
        
    def ticks_to_seconds(self, ticks):
        seconds_per_tick = (self.tempo / 1000000.0) / self.ticks_per_beat
        return ticks * seconds_per_tick
        
    def play_track(self, track_index=1):
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
        time.sleep(2)  # Give bellows time to build pressure
        
        self.playing = True
        
        try:
            for msg in track:
                if not self.playing:
                    break
                    
                if msg.time > 0:
                    sleep_time = self.ticks_to_seconds(msg.time)
                    time.sleep(sleep_time)
                
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
            
    def start_playback(self, track_index=1):
        if self.play_thread and self.play_thread.is_alive():
            print("Playback already in progress")
            return
            
        self.play_thread = threading.Thread(target=self.play_track, args=(track_index,))
        self.play_thread.daemon = True
        self.play_thread.start()
            
    def stop_playback(self):
        self.playing = False
        self.bagpipe.all_notes_off()
        self.bagpipe.stop_bellows()
        
    def cleanup(self):
        self.stop_playback()
        self.bagpipe.cleanup()


class BagpipeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robotic Bagpipe Controller")
        self.root.geometry("600x400")
        
        # Create player
        self.player = MIDIBagpipePlayer(pin_status_callback=self.update_pin_display)
        
        # Default MIDI file
        self.current_file = "MIDIFiles/scottish_1_(c)taylor.mid"
        
        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, columnspan=5, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(file_frame, text="MIDI File:").grid(row=0, column=0, padx=5)
        self.file_label = ttk.Label(file_frame, text=self.current_file, relief=tk.SUNKEN, width=40)
        self.file_label.grid(row=0, column=1, padx=5)
        
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)
        ttk.Button(file_frame, text="Load", command=self.load_file).grid(row=0, column=3, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=5, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="START", command=self.start_playback, width=15)
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = ttk.Button(button_frame, text="STOP", command=self.stop_playback, width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)
        
        # Pin status display
        status_frame = ttk.LabelFrame(main_frame, text="Pin Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=5, pady=10, sticky=(tk.W, tk.E))
        
        # Create 10 boxes for the pins
        self.pin_boxes = {}
        pins = self.player.bagpipe.all_pins  # Get all 10 unique pins
        
        for i, pin in enumerate(pins):
            row = i // 5
            col = i % 5
            
            frame = ttk.Frame(status_frame)
            frame.grid(row=row*2, column=col, padx=5, pady=5)
            
            label = ttk.Label(frame, text=f"Pin {pin}")
            label.pack()
            
            canvas = tk.Canvas(frame, width=60, height=60, bg='white', highlightthickness=2)
            canvas.pack()
            
            self.pin_boxes[pin] = canvas
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=10)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Load default file
        self.load_file()
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select MIDI file",
            filetypes=(("MIDI files", "*.mid"), ("All files", "*.*"))
        )
        if filename:
            self.current_file = filename
            self.file_label.config(text=filename)
            
    def load_file(self):
        if self.player.load_midi_file(self.current_file):
            self.status_label.config(text=f"Loaded: {self.current_file}")
        else:
            self.status_label.config(text="Error loading file")
            
    def start_playback(self):
        self.player.start_playback(track_index=1)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Playing...")
        
    def stop_playback(self):
        self.player.stop_playback()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped")
        
    def update_pin_display(self, pin_states):
        """Update the pin display boxes based on pin states"""
        for pin, state in pin_states.items():
            if pin in self.pin_boxes:
                canvas = self.pin_boxes[pin]
                color = 'green' if state else 'white'
                canvas.config(bg=color)
                
    def cleanup(self):
        self.player.cleanup()


def main():
    root = tk.Tk()
    app = BagpipeGUI(root)
    
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
