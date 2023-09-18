'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
'''

# python 3.6

from db_utils import *
from StreetAutomation import *

import json
import logging
import random
import time
from paho.mqtt import client as mqtt_client
	
#set pin num variables
O_PIN = 12
C_PIN = 13
S_PIN = 15
L_PIN = 11

BROKER = '10.10.10.3'
PORT = 1883
SUB_TOPIC = "accesscontrol/#"
DEFAULT_PUB_TOPIC = "accesscontrol/gate"
# generate client ID with pub prefix randomly
CLIENT_ID = f'python-mqtt-tcp-pub-sub-{random.randint(0, 1000)}'
USERNAME = ''
PASSWORD = ''

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

FLAG_EXIT = False

def on_connect(client, userdata, flags, rc):
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
    else:
        print(f'Failed to connect, return code {rc}')


def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    global FLAG_EXIT
    FLAG_EXIT = True


def connect_mqtt():
    client = mqtt_client.Client(CLIENT_ID)
    # client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=120)
    client.on_disconnect = on_disconnect
    return client


def subscribe(client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        if msg.topic == "accesscontrol/gate/OPEN":
            gate.open()
        elif msg.topic == "accesscontrol/gate/CLOSE":
            gate.close()
        elif msg.topic == "accesscontrol/gate/STOP":
            gate.stop()
        elif msg.topic == "accesscontrol/lock/OPEN":
            lock.open()


    client.subscribe(SUB_TOPIC)
    client.on_message = on_message

    print(f"Subscribed to {SUB_TOPIC}!")


def publish(client, PUB_TOPIC =DEFAULT_PUB_TOPIC, msg ="test"):
    if not FLAG_EXIT:
        # msg_dict = {
        #     'msg': msg_count
        # }
        # msg = json.dumps(msg_dict)
        msg = "test"
        if not client.is_connected():
            logging.error("publish: MQTT client is not connected!")
            time.sleep(1)
        result = client.publish(PUB_TOPIC, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f'Send `{msg}` to topic `{PUB_TOPIC}`')
        else:
            print(f'Failed to send message to topic {PUB_TOPIC}')


def runMQTTSetup():
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                        level=logging.DEBUG)
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

def logic(keypad_input):
	accessLevel = search_code(con, keypad_input)

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
	elif accessLevel == "stop":
		print("stopping gate")
		gate.stop(2)
	else:
		#TODO: flash lights like an angry old man
		print("no hits found for either access level or code")
		pass

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
		runMQTTSetup()
		while True:
			keypad = input("Enter Access Code: ")
			logic(keypad)
			
	finally:
		gpioCleanup()







