# Welcome Piper! 🎵

Piper is an autonomous bagpipe instrument mounted on a Boston Dynamics Spot robot, developed as a capstone project at Queen's University in partnership with Ingenuity Labs. The system parses MIDI files and translates them into real-time actuator commands, physically fingering the chanter of a real bagpipe instrument.

> 📹 **[Watch Piper in action](#)** ← *(replace with your YouTube link)*

---

## System Overview

The Raspberry Pi serves as the central controller, running two major modules:

- **`LCD_Master.py`** — User interface and song management via a 16x2 LCD screen and IR remote
- **`MIDI_interpretation_module_with_LCD.py`** — MIDI parsing and real-time actuator control

On bootup (configured via `setup_hardware.sh`), the Pi automatically launches the LCD interface. From there, all that's needed to get Piper playing is power to the actuators, robot, and pumps.

---

## Modules

### `LCD_Master.py`
Handles all visual interfacing and user input through a 16x2 LCD screen controlled by an IR remote and receiver.

On launch, the interface plays a welcome message and bagpipe bootup animation before entering the main menu, which has two features:

- **Song Library** — Browse and select from preloaded MIDI files in the `MIDIFiles/` directory. When a song is selected, a 5-second buffer is given for the pumps to reach pressure before the actuators begin firing in sync with the music. Song progress is displayed on screen throughout playback.
- **Loading Dock** — Allows new songs to be loaded from a USB drive without needing desktop access. The interface lets you navigate folder structures on the USB and load any `.mid` file directly into the Song Library. Only `.mid` files are recognized to prevent compatibility issues. Loaded songs are available after reboot.

> **Note for contributors:** A useful future addition would be a menu option with elevated privileges to reboot or shut down the Pi cleanly, avoiding the need to cut power manually when running headless.

---

### `MIDI_interpretation_module_with_LCD.py`
Responsible for converting MIDI files into physical music on the instrument.

The module uses the `mido` Python library to parse the hex-encoded note and timing data contained in `.mid` files. Each MIDI note is mapped to a GPIO pin on the Raspberry Pi, which in turn controls a specific actuator corresponding to a finger position on the chanter.

Timing is derived from MIDI velocity and note duration values — the library holds each note until the next instruction arrives, mirroring natural finger movement.

To handle transitions between notes smoothly, the interpreter maintains a list of currently active actuators and compares it against the actuators required for the next note. It then computes:
- Actuators to **add** (fingers to press)
- Actuators to **remove** (fingers to lift)

This approach plays music as a continuous sequence of transitions rather than a series of isolated notes, which is essential for producing coherent sound on a real instrument.

---

## Hardware

- Raspberry Pi (main controller)
- Boston Dynamics Spot Robot (locomotion platform)
- Pneumatic actuators (finger control)
- Bagpipe pumps (air pressure)
- 16x2 LCD screen + IR remote (user interface)
- I2C peripheral interface

---

## Getting Started

1. Clone the repo onto the Raspberry Pi
2. Run `setup_hardware.sh` to configure autoboot
3. Power on the Pi, actuators, robot, and pumps
4. Use the LCD interface to select and play a song

MIDI files can be added via USB using the Loading Dock menu, or by copying `.mid` files directly into the `MIDIFiles/` directory from a desktop.

---

## Built With

- Python (`mido`, `RPi.GPIO`)
- Raspberry Pi GPIO
- I2C (LCD interface)
- MIDI file format
