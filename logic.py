'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
	-> change to async MQTT to stop blocking when 
'''

# python 3.10

from db_utils import *
# from StreetAutomation import *

import json
import logging
import random
import time
import gpiozero


#MQTT Imports
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Cover, CoverInfo, Button, ButtonInfo, Text, TextInfo, BinarySensor, BinarySensorInfo, DeviceTriggerInfo, DeviceTrigger
from paho.mqtt.client import Client, MQTTMessage

#Keyboard Imports
import asyncio, evdev
from evdev import InputDevice, categorize, ecodes

#set pin num variables
O_PIN = 6
C_PIN = 13
S_PIN = 19
L_PIN = 26

gpioOpen = gpiozero.OutputDevice(O_PIN, active_high=True, initial_value=False)
gpioClose = gpiozero.OutputDevice(C_PIN, active_high=True, initial_value=False)
gpioStop = gpiozero.OutputDevice(S_PIN, active_high=True, initial_value=False)
gpioLock = gpiozero.OutputDevice(L_PIN, active_high=True, initial_value=False)

#Keyboard device mapping
kbd_outside = evdev.InputDevice('/dev/input/by-path/keypad1')
kbd_inside =  evdev.InputDevice('/dev/input/by-path/keypad2')

#prevent other applications from receiveing keypad input
kbd_outside.grab()
kbd_inside.grab()

#set initial keypad string
keypad_string = ''

keypad_string_timeout = 10
keypad_last_pressed_time = time.time()

#ASCII Mapping for Inside Keypad
inside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 14: u'*', 30: u'OPEN', 48: u'STOP', 46: u'CLOSE', 32: u'MAILBOX'
}

#ASCII Mapping for Outside Keypad
outside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 14: u'*', 30: u'A', 48: u'B', 46: u'C', 32: u'D'
}

async def keypad(device, location):
	global keypad_string
	global keypad_string_timeout
	global keypad_last_pressed_time
	async for event in device.async_read_loop():
		
		if event.type == evdev.ecodes.EV_KEY:
			# if location	== 'inside':
			data = evdev.categorize(event)
			if data.keystate == 0: # up events only
				if location == 'inside':
					keypressed = inside_scancodes.get(data.scancode)
				elif location == 'outside':
					keypressed = outside_scancodes.get(data.scancode)
				
				if keypressed == 'ENTR':
					logic(keypad_string)
					keypad_string = ''
				elif keypressed == 'OPEN':
					gate.open()
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'CLOSE':
					gate.close()
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'STOP':
					gate.stop(2)
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'MAILBOX':
					print(keypressed)
					exPkgLck.open(10)
					keypad_string = ''
				elif keypressed == 'A':
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'B':
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'C':
					print(keypressed)
					keypad_string = ''
				elif keypressed == 'D':
					print(keypressed)
					keypad_string = ''
				elif keypressed == '*':
					print(keypressed)
					keypad_string = keypad_string[:-1]
				else:
					print('key pressed: ', keypressed)
					try:
						print('len:', len(keypad_string))
						print('time:', keypad_last_pressed_time)
						if len(keypad_string) <= 9:
							print('timemath: ', time.time() - keypad_last_pressed_time)
							if time.time() - keypad_last_pressed_time <= keypad_string_timeout:
								keypad_last_pressed_time = time.time()
								print('in loop', keypad_last_pressed_time)
								keypad_string += keypressed
							else:
								print('in timeout section')
								keypad_last_pressed_time = time.time()
								keypad_string = keypressed
						else:
							keypad_last_pressed_time = time.time()
							keypad_string = keypressed
					except TypeError:
						continue
					except:
						print("keypad data error")


# async def outside_keypad(device):
# 	global outside_keypad_string
# 	async for event in device.async_read_loop():
# 		global outside_keypad_string
# 		if event.type == evdev.ecodes.EV_KEY:
# 			data = evdev.categorize(event)
# 			if data.keystate == 0: # up events only
# 				keypressed = outside_scancodes.get(data.scancode)
# 				if keypressed == 'ENTR':
# 					logic(outside_keypad_string)
# 					outside_keypad_string = ''
# 				elif keypressed == 'A':
# 					print(keypressed)
# 					outside_keypad_string = ''
# 				elif keypressed == 'B':
# 					print(keypressed)
# 					outside_keypad_string = ''
# 				else:
# 					# print(keypressed)
# 					try:
# 						outside_keypad_string += keypressed
# 					except TypeError:
# 						print("scancode not added")
# 					except:
# 						print("other error")


def logic(keypad_input):
	accessLevel = search_code(con, keypad_input)
	catt_accesscode.set_attributes({"AccessLevel": accessLevel, "AccessCode": keypad_input})
	if accessLevel == "gate":
		print("gate open")
		gate.open()
	elif accessLevel == "owner":
		print("owner")
		gate.personOpen()
	elif accessLevel == "lock":
		print("lock open")
		exPkgLck.open(10)
	elif accessLevel == "close":
		print("closing Gate")
		gate.close()
		catt_gate.closed()
	elif accessLevel == "stop":
		print("stopping gate")
		gate.stop(2)
		catt_gate.stopped()
	elif accessLevel == "party":
		gate.party()
	else:
		#TODO: flash lights like an angry old man
		print("no hits found for either access level or code")
		pass

#TODO build ring function
def outside_ring(keypad_input):
	ringer

class lock:
	default_time = 15
#	gpioLock = gpiozero.OutputDevice(26, active_high=True, initial_value=False)
	
	def __init__(self, name, gpioNumber):
		self.name = name
		self.pin = gpioNumber
	#	gpioLock = gpiozero.OutputDevice(self.pin, active_high=True, initial_value=False)
		pass

	def open(self, unlocktime=default_time):
		print("Opening " + self.name + " for: " + str(unlocktime) + "sec")
		gpioLock.on()
		time.sleep(unlocktime)
		print("Locking " + self.name + " trigger")
		gpioLock.off()

class gate:
	personTime = 10
	toggle_length = .3
#	gpioOpen = gpiozero.OutputDevice(6, active_high=True, initial_value=False)
#	gpioClose = gpiozero.OutputDevice(13, active_high=True, initial_value=False)
#	gpioStop = gpiozero.OutputDevice(19, active_high=True, initial_value=False)
	

	def __init__(self, name, pins):
		self.name = name
		self.pinArray = pins
	#	gpioOpen = gpiozero.OutputDevice(self.pinArray["open"], active_high=True, initial_value=False)
	#	gpioClose = gpiozero.OutputDevice(self.pinArray["close"], active_high=True, initial_value=False)
	#	gpioStop = gpiozero.OutputDevice(self.pinArray["stop"], active_high=True, initial_value=False)


	def open(self):
		# open_gate_trigger.trigger()
		print("OPEN FUNCTION STARTING " + self.name)
		# let HA know that the cover is opening
		catt_gate.opening()
		gpioOpen.on()
		time.sleep(self.toggle_length)
		print("Releasing " + self.name + " trigger")
		gpioOpen.off()
		# Let HA know that the cover was opened
		catt_gate.open()
		pass

	def close(self):
		print("CLOSE FUNCTION STARTING " + self.name)
		# let HA know that the cover is closing
		catt_gate.closing()
		gpioClose.on()
		time.sleep(self.toggle_length)
		print("Releasing " + self.name + " trigger")
		gpioClose.off()
		# Let HA know that the cover was closed
		catt_gate.closed()
		pass

	def stop(self, stoptime=toggle_length):
		# Let HA know that the cover was stopped
		catt_gate.stopped()
		print("STOP FUNCTION STARTING " + self.name + " for: " + str(stoptime) + "sec")
		gpioStop.on()
		time.sleep(stoptime)
		print("Releasing " + self.name + " trigger")
		gpioStop.off()
		pass

	def personOpen(self, openLength=4):
		print("PERSONOPEN FUNCTION STARTING " + self.name + " for: " + str(self.personTime) + "sec")
		self.open()
		time.sleep(openLength)
		self.stop(self.personTime)
		print("Closing " + self.name)
		self.close()
		pass

	def party(self, openLength=4):
		self.open()
		time.sleep(openLength)
		self.stop()

def gpioCleanup():
	print("clean up not necessary with new library")


#######MQTT#######

# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="10.10.10.3")

# Define the device. At least one of `identifiers` or `connections` must be supplied
device_info = DeviceInfo(name="Catt-AccessControl", identifiers="catt-gatepi")

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Information about the cover
gate_info = CoverInfo(name="catt-gatepi-gate", unique_id="catt-gatepi-gate", device=device_info)
gate_settings = Settings(mqtt=mqtt_settings, entity=gate_info)

# To receive state commands from HA, define a callback function:
def gate_callback(client: Client, user_data, message: MQTTMessage):
	payload = message.payload.decode()
	if payload == "OPEN":
		# call function to open cover
		gate.open()
	if payload == "CLOSE":
		# call function to close the cover
		gate.close()
	if payload == "STOP":
		# call function to stop the cover
		gate.stop()

# Instantiate the cover
catt_gate = Cover(gate_settings, gate_callback, user_data)

# Set the initial state of the cover, which also makes it discoverable
catt_gate.closed()


## Package Drop Door
# Information about the button
package_info = ButtonInfo(name="catt-gatepi-package", unique_id="catt-gatepi-packageLock", device=device_info)
package_settings = Settings(mqtt=mqtt_settings, entity=package_info)

# To receive button commands from HA, define a callback function:
def package_callback(client: Client, user_data, message: MQTTMessage):
	exPkgLck.open(10)

# Instantiate the button
catt_package = Button(package_settings, package_callback, user_data)

# Publish the button's discoverability message to let HA automatically notice it
catt_package.write_config()


## Person Gate
# Information about the button
gate_person_info = ButtonInfo(name="catt-gatepi-person", unique_id="catt-gatepi-person", device=device_info)
gate_person_settings = Settings(mqtt=mqtt_settings, entity=gate_person_info)

# To receive button commands from HA, define a callback function:
def person_callback(client: Client, user_data, message: MQTTMessage):
	# Update MQTT status as opening
	catt_gate.opening()
	# Call gate person open function
	gate.personOpen()
	# Update MQTT status as Stopped
	catt_gate.stopped()

# Instantiate the button
catt_person = Button(gate_person_settings, person_callback, user_data)

# Publish the button's discoverability message to let HA automatically notice it
catt_person.write_config()

## AccessCode Used
# Information about the access code text
AccessCodeUsed = BinarySensorInfo(name="access-code-entered", unique_id="catt-gatepi-accesscode-sensor", device=device_info)
AccessCodeUsed_settings = Settings(mqtt=mqtt_settings, entity=AccessCodeUsed)

# # To receive button commands from HA, define a callback function:
# def accesscode_callback(client: Client, user_data, message: MQTTMessage):
# 	text = message.payload.decode()
# 	logging.info(f"Received {text} from HA")
# 	# do_some_custom_thing(text)
# 	# Send an MQTT message to confirm to HA that the text was changed
# 	catt_accesscode.set_text(text)
	

# Instantiate the text
catt_accesscode = BinarySensor(AccessCodeUsed_settings)

# Publish the button's discoverability message to let HA automatically notice it
catt_accesscode.set_attributes({"AccessLevel": "bootup", "AccessCode": "bootup"})

# open_gate_trigger_into = DeviceTriggerInfo(name="Open Gate", type="gate", subtype="open", unique_id="open_gate_trigger", device=device_info)
# open_gate_trigger_settings = Settings(mqtt=mqtt_settings, entity=open_gate_trigger_into)
# open_gate_trigger = DeviceTrigger(open_gate_trigger_settings)

if __name__ == '__main__' :
	'''
	This functin only runs if this specific python file is the one that is run
	
	Description:	sets up package electric strike lock and gate objects
					sets up database connection 
					loops input and checks result with db
					db returns input access level
					check access level and trigger associated logic

	TODO: 	add Ringer logic (ABCD)
			Confirm 4X4 keypad configuration and order from https://www.oitkeypad.com/Site/PDF/MVP-15-hr.pdf
			

	'''

	try:
		'''
		Setup Lock object for package drop
		'''
		exPkgLck = lock("package", L_PIN)

		'''
		Setup gate object
		'''
		gate = gate("gate1", {"open": O_PIN, "close": C_PIN, "stop": S_PIN})

		'''
		Setup database connection
		'''
		con = db_connect()
		cur = con.cursor()
		
		'''
		Loop waiting for keypad input. Perform action based on returned access level
		'''
		asyncio.ensure_future(keypad(kbd_inside, 'inside'))
		asyncio.ensure_future(keypad(kbd_outside, 'outside'))

		loop = asyncio.get_event_loop()
		loop.run_forever()
	except KeyboardInterrupt:
		print("exiting nicely via keyboard interrupt")
	except:
		print("other exit")	
	finally:
		gpioCleanup()
