from mido import MidiFile
import time
midifilepath = 'MIDIFiles/devkitchenP.mid'
midi_data = MidiFile(midifilepath)
track = midi_data.tracks[1]  # Accessing the second track (index 1)

print('Track {}: {}'.format(1, track.name))
for msg in track:
    if msg.type == 'set_tempo':
        print(f"Set Tempo: {msg.tempo} Time: {msg.time}")
    elif msg.type == 'note_on':
        print(f"Note On: Note {msg.note} Velocity {msg.velocity} Time: {msg.time}")
        wait_time = msg.time
        wait_time_seconds = wait_time / 1000.0  # Convert milliseconds to seconds
        time.sleep(wait_time_seconds)
    elif msg.type == 'note_off':
        print(f"Note Off: Note {msg.note} Velocity {msg.velocity} Time: {msg.time}")
        wait_time = msg.time
        wait_time_seconds = wait_time / 1000.0  # Convert milliseconds to seconds
        time.sleep(wait_time_seconds)
