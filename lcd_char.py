from RPLCD.i2c import CharLCD
import time

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2)

for i in range(0,256,16):
	lcd.clear()
	lcd.cursor_pos = (0,0)
	lcd.write_string(f"{i}-{i+15}:")
	lcd.cursor_pos = (1,0)
	for j in range (i, i+16):
		try:
			lcd.write_string(chr(j))
		except:
			lcd.write_string('?')
	time.sleep(3)
	
lcd.close()
