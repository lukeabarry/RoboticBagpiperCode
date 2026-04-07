import time
try:
	import RPi.GPIO as GPIO
	GPIO_AVAILABLE = True
except ImportError:
	print("NO GPIO")
	GPIO_AVAILABLE = False

note_to_gpio = {
            67: [26, 19, 20, 21, 16, 6, 5, 7],   # low G
            69: [26, 19, 20, 21, 16, 6, 5],      # A
            71: [26, 19, 20, 21, 16, 6],          # B
            72: [26, 19, 20, 21, 16, 7],         # C
            73: [26, 19, 20, 21, 16],            # C sharp
            74: [26, 19, 20, 21, 7],            # D
            76: [26, 19, 20, 16, 6, 5],         # E
            78: [26, 19, 20, 6, 5],            # F sharp
            79: [26, 20, 6, 5, 7],         # high G
            81: [20, 16, 6, 5]       # high A
}

if GPIO_AVAILABLE:
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	all_pins = set(pin for pins in note_to_gpio.values() for pin in pins)
	for pin in all_pins:
		GPIO.setup(pin, GPIO.OUT)
		GPIO.output(pin, GPIO.LOW)

for note, pins in note_to_gpio.items():
	print(f"Note {note} ON - pins {pins}")
	if GPIO_AVAILABLE:
		GPIO.output(pins, GPIO.HIGH)
	time.sleep(2)
	print(f"Note {note} OFF")
	if GPIO_AVAILABLE:
		GPIO.output(pins, GPIO.LOW)
	time.sleep(1)

if GPIO_AVAILABLE:
	GPIO.cleanup()
print("Done")