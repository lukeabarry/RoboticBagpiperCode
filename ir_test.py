import evdev                          
for path in evdev.list_devices():
	dev = evdev.InputDevice(path)
	print(f"name='{dev.name}' path = {path}")
	if 'ir' in dev.name.lower() or 'gpio' in dev.name.lower():
		print(f" -> ,matched, listening...")
		for event in dev.read_loop():
			print(f"event : type={event.type} code = {event.code} value={event.value}")
