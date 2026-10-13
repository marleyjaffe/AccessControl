'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
	-> change to async MQTT to stop blocking when 
'''

# python 3.10

from db_utils import *
import config

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
from paho.mqtt.enums import CallbackAPIVersion

#Keyboard Imports
import asyncio, evdev
from evdev import InputDevice, categorize, ecodes

tz = ZoneInfo(config.TZ)

logging.Formatter.converter = time.localtime
logging.basicConfig(format='%(asctime)s %(levelname)s- %(message)s',
					datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(config.LOG_LEVEL)

#set pin num variables
O_PIN = config.GATE_OPEN_PIN
C_PIN = config.GATE_CLOSE_PIN
S_PIN = config.GATE_STOP_PIN
L_PIN = config.LOCK_PIN

gpioOpen = gpiozero.OutputDevice(O_PIN, active_high=True, initial_value=False)
gpioClose = gpiozero.OutputDevice(C_PIN, active_high=True, initial_value=False)
gpioStop = gpiozero.OutputDevice(S_PIN, active_high=True, initial_value=False)
gpioLock = gpiozero.OutputDevice(L_PIN, active_high=True, initial_value=False)

#Reed switch pin num variables (BCM). Defaults: physical header pins 16, 18, 22 with GND on pin 20.
#Wired between GPIO and GND using the internal pull-up: magnet present (closed) = LOW
GATE_REED_PIN = config.GATE_REED_PIN
MAILBOX1_REED_PIN = config.MAILBOX1_REED_PIN
MAILBOX2_REED_PIN = config.MAILBOX2_REED_PIN

class reedSwitch:
	'''
	Magnetic reed switch. Reports open/closed locally (isOpen, listeners) and to HA over MQTT.
	Listeners are called as callback(reedSwitch) from the gpiozero thread on every state change.
	'''
	bounce_time = config.REED_BOUNCE_TIME

	def __init__(self, name, key, gpioNumber):
		self.name = name
		self.key = key
		self.pin = gpioNumber
		self.mqtt_sensor = None
		self.listeners = []
		self.last_changed = datetime.now().astimezone(tz)
		self.device = gpiozero.Button(gpioNumber, pull_up=True, bounce_time=self.bounce_time)
		self.device.when_pressed = self._changed
		self.device.when_released = self._changed

	@property
	def isOpen(self):
		# pressed == pin pulled LOW == magnet present == closed
		return not self.device.is_pressed

	@property
	def state(self):
		return "open" if self.isOpen else "closed"

	def add_listener(self, callback: Callable):
		self.listeners.append(callback)

	def _changed(self):
		self.last_changed = datetime.now().astimezone(tz)
		logging.info(f"{self.name} {self.state.upper()}")
		self.publish()
		for callback in self.listeners:
			try:
				callback(self)
			except Exception as error:
				logging.error(f"{self.name} listener error: {error}")

	def publish(self):
		if self.mqtt_sensor is None or not mqtt_is_connected():
			logging.debug(f"{self.name} MQTT offline. not published.")
			return
		try:
			if self.isOpen:
				self.mqtt_sensor.on()
			else:
				self.mqtt_sensor.off()
			self.mqtt_sensor.set_attributes({"State": self.state, "LastChanged": str(self.last_changed), "GPIO": self.pin})
		except Exception as error:
			logging.warning(f"Failed to publish {self.name} state: {error}")

gateReed = reedSwitch("Gate", "gate", GATE_REED_PIN)
mailbox1Reed = reedSwitch("Mailbox 1", "mailbox-1", MAILBOX1_REED_PIN)
mailbox2Reed = reedSwitch("Mailbox 2", "mailbox-2", MAILBOX2_REED_PIN)
reed_switches = [gateReed, mailbox1Reed, mailbox2Reed]

#Keyboard device mapping
kbd_outside = evdev.InputDevice(config.KEYPAD_OUTSIDE_DEVICE)
kbd_inside =  evdev.InputDevice(config.KEYPAD_INSIDE_DEVICE)

#prevent other applications from receiveing keypad input
kbd_outside.grab()
kbd_inside.grab()

#set initial keypad string
isKeypadActive = False
keypad_string = ''
keypad_string_max_length = config.KEYPAD_CODE_MAX_LENGTH
keypad_string_timeout = config.KEYPAD_CODE_TIMEOUT
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
						gate.stop()
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
	mqtt_set_access_attributes({"AccessLevel": accessLevel, "AccessCode": keypad_input, "Name": codeName, "Datetime": str(datetime.now().astimezone(tz)), "Location": location})

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
		gate.stop()
	elif accessLevel in ("person", "party"):
		# "party" is the legacy name for person open, kept so existing codes keep working
		logging.info(f"PERSON OPEN function triggered")
		gate.personOpen()
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
	default_time = config.LOCK_UNLOCK_TIME
	
	def __init__(self, name, gpioNumber):
		self.name = name
		self.pin = gpioNumber
		pass

	def open(self, unlocktime=default_time):
		gpioLock.on()
		time.sleep(unlocktime)
		gpioLock.off()

class gate:
	personOpenLength = config.GATE_PERSON_OPEN_LENGTH
	personTime = config.GATE_PERSON_TIME
	toggle_length = config.GATE_TOGGLE_LENGTH
	stop_hold_timeout = config.GATE_STOP_HOLD_TIMEOUT
	hard_open_timeout = config.GATE_HOLD_OPEN_TIMEOUT
	
	def __init__(self, name, pins, reed=None):
		self.name = name
		self.pinArray = pins
		self.reed = reed
		self.isStopped = False
		self.isHardOpen = False
		# person open runs in a background thread; this Event cancels the active run
		self._personCancel = None
		self._personLock = threading.Lock()

	@property
	def isOpen(self):
		# None when no reed switch is attached (position unknown)
		return self.reed.isOpen if self.reed is not None else None

	@property
	def isPersonOpen(self):
		return self._personCancel is not None
		
	def open(self, isHardOpen=False):
		self.cancelPersonOpen()
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
		self.cancelPersonOpen()
		self.releaseHardOpen()
		self.releaseStop()
		gpioClose.on()
		time.sleep(self.toggle_length)
		gpioClose.off()

	def stop(self):
		'''Hold the stop relay until releaseStop()/open()/close(), or stop_hold_timeout (then close).'''
		# set before cancelling so a running person open leaves the stop relay on for us
		self.isStopped = True
		self.cancelPersonOpen()
		self.releaseHardOpen()

		thread = threading.Thread(target=self.runAsyncMonitorIsStopped)
		thread.start()

	# PERSON OPEN: open, stop at a person-width gap, hold, then close. Never blocks the caller.
	def personOpen(self):
		self.cancelPersonOpen()
		self.releaseHardOpen()
		self.releaseStop()
		cancel = threading.Event()
		with self._personLock:
			self._personCancel = cancel
		thread = threading.Thread(target=self._personOpenSequence, args=(cancel,), daemon=True)
		thread.start()

	def cancelPersonOpen(self):
		'''Any other gate command takes over from a running person open.'''
		with self._personLock:
			cancel, self._personCancel = self._personCancel, None
		if cancel is not None:
			cancel.set()

	def _personOpenSequence(self, cancel):
		try:
			logging.info(f"PERSON OPEN: opening for {self.personOpenLength}s")
			gpioOpen.on()
			time.sleep(self.toggle_length)
			gpioOpen.off()
			if cancel.wait(self.personOpenLength):
				logging.info(f"PERSON OPEN cancelled while opening")
				return

			logging.info(f"PERSON OPEN: stopped for {self.personTime}s")
			gpioStop.on()
			if cancel.wait(self.personTime):
				logging.info(f"PERSON OPEN cancelled while stopped")
				# leave the stop relay on only if a STOP command took over
				if not self.isStopped:
					gpioStop.off()
				return

			with self._personLock:
				if cancel.is_set():
					return
				self._personCancel = None
			logging.info(f"PERSON OPEN: closing")
			gpioStop.off()
			self.close()
		except Exception as error:
			logging.error(f"PERSON OPEN failed: {error}")
			gpioStop.off()

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
			# relay cleanup only: this runs after the stop was already released, and must
			# not cancel a person open that the release started
			self._releaseStopRelay()

	async def waitIsStoppedFalse(self):
		while self.isStopped:
			await asyncio.sleep(0.5)
	
	def releaseStop(self):
		self.cancelPersonOpen()
		self._releaseStopRelay()

	def _releaseStopRelay(self):
		self.isStopped = False
		gpioStop.off()

#######MQTT#######
# MQTT is optional. Nothing here may block or raise into the keypad/gate path:
# - a single shared paho client connects in the background (connect_async + loop_start)
#   and retries forever, so a missing broker never delays startup
# - HA entities are (re)created in on_connect, so they come back after broker/HA restarts
# - publish helpers swallow errors; when offline, events are only logged locally

MQTT_BASE_NAME = config.MQTT_BASE_NAME
MQTT_DEVICE_NAME = f"{MQTT_BASE_NAME}-AccessControl"
MQTT_BASE_IDENTIFIER = config.MQTT_BASE_IDENTIFIER
MQTT_DEVICE_IDENTIFIER = f"{MQTT_BASE_IDENTIFIER}-gatepi"

mqtt_client = None
mqtt_trigger = None
mqtt_binary_sensor = None

def mqtt_is_connected():
	return mqtt_client is not None and mqtt_client.is_connected()

def mqtt_trigger_log(dict):
	if mqtt_trigger is None or not mqtt_is_connected():
		logging.debug(f"MQTT offline, not sent: {dict}")
		return
	try:
		mqtt_trigger.trigger(json.dumps(dict))
	except Exception as error:
		logging.warning(f"Failed to send MQTT trigger: {error}")

def mqtt_set_access_attributes(attributes):
	if mqtt_binary_sensor is None or not mqtt_is_connected():
		return
	try:
		mqtt_binary_sensor.set_attributes(attributes)
	except Exception as error:
		logging.warning(f"Failed to set MQTT access attributes: {error}")

def create_callback_function(command, action):
	def callback(client: Client, user_data, message: MQTTMessage):
		try:
			mqtt_trigger_log({"Command": f"HA Override {command}"})
			logging.info(f"{command} triggered from HomeAssistant")
			logging.debug(f"{message.payload}")
			action()
		except Exception as error:
			logging.error(f"HA {command} failed: {error}")
	return callback

# (name suffix, command label, action) for HA buttons
mqtt_buttons = [
	("gate-open", "OPEN", lambda: gate.open()),
	("gate-hold-open", "HOLD OPEN", lambda: gate.open(True)),
	("gate-close", "CLOSE", lambda: gate.close()),
	("gate-stop", "STOP", lambda: gate.stop()),
	("gate-release_stop", "RELEASE STOP", lambda: gate.releaseStop()),
	("gate-person-open", "PERSON OPEN", lambda: gate.personOpen()),
]

def mqtt_create_entities(mqtt_settings, device_info):
	'''Create/refresh all HA entities. Each entity is independent so one failure does not block the rest.'''
	global mqtt_trigger, mqtt_binary_sensor

	def entity_id(suffix):
		return f"{MQTT_BASE_IDENTIFIER}-gatepi-{suffix}"

	for suffix, command, action in mqtt_buttons:
		try:
			info = ButtonInfo(name=entity_id(suffix), unique_id=entity_id(suffix), device=device_info)
			Button(Settings(mqtt=mqtt_settings, entity=info), create_callback_function(command, action)).write_config()
		except Exception as error:
			logging.warning(f"Failed to set up MQTT button {suffix}: {error}")

	try:
		info = DeviceTriggerInfo(name=entity_id("device-log-trigger"), type="button_press", subtype="device-log", unique_id=entity_id("device-log-trigger"), device=device_info)
		trigger = DeviceTrigger(Settings(mqtt=mqtt_settings, entity=info))
		trigger.write_config()
		mqtt_trigger = trigger
	except Exception as error:
		logging.warning(f"Failed to set up MQTT trigger: {error}")

	try:
		info = BinarySensorInfo(name=entity_id("access-code-entered"), unique_id=entity_id("access-code-entered"), device=device_info)
		sensor = BinarySensor(Settings(mqtt=mqtt_settings, entity=info))
		if mqtt_binary_sensor is None:
			sensor.set_attributes({"AccessLevel": "bootup", "AccessCode": "bootup",  "Name": "bootup", "Datetime": str(datetime.now().astimezone(tz))})
		else:
			sensor.write_config()
		mqtt_binary_sensor = sensor
	except Exception as error:
		logging.warning(f"Failed to set up MQTT binary sensor: {error}")

	for reed in reed_switches:
		try:
			info = BinarySensorInfo(name=entity_id(f"{reed.key}-contact"), unique_id=entity_id(f"{reed.key}-contact"), device_class="opening", device=device_info)
			reed.mqtt_sensor = BinarySensor(Settings(mqtt=mqtt_settings, entity=info))
			# publish current state so HA is correct after boot/reconnect
			reed.publish()
		except Exception as error:
			logging.warning(f"Failed to set up MQTT {reed.name} sensor: {error}")

def mqtt_start():
	'''Start the background MQTT connection. Returns immediately; never raises.'''
	global mqtt_client
	for warning in config.WARNINGS:
		logging.warning(warning)
	if not config.MQTT_ENABLED:
		return

	try:
		client = Client(callback_api_version=CallbackAPIVersion.VERSION2)
		client.username_pw_set(config.MQTT_USERNAME, password=config.MQTT_PASSWORD)
		client.reconnect_delay_set(min_delay=1, max_delay=60)

		mqtt_settings = Settings.MQTT(
			host=config.MQTT_HOST,
			port=config.MQTT_PORT,
			username=config.MQTT_USERNAME,
			password=config.MQTT_PASSWORD,
			discovery_prefix=config.MQTT_DISCOVERY_PREFIX,
			client=client
		)
		# At least one of `identifiers` or `connections` must be supplied
		device_info = DeviceInfo(name=MQTT_DEVICE_NAME, identifiers=MQTT_DEVICE_IDENTIFIER)

		def on_connect(client, userdata, flags, reason_code, properties):
			if reason_code.is_failure:
				logging.warning(f"MQTT connection to {config.MQTT_HOST}:{config.MQTT_PORT} refused: {reason_code}")
				return
			logging.info(f"MQTT connected to {config.MQTT_HOST}:{config.MQTT_PORT}")
			try:
				mqtt_create_entities(mqtt_settings, device_info)
			except Exception as error:
				# never let an exception escape into (and kill) the paho network thread
				logging.error(f"MQTT entity setup failed: {error}")

		def on_disconnect(client, userdata, flags, reason_code, properties):
			logging.warning(f"MQTT disconnected ({reason_code}). Keypads/gate continue offline; reconnecting in background.")

		def on_connect_fail(client, userdata):
			logging.debug(f"MQTT connection to {config.MQTT_HOST}:{config.MQTT_PORT} failed, retrying")

		client.on_connect = on_connect
		client.on_disconnect = on_disconnect
		client.on_connect_fail = on_connect_fail
		client.connect_async(config.MQTT_HOST, config.MQTT_PORT)
		client.loop_start()
		mqtt_client = client
		logging.info(f"MQTT connecting to {config.MQTT_HOST}:{config.MQTT_PORT} in background")
	except Exception as error:
		logging.error(f"MQTT setup failed, running offline: {error}")

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
		gate = gate("gate1", {"open": O_PIN, "close": C_PIN, "stop": S_PIN}, reed=gateReed)

		'''
		Start MQTT in the background (optional, never blocks keypads)
		'''
		mqtt_start()

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