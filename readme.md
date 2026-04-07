Welcome Piper! 

This repo contains all the code you need for the Raspberry Pi to make Spot the Robotic Bagpiper work. Two major files are responsible for this: MIDI_interpretation_module_with_LCD.py, and LCD_Master.py. Here's a bit about both.

LCD_Master.py
This file contains all the major visual interfacing bits, viewed on the 16x2 LCD Screen, and
controlled by the IR Remote and it's receiver. When run, it'll start by playing a short
welcome message, followed by a bootup animation of a bagpipe. This leads to the main menu
which has 2 features; the song library, and the loading dock. The former allows you
select songs among the preloaded catalogue found in the MIDIFiles/ directory. All songs
when played will give a 5 second buffer (this time variable is actually set in the midi
interpreter) for the pumps to start (as of now there's no automation to the pumps due to
pressure issues) and then the song progress will be displayed on the screen while the
actuators fire in line with the music. From a desktop setup it may be easier to load new 
songs by simply dragging compatible MIDI files to this directory. This however is not 
required due to the latter menu, the loading dock. This menu will prompt the user to insert 
a USB, searching the media/ folder for it, and generate an interactable menu directing you 
to scroll either deeper into the folders on the USB, or remain surface level. Only files of 
the .mid extension will be recognized as to avoid causing compatibility problems for files 
loaded without proper extension. Selecting [OK] on a song results in it's loading to the 
Song Library, where it can be found after the pi is rebooted. Currently, this reboot when 
not in desktop mode involes entirely cutting power to the board, so understand this is a 
potentially time consuming step. A good idea for future contributors to the repo is make a 
new menu option which has the elevated priviledges to both power down the board, or restart 
it, avoiding any unnecessary unplugging. 

MIDI_interpretation_with_LCD.py

This file is responsible for converting MIDI files (files which use the extension .mid, and
found in the MIDIFiles/ dir) into music. The module makes use of mido extension in python 
to interpret the hex contained in MIDI files. Using the GPIO pins of the board to create a
mapping for the notes and then associating them to a hex value used by MIDI allows the 
actuators to create the finger layout on the physical intrument each time the note appears
in a song. Also extracted are the timing of these notes, based on a velocity measurement 
in hex. The mido library keeps track of the length of a note using this and will hold 
that note until the next instruction/note. To switch between the notes, the code uses a 
list to keep track of the actuators currently being used, and compares it to a list of 
actuators it'll need for the next state. It will then make 2 more lists, the actuators to
add, and the ones to remove from the next note. This, in essence is the spirit of 
playing a song instead of a series of single notes in order. 

As of right now, the Raspberry Pi associated with this project is instructed (by setup_hardware.sh) to run the LCD_master.py file on bootup, so all that is required to get the instrument playing is to plug in the pi, and of course, power the actuators, robot, and pumps.