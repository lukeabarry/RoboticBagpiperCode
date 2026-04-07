import sys
import tty
import termios
import os
import time
import threading
import shutil
import queue
import subprocess
from pathlib import Path

try:
    import evdev
    EVDEV_AVAILABLE = True
except ImportError:
    EVEDEV_AVAILABLE = False
    print("evdev not available, IR remote is disabled.")

from MIDI_interpretation_with_LCD import MIDIBagpipePlayer

LCD_I2C_ADDR = 0x27
LCD_COLS = 16
LCD_ROWS = 2

MIDI_FOLDER = "MIDIFiles"
USB_MOUNT_PATH = "/media/team-38"

SIMULATE_MODE = False

IR_CODES = {
    0x18: 'UP',
    0x52: 'DOWN',
    0x08: 'LEFT',
    0x5a: 'RIGHT',
    0x18: 'UP',
    0x1c: 'SELECT',
}

def lcd_line(text, width=LCD_COLS):
    return text[:width].ljust(width)

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

def welcome_text(lcd):
    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string(lcd_line("Spot, the"))
    lcd.cursor_pos = (1,0)
    lcd.write_string(lcd_line("Robotic Bagpiper"))
    time.sleep(3)

def bagpipe_animation(lcd, loops=4):
    pipe_top_old = (
        0b01010,
        0b01010,
        0b01010,
        0b11111,
        0b11111,
        0b11111,
        0b01110,
        0b00100,
    )
    pipe_top = (
        0b00011,
        0b00011,
        0b00011,
        0b00011,
        0b00011,
        0b00011,
        0b00011,
        0b11111,
    )
    pipe_low = (
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b00000,
        0b00000,
    )
    bag_full_l = (
        0b00111,
        0b01111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b01111,
        0b00111,
    )
    bag_squeezed_l = (
        0b00011,
        0b00111,
        0b01111,
        0b11111,
        0b11111,
        0b01111,
        0b00111,
        0b00000,
    )
    bag_full_r = (
        0b11100,
        0b11110,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11110,
        0b11100,
    )
    bag_squeezed_r = (
        0b11000,
        0b11100,
        0b11110,
        0b11111,
        0b11111,
        0b11110,
        0b11100,
        0b00000,
    )
    bag_squeezed = (
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b00000,
    )
    music_note = (
        0b01111,
        0b01001,
        0b01001,
        0b11011,
        0b11011,
        0b00000,
        0b00000,
        0b00000,
    )
    lcd.create_char(1, pipe_top)
    lcd.create_char(2, pipe_low)
    lcd.create_char(3, bag_full_l)
    lcd.create_char(4, bag_squeezed_l)
    lcd.create_char(5, bag_squeezed)
    lcd.create_char(6, bag_full_r)
    lcd.create_char(7, bag_squeezed_r)
    lcd.create_char(0, music_note)

    line1 = chr(1)*3
    line2 = chr(2) + chr(3) + chr(255)*3 + chr(6) + chr(2)*2
    line3 = chr(2) + chr(4) + chr(5)*3 + chr(7) + chr(2)*2 + chr(0)*2

    for i in range(loops):
        lcd.clear()
        lcd.cursor_pos = (0,5)
        lcd.write_string(line1)
        lcd.cursor_pos = (1,3)
        lcd.write_string(line2)
        time.sleep(0.5)

        lcd.cursor_pos = (1,3)
        lcd.write_string(line3)
        time.sleep(0.5)

def run_splash_seq(lcd):
    welcome_text(lcd)
    bagpipe_animation(lcd, loops=4)

    lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string(lcd_line("SYSTEM READY".center(16)))
    lcd.cursor_pos = (1,0)
    lcd.write_string(lcd_line("Welcome piper!!".center(16)))
    time.sleep(2)
    lcd.clear()

class BaseMenu:
    def __init__(self, lcd):
        self.lcd = lcd
        self.options = ["Song Library", "Load Songs"]
        self.curr_idx = 0

    def display(self):
        self.lcd.clear()
        for row, option in enumerate(self.options):
            self.lcd.cursor_pos = (row, 0)
            prefix = '>' if row == self.curr_idx else ' '
            self.lcd.write_string(lcd_line(f"{prefix} {option}"))

    def next_option(self):
        self.curr_idx = (self.curr_idx + 1) % len(self.options)
        self.display()

    def prev_option(self):
        self.curr_idx = (self.curr_idx - 1) % len(self.options)
        self.display()

    def selected(self):
        return self.options[self.curr_idx]

class SongMenu:
    def __init__(self, songs, lcd):
        self.songs = songs
        self.lcd = lcd
        self.curr_idx = 0
        self.player = None
        self.playback_thread = None
        self.loading = False

    def display_current(self):
        time.sleep(0.1)
        self.lcd.clear()
        time.sleep(0.05)

        song = self.songs[self.curr_idx][0]
        left_arrow = '<' if self.curr_idx > 0 else ' '
        right_arrow = '>' if self.curr_idx < len(self.songs) - 1 else ' '

        max_song_length = LCD_COLS - 2
        if len(song) > max_song_length:
            song = song[:max_song_length - 3] + '...'

        line1 = f"{left_arrow}{song.center(LCD_COLS - 2)}{right_arrow}"

        line2 = "[Enter to Play]".center(LCD_COLS)

        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(lcd_line(line1))
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(lcd_line(line2))

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
        """selected song is played and screen updated"""

        song_name, song_path = self.songs[self.curr_idx]
        print(f"\nSelected: {song_name}")

        if self.player and self.player.playing:
            self.stop_song()
            time.sleep(1)

        self.player = MIDIBagpipePlayer(song_path)
        if self.player.load_midi_file():
            self.lcd.clear()
            self.lcd.write_string(lcd_line(f"Loading:"))
            self.lcd.cursor_pos = (1,0)
            self.lcd.write_string(lcd_line(song_name))

            self.playback_thread = threading.Thread(target=self.player.play_track, args=(1, self.lcd, self.song_progress))
            self.playback_thread.daemon = True
            self.playback_thread.start()

        else:
            self.lcd.clear()
            self.lcd.write_string(lcd_line("Failed to load!"))
            time.sleep(2)
            self.display_current()

    def song_progress(self, current_time, total_time):
        """displays the progress bar and time elapsed on the screen when song has been played"""

        empty_block = (
            0b11111,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b11111,
        )
        self.lcd.create_char(0, empty_block)

        if total_time > 0:
            progress = current_time / total_time
        else:
            progress = 0

        filled_blocks = int(progress * LCD_COLS)
        bar = chr(255) * filled_blocks + chr(0) * (LCD_COLS - filled_blocks)

        curr_mins  = int(current_time // 60)
        curr_secs  = int(current_time % 60)
        total_mins = int(total_time // 60)
        total_secs = int(total_time % 60)

        time_str = f"{curr_mins}:{curr_secs:02d}/{total_mins}:{total_secs:02d}".ljust(LCD_COLS)

        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(lcd_line(bar))
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(lcd_line(time_str))

    def stop_song(self):
        """Ends the playback of the active song"""
        print("\nStopping playback...")

        if self.player:
            self.player.stop_playback()
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=2)

        self.lcd.clear()
        self.lcd.write_string(lcd_line("Playback Stopped"))
        time.sleep(2)
        self.display_current()

    def is_busy(self):
        """checks to see if the song is loading or playing"""
        return self.playback_thread is not None and self.playback_thread.is_alive()

    def cleanup(self):
        if self.player:
            self.player.cleanup()

class LoadMenu:
    def __init__(self, lcd):
        self.lcd = lcd
        self.current_path = None
        self.entries = []
        self.curr_idx = 0
        self.state = "waiting"
        self.dest_dir = Path(__file__).parent / MIDI_FOLDER

    def enter(self):
        """called when Load Songs becomes the active menu"""
        self.state = "waiting"
        self._show_waiting()

    def _show_waiting(self):
        """prompts the user to insert a usb"""
        self.lcd.clear()
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(lcd_line("Insert USB"))
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(lcd_line("drive..."))

    def _detect_usb(self):
        """returns the first detected usb mounting path or none"""
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].startswith(USB_MOUNT_PATH):
                        return Path(parts[1])
        except Exception:
           pass
        return None

    def _load_entries(self, path):
        entries = []
        try:
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    entries.append((f"/{item.name}", item, True))
                elif item.suffix.lower() == ".mid":
                    entries.append((item.name, item, False))
        except PermissionError:
            pass_none

        if self.current_path != self._usb_root:
            entries.insert(0, ("..", path.parent, True))

        return entries

    def _show_browser(self):
        print("called _show_browser")
        if not self.entries:
            print("no entries")
            self.lcd.clear()
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(lcd_line("No .mid files"))
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(lcd_line("found here"))
            return

        name, _, is_dir = self.entries[self.curr_idx]
        left_arrow = '<' if self.curr_idx > 0 else ' '
        right_arrow = '>' if self.curr_idx < len(self.entries) -1 else ' '

        self.lcd.clear()
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(lcd_line(f"{left_arrow}{name.center(LCD_COLS - 2)}{right_arrow}"))
        self.lcd.cursor_pos = (1, 0)
        if is_dir:
            self.lcd.write_string(lcd_line("[Open folder]".center(LCD_COLS)))
        else:
            self.lcd.write_string(lcd_line("[Select]".center(LCD_COLS)))

    def _show_notice(self, message_line1, message_line2):
        self.lcd.clear()
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(lcd_line(message_line1))
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(lcd_line(message_line2))

    def poll(self):
        if self.state != "waiting":
            return
        usb = self._detect_usb()
        if usb:
            try:
                print(f"transition to browsing: {usb}")
                self._usb_root = usb
                self.current_path = usb
                self.entries = self._load_entries(usb)
                print(f"Entries Loaded: {self.entries}")
                self.curr_idx = 0
                self.state = "browsing"
                print("entering browsing")
                self._show_browser()
                print("browsed")
            except Exception as e:
                print(f"Error in poll transition: {e}")

    def handle_key(self, key):
        if self.state == "waiting":
            if key == 'DOWN':
                return "back"

        elif self.state == "browsing":
            if key == 'RIGHT':
                if self.curr_idx < len(self.entries) - 1:
                    self.curr_idx += 1
                    self._show_browser()
            elif key == 'LEFT':
                if self.curr_idx > 0:
                    self.curr_idx -= 1
                    self._show_browser()
            elif key == 'SELECT' or key == 'UP':
                if self.entries:
                    name, path, is_dir = self.entries[self.curr_idx]
                    if is_dir:
                        self.current_path = path
                        self.entries = self._load_entries(path)
                        self.curr_idx = 0
                        self._show_browser()
                    else:
                        self._copy_file(path)
            elif key == 'DOWN':
                return "back"

        elif self.state == "notice":
            if key == 'SELECT' or key == 'UP':
                self.state = "browsing"
                self._show_browser()
            elif key == 'DOWN':
                return "back"

        return None

    def _copy_file(self, src_path):
        try:
            self.dest_dir.mkdir(exist_ok=True)
            dest = self.dest_dir / src_path.name
            shutil.copy2(src_path, dest)
            print(f"Copied {src_path.name} to {self.dest_dir}")
            self.state = "notice"
            self._show_notice("Loaded! Restart", "reqd. [OK]")
        except Exception as e:
            print(f"Copy Failed: {e}")
            self.state = "notice"
            self._show_notice("Copy Failed!", "[OK]")

key_queue = queue.Queue()

def _read_key():
    """Grabs the key input from the keyboard when called and creates command"""

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        if ch == '\x1b':  # Escape character
            ch += sys.stdin.read(2)
            if ch == '\x1b[C':  return 'RIGHT'
            elif ch == '\x1b[D':  return 'LEFT'
            elif ch == '\x1b[A':  return 'UP'
            elif ch == '\x1b[B':  return 'DOWN'
        elif ch == '\r':  return 'SELECT'
        elif ch == 'q' or ch == '\x03': return 'QUIT'

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return None

def key_listener():
    while True:
        key = _read_key()
        if key:
            key_queue.put(key)

def ir_listener():
    if not EVDEV_AVAILABLE:
        return

    last_press = 0
    debounce_delay = 0.25

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    device = None
    for dev in devices:
        if 'ir' in dev.name.lower() or 'gpio' in dev.name.lower():
            device = dev
            print(f"IR device found: {dev.name} at {dev.path}")
            break

    if not device:
        print("No IR input device found. Check dtoverlay=gpio-ir is in /boot/config.txt")
        return_event

    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_MSC and event.code == evdev.ecodes.MSC_SCAN:
            current_time = time.time()

            if (current_time - last_press) > debounce_delay:
                scancode = event.value
                action = IR_CODES.get(scancode)
                if action:
                    print(f"IR: {hex(scancode)} -> {action}")
                    key_queue.put(action)
                    last_press = current_time

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

    run_splash_seq(lcd)

    base_menu = BaseMenu(lcd)
    song_menu = SongMenu(songs, lcd)
    load_menu = LoadMenu(lcd)

    current_screen = "base"
    base_menu.display()

    threading.Thread(target=key_listener, daemon=True).start()
    threading.Thread(target=ir_listener, daemon=True).start()

    print("Song Menu Active\n")
    print("Use LEFT/RIGHT arrows to navigate, ENTER/UP to select, DOWN to go back, 'q' to quit\n")

    try:
        while True:

            try:
                key = key_queue.get_nowait()
            except queue.Empty:
                key = None

            time.sleep(0.05)

            if song_menu.is_busy():
                if key == 'DOWN':
                    song_menu.stop_song()
                    current_screen = "song"
                continue

            if current_screen == "load":
                load_menu.poll()

            if current_screen == "base":
                if key == 'RIGHT':
                    base_menu.next_option()
                elif key == 'LEFT':
                    base_menu.prev_option()
                elif key == 'SELECT' or key == 'UP':
                    if base_menu.selected() == "Song Library":
                        current_screen = "song"
                        song_menu.display_current()
                    elif base_menu.selected() == "Load Songs":
                        current_screen = "load"
                        load_menu.enter()
                elif key == 'QUIT':
                    break

            elif current_screen == "song":
                if key == 'RIGHT':
                    song_menu.next_song()
                elif key == 'LEFT':
                    song_menu.prev_song()
                elif key == 'SELECT' or key == 'UP':
                    song_menu.select_song()
                elif key == 'DOWN':
                    current_screen = "base"
                    base_menu.display()
                elif key == 'QUIT':
                    break

            elif current_screen == "load":
                result = load_menu.handle_key(key)
                if result == 'back':
                    current_screen = "base"
                    base_menu.display()
                elif key == 'QUIT':
                    break

    except KeyboardInterrupt:
        pass
    finally:
        menu.cleanup()
        lcd.clear()
        lcd.write_string(lcd_line("Goodbye!"))
        time.sleep(2)
        lcd.clear()
        lcd.close()
        print("\nMenu Now Inactive")

if __name__ == "__main__":
    main()