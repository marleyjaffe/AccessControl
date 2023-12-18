'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
	-> change to async MQTT to stop blocking when 
'''

# python 3.10

from db_utils import *
from StreetAutomation import *

import json
import logging
import random
import time

from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Cover, CoverInfo, Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage

	
#set pin num variables
O_PIN = 12
C_PIN = 13
S_PIN = 15
L_PIN = 11



def logic(keypad_input):
	accessLevel = search_code(con, keypad_input)

	if accessLevel == "gate":
		print("gate open")
		gate.open()
		catt_gate.open()
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
	else:
		#TODO: flash lights like an angry old man
		print("no hits found for either access level or code")
		pass



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
		# let HA know that the cover is opening
		catt_gate.opening()
		# call function to open cover
		gate.open()
		# Let HA know that the cover was opened
		catt_gate.open()
	if payload == "CLOSE":
		# let HA know that the cover is closing
		catt_gate.closing()
		# call function to close the cover
		gate.close()
		# Let HA know that the cover was closed
		catt_gate.closed()
	if payload == "STOP":
		# call function to stop the cover
		gate.stop()
		# Let HA know that the cover was stopped
		catt_gate.stopped()

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
			Send result of db check to HomeAssistant

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
		while True:
			keypad = input("Enter Access Code: ")
			logic(keypad)
			
	finally:
		gpioCleanup()







