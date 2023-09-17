#mqtt.py
#http://www.steves-internet-guide.com/client-connections-python-mqtt/

#!python3
import paho.mqtt.client as mqtt  #import the client1
from paho.mqtt.properties import Properties #future proofing mqtt v5
from paho.mqtt.packettypes import PacketTypes #future proofing mqtt v5
import time

def on_connect(client, userdata, flags, rc, properties=None):
    if rc==0:
        client.connected_flag=True #set flag
        print("connected OK")
    else:
        print("Bad connection Returned code=",rc)

mqtt.Client.connected_flag=False#create flag in class
broker="10.10.10.3"
properties=None #needed for MQTTv3 with script supporting v5
client = mqtt.Client("gatepi", protocol=MQTTv3)             #create new instance 
client.on_connect=on_connect  #bind call back function
client.loop_start()
print("Connecting to broker ",broker)
client.connect(self, broker, port=1883, keepalive=60, bind_address="", bind_port=0, clean_start=MQTT_CLEAN_START_FIRST_ONLY, properties=None)      #connect to broker
while not client.connected_flag: #wait in loop
    print("In wait loop")
    time.sleep(1)
print("in Main Loop")
client.subscribe("gate/#")


client.loop_stop()    #Stop loop 
client.disconnect() # disconnect