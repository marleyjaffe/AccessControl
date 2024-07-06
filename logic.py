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
import logging
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

logging.Formatter.converter = time.localtime
logging.basicConfig(format='%(asctime)s %(levelname)s- %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

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
isKeypadActive = False
keypad_string = ''
keypad_string_max_length = 9
keypad_string_timeout = 10
keypad_last_pressed_time = time.time()

#ASCII Mapping for Inside Keypad
inside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 14: u'*', 30: u'OPEN', 48: u'STOP', 46: u'CLOSE', 32: u'RELEASE'
}

#ASCII Mapping for Outside Keypad
outside_scancodes = {
	# Scancode: ASCIICode
	2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 
	28: u'ENTR', 14: u'*', 30: u'A', 48: u'B', 46: u'C', 32: u'D'
}

async def keypad(device, location):
	global keypad_string
	global keypad_string_max_length
	global keypad_string_timeout
	global keypad_last_pressed_time
	global isKeypadActive
	global isLengthOK
	global isTimeoutOK

	try:
		async for event in device.async_read_loop():
		
			if event.type == evdev.ecodes.EV_KEY:
				data = evdev.categorize(event)

				if data.keystate == 0 and data.scancode != 42: # up events only, ignoring duplicate keypress for right column keys
					if location == 'inside':
						keypressed = inside_scancodes.get(data.scancode)
					elif location == 'outside':
						keypressed = outside_scancodes.get(data.scancode)
					else:
						logging.error(f"Keypad Location variable not found")
					
					logging.info(f"Key pressed: {keypressed} at location: {location }")

					if keypressed == 'ENTR':
						logic(keypad_string, location)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'OPEN':
						master_code(keypressed, location)
						gate.open()
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'CLOSE':
						master_code(keypressed, location)
						gate.close()
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'STOP':
						master_code(keypressed, location)
						gate.stop(2)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'RELEASE':
						master_code(keypressed, location)
						gate.releaseStop()
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'A':
						doorbell(keypressed, location)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'B':
						doorbell(keypressed, location)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'C':
						doorbell(keypressed, location)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'D':
						doorbell(keypressed, location)
						keypad_string = ''
						isKeypadActive = False
					# delete last character from string
					elif keypressed == '*':
						keypad_string = keypad_string[:-1]
					else:
						try:
							isLengthOK = len(keypad_string) <= keypad_string_max_length
							isTimeoutOK = time.time() - keypad_last_pressed_time <= keypad_string_timeout

							if isKeypadActive:
								if isLengthOK:		
									if isTimeoutOK:
										keypad_last_pressed_time = time.time()
										keypad_string += keypressed
									else:
										logging.debug(f"`keypad_string` will be reset from timeout")
										keypad_last_pressed_time = time.time()
										keypad_string = keypressed
								else:
									logging.debug(f"`keypad_string` reset from length exceeded")
									keypad_last_pressed_time = time.time()
									keypad_string = keypressed
							else:
								logging.debug(f"Keypad set to active.")
								isKeypadActive = True
								keypad_last_pressed_time = time.time()
								keypad_string = keypressed
						except TypeError as error:
							logging.debug(f"TypeError: {error}")
							continue
						except Exception as error:
							logging.error(f"Unexpected error: {error}")
	except OSError as error:
		if error.errno == 19:
			dict = {
			"Error": f"{location.capitalize()} Keypad Disconnected",
			"Datetime": str(datetime.now().astimezone(tz))
			}
			mqtt_trigger.trigger(json.dumps(dict))
			logging.critical(f"No such device. Location: {location}. Is the keypad connected?")
		else:
			logging.critical(f"OSError: {error}")
	except Exception as error:
		logging.critical(f"Exception: {error}")

def master_code(keypad_input, location):
	dict = {
			"Command": f"{location.capitalize()} Override: {keypad_input}",
			"Location": location,
			"Datetime": str(datetime.now().astimezone(tz))
		}
	mqtt_trigger.trigger(json.dumps(dict))

def doorbell(keypad_input, location):
	dict = {
			"Command": f"Doorbell: {keypad_input}",
			"Location": location,
			"Datetime": str(datetime.now().astimezone(tz))
		}
	mqtt_trigger.trigger(json.dumps(dict))

def logic(keypad_input, location):
	try:
		accessLevel, codeName = search_code(con, keypad_input)
	except:
		accessLevel = "error"
		codeName = "BadCode"
		
	dict = {
			"AccessLevel": accessLevel,
			"AccessCode": keypad_input,
			"Command": f"{location.capitalize()} {codeName} ",
			"Location": location,
			"Datetime": str(datetime.now().astimezone(tz))
		}
	mqtt_trigger.trigger(json.dumps(dict))
	
	mqtt_accesscode.on()
	mqtt_accesscode.set_attributes({"AccessLevel": accessLevel, "AccessCode": keypad_input, "Name": codeName, "Datetime": str(datetime.now().astimezone(tz))})

	logging.info(f"Name: {codeName} | AccessCode: {keypad_input} | AccessLevel: {accessLevel} ")
	if accessLevel == "gate":
		logging.info(f"OPEN function triggered")
		gate.open()
	elif accessLevel == "delivery":
		logging.info(f"DELIVERY function triggered")
		gate.open(True)
	elif accessLevel == "lock":
		logging.info(f"LOCK function triggered")
		exPkgLck.open(10)
	elif accessLevel == "close":
		logging.info(f"CLOSE function triggered")
		gate.close()
	elif accessLevel == "stop":
		logging.info(f"STOP function triggered")
		gate.stop(2)
	elif accessLevel == "party":
		logging.info(f"PARTY function triggered")
		gate.party()
	else:
		#TODO: flash lights like an angry old man
		logging.critical(f"AccessLevel undefined!")
		pass

#TODO build ring function
def outside_ring(keypad_input):
	ringer

def gpioCleanup():
	logging.debug(f"GPIO clean up not necessary with new library, EndOfFunction")

class lock:
	default_time = 15
	
	def __init__(self, name, gpioNumber):
		self.name = name
		self.pin = gpioNumber
		pass

	def open(self, unlocktime=default_time):
		gpioLock.on()
		time.sleep(unlocktime)
		gpioLock.off()

class gate:
	personTime = 10
	toggle_length = .3
	stop_hold_timeout = 60 * 5
	hard_open_timeout = 60 * 1
	
	def __init__(self, name, pins):
		self.name = name
		self.pinArray = pins
		self.isStopped = False
		self.isHardOpen = False
		
	def open(self, isHardOpen=False):
		self.releaseHardOpen()
		if isHardOpen:
			logging.info(f"HOLD OPEN")
			self.isHardOpen = True
			thread = threading.Thread(target=self.runAsyncMonitorIsHardOpen)
			thread.start()
		else:
			logging.info(f"SOFT OPEN")
			self.releaseStop()
			gpioOpen.on()
			time.sleep(self.toggle_length)
			gpioOpen.off()

	def close(self):
		self.releaseHardOpen()
		self.releaseStop()
		gpioClose.on()
		time.sleep(self.toggle_length)
		gpioClose.off()

	def stop(self, stoptime=toggle_length):
		self.releaseHardOpen()
		self.isStopped = True

		thread = threading.Thread(target=self.runAsyncMonitorIsStopped)
		thread.start()

	def personOpen(self, openLength=4):
		self.releaseHardOpen()
		self.releaseStop()
		self.open()
		time.sleep(openLength)
		self.stop(self.personTime)
		self.close()

	def party(self, openLength=4):
		self.releaseHardOpen()
		self.releaseStop()

		self.open()
		time.sleep(openLength)
		self.stop()

	# HARD OPEN helper functions
	def runAsyncMonitorIsHardOpen(self):
		asyncio.run(self.monitorIsHardOpen())

	async def monitorIsHardOpen(self):
		gpioOpen.on()
		try:
			await asyncio.wait_for(self.waitIsHardOpenFalse(), timeout=self.hard_open_timeout)
		except asyncio.TimeoutError:
			logging.info(f"HOLD OPEN timeout hit")
			self.releaseHardOpen()
			self.close()
		finally:
			self.releaseHardOpen()

	async def waitIsHardOpenFalse(self):
		while self.isHardOpen:
			await asyncio.sleep(0.5)
	
	def releaseHardOpen(self):
		self.isHardOpen = False
		gpioOpen.off()

	# `stop` helper functions
	def runAsyncMonitorIsStopped(self):
		asyncio.run(self.monitorIsStopped())

	async def monitorIsStopped(self):
		gpioStop.on()
		try:
			await asyncio.wait_for(self.waitIsStoppedFalse(), timeout=self.stop_hold_timeout)
		except asyncio.TimeoutError:
			logging.info(f"STOP HOLD timeout hit")
			self.releaseStop()
			self.close()
		finally:
			self.releaseStop()

	async def waitIsStoppedFalse(self):
		while self.isStopped:
			await asyncio.sleep(0.5)
	
	def releaseStop(self):
		self.isStopped = False
		gpioStop.off()

#######MQTT#######

MQTT_HOST = "10.10.10.3"
MQTT_BASE_NAME = "Catt"
MQTT_DEVICE_NAME = f"{MQTT_BASE_NAME}-AccessControl"
MQTT_BASE_IDENTIFIER = "catt"
MQTT_DEVICE_IDENTIFIER = f"{MQTT_BASE_IDENTIFIER}-gatepi"

# # Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host=MQTT_HOST)

# # Define the device. At least one of `identifiers` or `connections` must be supplied
device_info = DeviceInfo(name=MQTT_DEVICE_NAME, identifiers=MQTT_DEVICE_IDENTIFIER)

# # Define an optional object to be passed back to the callback
user_data = "Some custom data"



#### UNCOMMENT IF WE EVER SWITCH BACK TO USING THE HA "COVER" OBJECT ####

# # Information about the cover
# gate_info = CoverInfo(name="liq-gatepi-gate", unique_id="liq-gatepi-gate", device=device_info)
# gate_settings = Settings(mqtt=mqtt_settings, entity=gate_info)

# # To receive state commands from HA, define a callback function:
# def gate_callback(client: Client, user_data, message: MQTTMessage):
# 	payload = message.payload.decode()
# 	if payload == "OPEN":
# 		# call function to open cover
# 		gate.open()
# 	if payload == "CLOSE":
# 		# call function to close the cover
# 		gate.close()
# 	if payload == "STOP":
# 		# call function to stop the cover
# 		gate.stop()

#### UNCOMMENT IF WE EVER SWITCH BACK TO USING THE HA "COVER" OBJECT ####



def gate_open_callback(client: Client, user_data, message: MQTTMessage):
	dict = {
			"Command": f"HA Override OPEN",
		}
	mqtt_trigger.trigger(json.dumps(dict))
	logging.info(f"OPEN triggered from HomeAssistant")
	gate.open()

gate_open_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-open", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-open", device=device_info)
gate_open_settings = Settings(mqtt=mqtt_settings, entity=gate_open_info)
gate_open_button = Button(gate_open_settings, gate_open_callback, user_data)
gate_open_button.write_config()

def gate_hold_open_callback(client: Client, user_data, message: MQTTMessage):
	dict = {
			"Command": f"HA Override HOLD OPEN",
		}
	mqtt_trigger.trigger(json.dumps(dict))
	logging.info(f"HOLD OPEN triggered from HomeAssistant")
	gate.open(True)

gate_hold_open_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-hold-open", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-hold-open", device=device_info)
gate_hold_open_settings = Settings(mqtt=mqtt_settings, entity=gate_hold_open_info)
gate_hold_open_button = Button(gate_hold_open_settings, gate_hold_open_callback, user_data)
gate_hold_open_button.write_config()

def gate_close_callback(client: Client, user_data, message: MQTTMessage):
	dict = {
			"Command": f"HA Override CLOSE",
		}
	mqtt_trigger.trigger(json.dumps(dict))
	logging.info(f"CLOSE triggered from HomeAssistant")
	gate.close()

gate_close_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-close", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-close", device=device_info)
gate_close_settings = Settings(mqtt=mqtt_settings, entity=gate_close_info)
gate_close_button = Button(gate_close_settings, gate_close_callback, user_data)
gate_close_button.write_config()

def gate_stop_callback(client: Client, user_data, message: MQTTMessage):
	dict = {
			"Command": f"HA Override STOP",
		}
	mqtt_trigger.trigger(json.dumps(dict))
	logging.info(f"STOP triggered from HomeAssistant")
	gate.stop()

gate_stop_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-stop", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-stop", device=device_info)
gate_stop_settings = Settings(mqtt=mqtt_settings, entity=gate_stop_info)
gate_stop_button = Button(gate_stop_settings, gate_stop_callback, user_data)
gate_stop_button.write_config()

def gate_release_stop_callback(client: Client, user_data, message: MQTTMessage):
	dict = {
			"Command": f"HA Override RELEASE STOP",
		}
	mqtt_trigger.trigger(json.dumps(dict))
	logging.info(f"RELEASE-STOP triggered from HomeAssistant")
	gate.releaseStop()

gate_release_stop_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-release_stop", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-gate-release_stop", device=device_info)
gate_release_stop_settings = Settings(mqtt=mqtt_settings, entity=gate_release_stop_info)
gate_release_stop_button = Button(gate_release_stop_settings, gate_release_stop_callback, user_data)
gate_release_stop_button.write_config()

## Package Drop Door
# Information about the button
package_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-package", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-packageLock", device=device_info)
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
gate_person_info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-person", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-person", device=device_info)
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
AccessCodeUsed = BinarySensorInfo(name=f"{MQTT_BASE_IDENTIFIER}-access-code-entered", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-accesscode-sensor", device=device_info)
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



mqtt_trigger_info = DeviceTriggerInfo(name="MyTrigger", type="button_press", subtype="button_1", unique_id="unique id", device=device_info)
mqtt_trigger_settings = Settings(mqtt=mqtt_settings, entity=mqtt_trigger_info)
mqtt_trigger = DeviceTrigger(mqtt_trigger_settings)
mqtt_trigger.trigger("bootup")

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
		logging.warning(f"Keyboard interrupt detected. Exiting nicely")
	except Exception as error:
		logging.critical(f"Exception: {error}")
	finally:
		gpioCleanup()