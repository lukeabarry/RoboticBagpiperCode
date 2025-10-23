from mido import MidiFile
midifilepath = 'MIDIFiles/scottish_1_(c)taylor.mid'
midi_data = MidiFile(midifilepath)
track = enumerate(midi_data.tracks)

