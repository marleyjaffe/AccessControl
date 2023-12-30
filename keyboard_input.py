import asyncio, evdev
kbd_logi = evdev.InputDevice('/dev/input/by-id/usb-Logitech_USB_Receiver-if02-event-kbd')
kbd_wired = evdev.InputDevice('/dev/input/by-id/usb-SIGMACH1P_USB_Keykoard-event-kbd')


kbd_logi.grab()
kbd_wired.grab()

keypad_string = ''

all_scancodes = {
	# Scancode: ASCIICode
	0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
	10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
	20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
	30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
	40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
	50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}

scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 105: u'OPEN', 106: u'CLOSE'
}

async def print_events(device):
	async for event in device.async_read_loop():
		if event.type == evdev.ecodes.EV_KEY:
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				print(device.path, data, sep=': ')
				print(data.scancode)

async def create_string(device):
	global keypad_string
	async for event in device.async_read_loop():
		global keypad_string
		if event.type == evdev.ecodes.EV_KEY:
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				keypressed = scancodes.get(data.scancode)
				if keypressed == 'ENTR':
					print(keypad_string)
					keypad_string = ''
				elif keypressed == 'OPEN':
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'CLOSE':
					print(keypressed)
					keypad_string = ''
				else:
					# print(keypressed)
					keypad_string += keypressed


for device in kbd_logi, kbd_wired:
	# asyncio.ensure_future(print_events(device))
	# keypad_string = ''
	asyncio.ensure_future(create_string(device))

loop = asyncio.get_event_loop()
loop.run_forever()