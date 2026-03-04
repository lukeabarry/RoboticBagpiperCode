try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - running in simulation mode")
    GPIO_AVAILABLE = False

import time

# Pin to test
TEST_PIN = 18

# Setup
if GPIO_AVAILABLE:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TEST_PIN, GPIO.OUT)

# Test loop
try:
    while True:
        print(f"Pin {TEST_PIN} ON")
        if GPIO_AVAILABLE:
            GPIO.output(TEST_PIN, GPIO.HIGH)
        time.sleep(1)
        
        print(f"Pin {TEST_PIN} OFF")
        if GPIO_AVAILABLE:
            GPIO.output(TEST_PIN, GPIO.LOW)
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nStopped")
finally:
    if GPIO_AVAILABLE:
        GPIO.cleanup()
    print("Done")