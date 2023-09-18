#mqtt.py
# https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
# https://github.com/emqx/MQTT-Client-Examples/blob/master/mqtt-client-Python3/pub_sub_tcp.py

# python 3.6

import json
import logging
import random
import time

from paho.mqtt import client as mqtt_client

# from StreetAutomation import *
# from logic import *


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
        elif msg.topic == "accesscontrol/gate/CLOSE":
            gate.stop()
        elif msg.topic == "accesscontrol/lock/OPEN":
            lock.open(5)


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
    


if __name__ == '__main__':
    run()