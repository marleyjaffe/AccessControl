from ha_mqtt_discoverable import *
# from ha_mqtt_discoverable import Settings
# from ha_mqtt_discoverable.sensors import Cover, CoverInfo
from paho.mqtt.client import Client, MQTTMessage

from StreetAutomation import *
from logic import *


# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="10.10.10.3")

# Information about the cover
cover_info = CoverInfo(name="catt-gatepi")

settings = Settings(mqtt=mqtt_settings, entity=cover_info)

# To receive state commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
	payload = message.payload.decode()
	if payload == "OPEN":
		# let HA know that the cover is opening
		my_cover.opening()
		# call function to open cover
		gate.open()
		# Let HA know that the cover was opened
		my_cover.open()
	if payload == "CLOSE":
		# let HA know that the cover is closing
		my_cover.closing()
		# call function to close the cover
		close_my_custom_cover()
		# Let HA know that the cover was closed
		my_cover.closed()
	if payload == "STOP":
		# call function to stop the cover
		stop_my_custom_cover()
		# Let HA know that the cover was stopped
		my_cover.stopped()

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Instantiate the cover
my_cover = Cover(settings, my_callback, user_data)

# Set the initial state of the cover, which also makes it discoverable
my_cover.closed()