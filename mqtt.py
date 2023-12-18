from ha_mqtt_discoverable import *
# from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Cover, CoverInfo, Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage

from StreetAutomation import *
from logic import *


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