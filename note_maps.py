from mido import MidiFile
mid = MidiFile('MIDIFiles/devkitchenP.mid')
mapped = {67, 69, 71, 72, 73, 74, 76, 78, 79, 81}
for i, track in enumerate(mid.tracks):
	notes = set()
	for msg in track:
		if msg.type == 'note_on' and msg.velocity > 0:
			notes.add(msg.note)
	if notes:
		in_range = notes & mapped
		out_of_range = notes - mapped 
		print(f"Track {i} '{track.name}': mapped={sorted(in_range)} unmapped={sorted(out_of_range)}")