import asyncio, evdev
from evdev import InputDevice, categorize, ecodes
kbd_outside = evdev.InputDevice('/dev/input/by-id/usb-Logitech_USB_Receiver-if02-event-kbd')
kbd_inside = evdev.InputDevice('/dev/input/by-id/usb-SIGMACH1P_USB_Keykoard-event-kbd')

kbd_outside.grab()
kbd_inside.grab()

inside_keypad_string = ''
outside_keypad_string = ''
all_scancodes = {
	# Scancode: ASCIICode
	0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
	10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
	20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
	30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
	40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
	50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}

inside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 105: u'OPEN', 106: u'CLOSE'
}

outside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 105: u'call1', 106: u'call2'
}

async def print_events(device):
	async for event in device.async_read_loop():
		if event.type == evdev.ecodes.EV_KEY:
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				print(device.path, data, sep=': ')
				print(data.scancode)

async def inside_keypad(device):
	global inside_keypad_string
	async for event in device.async_read_loop():
		global inside_keypad_string
		if event.type == evdev.ecodes.EV_KEY:
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				keypressed = inside_scancodes.get(data.scancode)
				if keypressed == 'ENTR':
					print(inside_keypad_string)
					inside_keypad_string = ''
				elif keypressed == 'OPEN':
					print(keypressed)
					inside_keypad_string = ''
				elif keypressed == 'CLOSE':
					print(keypressed)
					inside_keypad_string = ''
				else:
					# print(keypressed)
					try:
						inside_keypad_string += keypressed
					except TypeError:
						print("scancode not added")
					except:
						print("other error")

async def outside_keypad(device):
	global outside_keypad_string
	async for event in device.async_read_loop():
		global outside_keypad_string
		if event.type == evdev.ecodes.EV_KEY:
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				keypressed = outside_scancodes.get(data.scancode)
				if keypressed == 'ENTR':
					print(outside_keypad_string)
					outside_keypad_string = ''
				elif keypressed == 'call1':
					print(keypressed)
					outside_keypad_string = ''
				elif keypressed == 'call2':
					print(keypressed)
					outside_keypad_string = ''
				else:
					# print(keypressed)
					try:
						outside_keypad_string += keypressed
					except TypeError:
						print("scancode not added")
					except:
						print("other error")

asyncio.ensure_future(inside_keypad(kbd_inside))
asyncio.ensure_future(outside_keypad(kbd_outside))

loop = asyncio.get_event_loop()
try:
	loop.run_forever()
except KeyboardInterrupt:
	print("exiting nicely via keyboard interrupt")
except:
	print("other exit")