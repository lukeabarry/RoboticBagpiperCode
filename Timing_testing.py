import MIDI_interpretation_module

class Tester:
    def analyze_timing_requirements(self):
        print("Analyzing timing requirements...")
        min_note_gap = float('inf')
        max_notes_simultaneous = 0
        note_durations = []
        note_gaps = []
        current_notes = {}
        last_event_time = 0

        for track_idx, track in enumerate(self.midi_data.tracks):
            if track_idx == 0: continue 
    
        current_time = 0
        current_tempo = self.tempo