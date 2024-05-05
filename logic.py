'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
	-> change to async MQTT to stop blocking when 
'''

# python 3.10

from db_utils import *

import json
import logging
import random
import time
import gpiozero
import asyncio
import threading
from datetime import datetime
from zoneinfo import ZoneInfo



#MQTT Imports
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Cover, CoverInfo, Button, ButtonInfo, Text, TextInfo, BinarySensor, BinarySensorInfo, DeviceTriggerInfo, DeviceTrigger
from paho.mqtt.client import Client, MQTTMessage

#Keyboard Imports
import asyncio, evdev
from evdev import InputDevice, categorize, ecodes

tz = ZoneInfo('America/Los_Angeles')

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
					print("Datetime", str(datetime.now().astimezone(tz)), " ", location, " keypad: ", keypressed)
				elif location == 'outside':
					keypressed = outside_scancodes.get(data.scancode)
					print("Datetime", str(datetime.now().astimezone(tz)), " ", location, " keypad: ", keypressed)
				else:
					print("Datetime", str(datetime.now().astimezone(tz))," ERROR - Keypad Location variable not found")

				if keypressed == 'ENTR':
					logic(keypad_string)
					keypad_string = ''
				elif keypressed == 'OPEN':
					gate.open()
					keypad_string = ''
				elif keypressed == 'CLOSE':
					gate.close()
					keypad_string = ''
				elif keypressed == 'STOP':
					gate.stop(2)
					keypad_string = ''
				elif keypressed == 'MAILBOX':
					gate.releaseStop()
					keypad_string = ''
				elif keypressed == 'A':
					keypad_string = ''
				elif keypressed == 'B':
					keypad_string = ''
				elif keypressed == 'C':
					keypad_string = ''
				elif keypressed == 'D':
					keypad_string = ''
				elif keypressed == '*':
					keypad_string = keypad_string[:-1]
				else:
					try:
						# print('len:', len(keypad_string))
						# print('time:', keypad_last_pressed_time)
						if len(keypad_string) <= 9:
							# print('timemath: ', time.time() - keypad_last_pressed_time)
							if time.time() - keypad_last_pressed_time <= keypad_string_timeout:
								keypad_last_pressed_time = time.time()
								# print('in loop', keypad_last_pressed_time)
								keypad_string += keypressed
							else:
								print("Datetime", str(datetime.now().astimezone(tz))," ERROR - keypad timeout occured")
								keypad_last_pressed_time = time.time()
								keypad_string = keypressed
						else:
							print("Datetime", str(datetime.now().astimezone(tz))," ERROR - keycode length exceeded")
							keypad_last_pressed_time = time.time()
							keypad_string = keypressed
					except TypeError as err:
						# I believe these happen for every keypress
						# print(f"Datetime {str(datetime.now().astimezone(tz))} Unexpected Type Error {err=}, {type(err)=}")
						continue
					except Exception as err:
						print(f"Datetime {str(datetime.now().astimezone(tz))} Unexpected {err=}, {type(err)=}")


def logic(keypad_input):
	try:
		accessLevel, codeName = search_code(con, keypad_input)
	except:
		accessLevel = "error"
		codeName = "BadCode"
	mqtt_accesscode.set_attributes({"AccessLevel": accessLevel, "AccessCode": keypad_input, "Name": codeName, "Datetime": str(datetime.now().astimezone(tz))})
	print("Datetime", str(datetime.now().astimezone(tz)), " Name:", codeName, " AccessCode: ", keypad_input, " AccessLevel: ", accessLevel)
	if accessLevel == "gate":
		print("Datetime", str(datetime.now().astimezone(tz)), " OPEN function triggered")
		gate.open()
	elif accessLevel == "delivery":
		print("Datetime", str(datetime.now().astimezone(tz)), " DELIVERY function triggered")
		gate.personOpen()
	elif accessLevel == "lock":
		print("Datetime", str(datetime.now().astimezone(tz)), " LOCK function triggered")
		exPkgLck.open(10)
	elif accessLevel == "close":
		print("Datetime", str(datetime.now().astimezone(tz)), " CLOSE function triggered")
		gate.close()
	elif accessLevel == "stop":
		print("Datetime", str(datetime.now().astimezone(tz)), " STOP function triggered")
		gate.stop(2)
	elif accessLevel == "party":
		print("Datetime", str(datetime.now().astimezone(tz)), " PARTY function triggered")
		gate.party()
	else:
		#TODO: flash lights like an angry old man
		print("Datetime", str(datetime.now().astimezone(tz)), " ERROR - Access Level Missing not defined")
		pass

#TODO build ring function
def outside_ring(keypad_input):
	ringer

def gpioCleanup():
	print("Datetime", str(datetime.now().astimezone(tz)), " GPIO clean up not necessary with new library, EndOfFunction")

class lock:
	default_time = 15
	
	def __init__(self, name, gpioNumber):
		self.name = name
		self.pin = gpioNumber
		pass

	def open(self, unlocktime=default_time):
		# print("Opening " + self.name + " for: " + str(unlocktime) + "sec")
		gpioLock.on()
		time.sleep(unlocktime)
		# print("Locking " + self.name + " trigger")
		gpioLock.off()

class gate:
	personTime = 10
	toggle_length = .3
	stop_hold_timeout = 60 * 5
	

	def __init__(self, name, pins):
		self.name = name
		self.pinArray = pins
		self.isStopped = False

	def open(self):
		self.releaseStop()
		# print("OPEN FUNCTION STARTING " + self.name)
		gpioOpen.on()
		time.sleep(self.toggle_length)
		# print("Releasing " + self.name + " trigger")
		gpioOpen.off()

	def close(self):
		self.releaseStop()
		# print("CLOSE FUNCTION STARTING " + self.name)
		gpioClose.on()
		time.sleep(self.toggle_length)
		# print("Releasing " + self.name + " trigger")
		gpioClose.off()

	def stop(self, stoptime=toggle_length):
		# print("STOP FUNCTION STARTING " + self.name + " for: " + str(stoptime) + "sec")
		
		self.isStopped = True

		thread = threading.Thread(target=self.runAsyncMonitorIsStopped)
		thread.start()

	def personOpen(self, openLength=4):
		# print("PERSONOPEN FUNCTION STARTING " + self.name + " for: " + str(self.personTime) + "sec")
		self.open()
		time.sleep(openLength)
		self.stop(self.personTime)
		# print("Closing " + self.name)
		self.close()

	def party(self, openLength=4):
		self.open()
		time.sleep(openLength)
		self.stop()

	# `stop` helper functions
	def runAsyncMonitorIsStopped(self):
		asyncio.run(self.monitorIsStopped())

	async def monitorIsStopped(self):
		gpioStop.on()
		try:
			await asyncio.wait_for(self.waitIsStoppedFalse(), timeout=self.stop_hold_timeout)
		except asyncio.TimeoutError:
			self.releaseStop()
		finally:
			self.releaseStop()

	async def waitIsStoppedFalse(self):
		while self.isStopped:
			await asyncio.sleep(0.5)
	
	def releaseStop(self):
		self.isStopped = False
		gpioStop.off()

#######MQTT#######

# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="192.168.1.7")

# Define the device. At least one of `identifiers` or `connections` must be supplied
device_info = DeviceInfo(name="Liq-AccessControl", identifiers="liq-gatepi")

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Information about the cover
gate_info = CoverInfo(name="liq-gatepi-gate", unique_id="liq-gatepi-gate", device=device_info)
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

def gate_open_callback(client: Client, user_data, message: MQTTMessage):
	gate.open()

gate_open_info = ButtonInfo(name="liq-gatepi-gate-open", unique_id="liq-gatepi-gate-open", device=device_info)
gate_open_settings = Settings(mqtt=mqtt_settings, entity=gate_open_info)
gate_open_button = Button(gate_open_settings, gate_open_callback, user_data)
gate_open_button.write_config()

def gate_close_callback(client: Client, user_data, message: MQTTMessage):
	gate.close()

gate_close_info = ButtonInfo(name="liq-gatepi-gate-close", unique_id="liq-gatepi-gate-close", device=device_info)
gate_close_settings = Settings(mqtt=mqtt_settings, entity=gate_close_info)
gate_close_button = Button(gate_close_settings, gate_close_callback, user_data)
gate_close_button.write_config()

def gate_stop_callback(client: Client, user_data, message: MQTTMessage):
	gate.stop()

gate_stop_info = ButtonInfo(name="liq-gatepi-gate-stop", unique_id="liq-gatepi-gate-stop", device=device_info)
gate_stop_settings = Settings(mqtt=mqtt_settings, entity=gate_stop_info)
gate_stop_button = Button(gate_stop_settings, gate_stop_callback, user_data)
gate_stop_button.write_config()

def gate_release_stop_callback(client: Client, user_data, message: MQTTMessage):
	gate.releaseStop()

gate_release_stop_info = ButtonInfo(name="liq-gatepi-gate-release_stop", unique_id="liq-gatepi-gate-release_stop", device=device_info)
gate_release_stop_settings = Settings(mqtt=mqtt_settings, entity=gate_release_stop_info)
gate_release_stop_button = Button(gate_release_stop_settings, gate_release_stop_callback, user_data)
gate_release_stop_button.write_config()

## Package Drop Door
# Information about the button
package_info = ButtonInfo(name="liq-gatepi-package", unique_id="liq-gatepi-packageLock", device=device_info)
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
gate_person_info = ButtonInfo(name="liq-gatepi-person", unique_id="liq-gatepi-person", device=device_info)
gate_person_settings = Settings(mqtt=mqtt_settings, entity=gate_person_info)

# To receive button commands from HA, define a callback function:
def person_callback(client: Client, user_data, message: MQTTMessage):
	# Call gate person open function
	gate.personOpen()

# Instantiate the button
catt_person = Button(gate_person_settings, person_callback, user_data)

# Publish the button's discoverability message to let HA automatically notice it
catt_person.write_config()

## AccessCode Used
# Information about the access code text
AccessCodeUsed = BinarySensorInfo(name="access-code-entered", unique_id="liq-gatepi-accesscode-sensor", device=device_info)
AccessCodeUsed_settings = Settings(mqtt=mqtt_settings, entity=AccessCodeUsed)

# # To receive button commands from HA, define a callback function:
# def accesscode_callback(client: Client, user_data, message: MQTTMessage):
# 	text = message.payload.decode()
# 	logging.info(f"Received {text} from HA")
# 	# do_some_custom_thing(text)
# 	# Send an MQTT message to confirm to HA that the text was changed
# 	mqtt_accesscode.set_text(text)
	

# Instantiate the text
mqtt_accesscode = BinarySensor(AccessCodeUsed_settings)

# Publish the button's discoverability message to let HA automatically notice it
# mqtt_accesscode.set_text(bootup)
mqtt_accesscode.set_attributes({"AccessLevel": "bootup", "AccessCode": "bootup",  "Name": "bootup", "Datetime": str(datetime.now().astimezone(tz))})


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
		print("Datetime", str(datetime.now().astimezone(tz)), " Keyboard interrupt detected. Exiting nicely")
	except Exception as error:
		print("Datetime", str(datetime.now().astimezone(tz)), " other exit: ", error)	
	finally:
		gpioCleanup()
