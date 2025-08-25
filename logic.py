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
from typing import Callable

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
					
					logging.debug(f"Key pressed: {keypressed} at location: {location }")

					if keypressed == 'ENTR':
						logic(keypad_string, location)
						keypad_string = ''
						isKeypadActive = False
					elif keypressed == 'OPEN':
						master_code(keypressed, location)
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
			mqtt_trigger_log(dict)
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
	mqtt_trigger_log(dict)

def doorbell(keypad_input, location):
	dict = {
			"Command": f"Doorbell: {keypad_input}",
			"Location": location,
			"Datetime": str(datetime.now().astimezone(tz))
		}
	mqtt_trigger_log(dict)

def logic(keypad_input, location):
	try:
		logging.debug({"con": con, "keypad_input": keypad_input, "location": location})
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
	mqtt_trigger_log(dict)
	if mqtt_binary_sensor is not None:
		mqtt_binary_sensor.set_attributes({"AccessLevel": accessLevel, "AccessCode": keypad_input, "Name": codeName, "Datetime": str(datetime.now().astimezone(tz))})

	logging.info(f"Name: {codeName} | AccessCode: {keypad_input} | AccessLevel: {accessLevel} | Keypad: {location} ")
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
	elif accessLevel == "disabled":
		logging.critical(f"DISABLED gatecode attempted")
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

MQTT_HOST = "192.168.1.7"
MQTT_BASE_NAME = "Liq"
MQTT_DEVICE_NAME = f"{MQTT_BASE_NAME}-AccessControl"
MQTT_BASE_IDENTIFIER = "liq"
MQTT_DEVICE_IDENTIFIER = f"{MQTT_BASE_IDENTIFIER}-gatepi"

def mqtt_trigger_log(dict):
	if mqtt_trigger is not None:
		mqtt_trigger.trigger(json.dumps(dict))
	else:
		logging.info("mqtt_trigger not set up. unable to log.")


# # Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host=MQTT_HOST)

# # Define the device. At least one of `identifiers` or `connections` must be supplied
device_info = DeviceInfo(name=MQTT_DEVICE_NAME, identifiers=MQTT_DEVICE_IDENTIFIER)

# # Define an optional object to be passed back to the callback
user_data = "Some custom data"

def create_button_function(name_suffix, callback):
	def button_function():
		info = ButtonInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-{name_suffix}", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-{name_suffix}", device=device_info)
		settings = Settings(mqtt=mqtt_settings, entity=info)
		button = Button(settings, callback, user_data)
		button.write_config()
	return button_function

def create_callback_function(command, action):
	def callback(client: Client, user_data, message: MQTTMessage):
		dict = {"Command": f"HA Override {command}"}
		mqtt_trigger_log(dict)
		logging.info(f"{command} triggered from HomeAssistant")
		logging.info(f"{message.payload}")
		action()
	return callback

def create_trigger_function():
	global mqtt_trigger
	try:
		mqtt_trigger_info = DeviceTriggerInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-device-log-trigger", type="button_press", subtype="device-log", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-device-log-trigger", device=device_info)
		mqtt_trigger_settings = Settings(mqtt=mqtt_settings, entity=mqtt_trigger_info)
		mqtt_trigger = DeviceTrigger(mqtt_trigger_settings)
	except Exception as e:
		logging.warning(f"Failed to set up MQTT trigger: {e}")
		mqtt_trigger = None

def create_binary_sensor_function():
	global mqtt_binary_sensor
	try:
		info = BinarySensorInfo(name=f"{MQTT_BASE_IDENTIFIER}-gatepi-access-code-entered", unique_id=f"{MQTT_BASE_IDENTIFIER}-gatepi-access-code-entered", device=device_info)
		settings = Settings(mqtt=mqtt_settings, entity=info)
		mqtt_binary_sensor = BinarySensor(settings)
		mqtt_binary_sensor.set_attributes({"AccessLevel": "bootup", "AccessCode": "bootup",  "Name": "bootup", "Datetime": str(datetime.now().astimezone(tz))})
	except Exception as e:
		logging.warning(f"Failed to set up MQTT binary sensor: {e}")
		mqtt_binary_sensor = None

# Define the button functions
create_mqtt_gate_open_button = create_button_function("gate-open", create_callback_function("OPEN", lambda: gate.open()))
create_mqtt_gate_hold_open_button = create_button_function("gate-hold-open", create_callback_function("HOLD OPEN", lambda: gate.open(True)))
create_mqtt_gate_close_button = create_button_function("gate-close", create_callback_function("CLOSE", lambda: gate.close()))
create_mqtt_gate_stop_button = create_button_function("gate-stop", create_callback_function("STOP", lambda: gate.stop()))
create_mqtt_gate_release_stop_button = create_button_function("gate-release_stop", create_callback_function("RELEASE STOP", lambda: gate.releaseStop()))

# List of functions to be called
functions_to_call = [
	create_mqtt_gate_open_button, 
	create_mqtt_gate_hold_open_button, 
	create_mqtt_gate_close_button, 
	create_mqtt_gate_stop_button, 
	create_mqtt_gate_release_stop_button,
	create_trigger_function,
	create_binary_sensor_function
]

# Retry logic
def retry_on_network_error(func, delay=10):
	attempt = 0
	while True:
		logging.debug(f"Retry {attempt} in {delay} seconds...")
		try:
			func()
			break
		except OSError as error:
			if error.errno == 101:
				attempt += 1
				logging.debug(f"Network unreachable.")
				logging.debug(f"Retry {attempt} in {delay} seconds...")
				time.sleep(delay)
			else:
				logging.debug(f"Unhandled OSError in {func.__name__}: {error.errno}")
				logging.debug(f"Retry {attempt} in {delay} seconds...")
				break
		except Exception as error:
			logging.debug(f"Unhandled Exception in {func.__name__}: {error}: {error.errno}")
			logging.debug(f"Retry {attempt} in {delay} seconds...")
			break

def start_retry_in_thread(func: Callable, delay=10):
	thread = threading.Thread(target=retry_on_network_error, args=(func, delay))
	thread.daemon = True  # Ensure the thread exits when the main program does
	thread.start()

# Start all functions with retry logic in separate threads
for func in functions_to_call:
	start_retry_in_thread(func)

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