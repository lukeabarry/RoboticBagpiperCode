import sys
import tty
import termios
import os
import time
import threading
from pathlib import Path

from MIDI_interpretation_module import MIDIBagpipePlayer

LCD_I2C_ADDR = 0x27
LCD_COLS = 16
LCD_ROWS = 2

MIDI_FOLDER = "MIDIFiles"

SIMULATE_MODE = True

def load_songs():
    script_dir = Path(__file__).parent
    midi_dir = script_dir / MIDI_FOLDER

    if not midi_dir.exists():
        print(f"Error:{MIDI_FOLDER} not found!")
        return []
    
    midi_files = list(midi_dir.glob("*.mid"))

    songs = sorted([(f.stem, str(f)) for f in midi_files])

    if not songs:
        print(f"No MIDI files found in {MIDI_FOLDER}!")

    return songs
    
# ADDED:
class SimulatedLCD:
    """Mock LCD for testing without hardware"""
    def __init__(self, **kwargs):
        self.cols = kwargs.get('cols', 16)
        self.rows = kwargs.get('rows', 2)
        self.cursor_pos = (0, 0)
        self.display = [' ' * self.cols for _ in range(self.rows)]
        print(f"[Simulated LCD initialized: {self.cols}x{self.rows}]")
    
    @property
    def cursor_pos(self):
        return self._cursor_pos
    
    @cursor_pos.setter
    def cursor_pos(self, value):
        self._cursor_pos = value
    
    def clear(self):
        self.display = [' ' * self.cols for _ in range(self.rows)]
        print("\n[LCD CLEARED]")
    
    def write_string(self, text):
        row, col = self.cursor_pos
        if '\n' in text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if row + i < self.rows:
                    # Replace characters starting at cursor position
                    line_list = list(self.display[row + i])
                    for j, char in enumerate(line):
                        if col + j < self.cols:
                            line_list[col + j] = char
                    self.display[row + i] = ''.join(line_list)
        else:
            line_list = list(self.display[row])
            for i, char in enumerate(text):
                if col + i < self.cols:
                    line_list[col + i] = char
            self.display[row] = ''.join(line_list)
        
        self._print_display()
    
    def _print_display(self):
        print("┌" + "─" * self.cols + "┐")
        for line in self.display:
            print("│" + line + "│")
        print("└" + "─" * self.cols + "┘")
    
    def close(self):
        print("[LCD closed]")

class SongMenu:
    def __init__(self, songs, lcd):
        self.songs = songs
        self.lcd = lcd
        self.curr_idx = 0
        self.player = None
        self.playback_thread = None
       
    def display_current(self):
        self.lcd.clear()

        song = self.songs[self.curr_idx][0]
        left_arrow = '<' if self.curr_idx > 0 else ' '
        right_arrow = '>' if self.curr_idx < len(self.songs) - 1 else ' '

        max_song_length = LCD_COLS - 2
        if len(song) > max_song_length:
            song = song[:max_song_length - 3] + '...'

        line1 = f"{left_arrow}{song.center(LCD_COLS - 2)}{right_arrow}"

        line2 = "[Hit Enter to Play]".center(LCD_COLS)

        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(line1)
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(line2)

    def next_song(self):
        if self.curr_idx < len(self.songs) - 1:
            self.curr_idx += 1
            self.display_current()
            return True
        return False
    
    def prev_song(self):
        if self.curr_idx > 0:
            self.curr_idx -= 1
            self.display_current()
            return True
        return False
    
    def select_song(self):
        song_name, song_path = self.songs[self.curr_idx]
        print(f"\nSelected: {song_name}")

        if self.player and self.player.playing:
            self.stop_song()
            time.sleep(1)

        self.player = MIDIBagpipePlayer(song_path)
        if self.player.load_midi_file():
            self.lcd.clear()
            self.lcd.write_string(f"Loading:\n{song_name[:LCD_COLS]}")

            self.playback_thread = threading.Thread(target=self.player.play_track, args=(1, self.lcd, self.song_progress))
            self.playback_thread.daemon = True
            self.playback_thread.start()

        else:
            self.lcd.clear()
            self.lcd.write_string("Failed to load MIDI file!")
            time.sleep(2)
            self.display_current()

    def song_progress(self, current_time, total_time):
        if total_time > 0:
            progress = current_time / total_time
        else:
            progress = 0

        filled_blocks = int(progress * 16)
        bar = '█' * filled_blocks + '░' * (16 - filled_blocks)

        curr_mins  = int(current_time // 60)
        curr_secs  = int(current_time % 60)
        total_mins = int(total_time // 60)
        total_secs = int(total_time % 60)

        time_str = f"{curr_mins}:{curr_secs:02d}{' ' * 7}{total_mins}:{total_secs:02d}"

        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(bar)
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(time_str)

    def stop_song(self):
        print("\nStopping playback...")

        if self.player:
            self.player.stop_playback()
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=2)

        self.lcd.clear()
        self.lcd.write_string("Playback Stopped")
        time.sleep(2)
        self.display_current()

    def cleanup(self):
        if self.player:
            self.player.cleanup()


def get_key():

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

        if ch == '\x1b':  # Escape character
            ch += sys.stdin.read(2)
            if ch == '\x1b[C':  # Right arrow
                return 'RIGHT'
            elif ch == '\x1b[D':  # Left arrow
                return 'LEFT'
            elif ch == '\x1b[A':  # Up arrow
                return 'UP'
            elif ch == '\x1b[B':  # Down arrow
                return 'DOWN'
        elif ch == '\r':  # Enter key
            return 'SELECT'
        elif ch == 'q' or ch == '\x03':  # Ctrl+C or 'q' to quit
            return 'QUIT'
            
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return None

def main():
    songs = load_songs()
    if not songs:
        print("No MIDI files found. Add .mid files to the MIDIFiles folder and restart.")
        return
    
    print(f"Found {len(songs)} MIDI File(s)")

    try:
        if SIMULATE_MODE:
            print("Running in SIMULATION MODE (no LCD hardware required)")
            lcd = SimulatedLCD(cols=LCD_COLS, rows=LCD_ROWS)
        else:
            from RPLCD.i2c import CharLCD
            lcd = CharLCD(i2c_expander='PCF8574', address=LCD_I2C_ADDR, port=1, cols=LCD_COLS, rows=LCD_ROWS)
            lcd.clear()
    except Exception as e:
        print(f"Error initializing LCD: {e}")
        return
    
    menu = SongMenu(songs, lcd)
    menu.display_current()

    print("Song Menu Active\n")
    print("Use LEFT/RIGHT arrows to navigate, ENTER/UP to select, DOWN to stop playback, 'q' to quit\n")

    try:
        while True:
            key = get_key()
            if key == 'RIGHT':
                menu.next_song()
            elif key == 'LEFT':
                menu.prev_song()
            elif key == 'SELECT' or key == 'UP':
                menu.select_song()
            elif key == 'DOWN':
                menu.stop_song()
            elif key == 'QUIT':
                break
        
    except KeyboardInterrupt:
        pass
    finally:
        menu.cleanup()
        lcd.clear()
        lcd.write_string("Goodbye!")
        time.sleep(2)
        lcd.clear()
        lcd.close()
        print("\nMenu Now Inactive")

if __name__ == "__main__":
    main()
