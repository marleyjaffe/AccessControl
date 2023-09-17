#mqtt.py
#http://www.steves-internet-guide.com/client-connections-python-mqtt/

#!python3
import paho.mqtt.client as mqtt  #import the client1
import time

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        print("connected OK")
    else:
        print("Bad connection Returned code=",rc)

def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

mqtt.Client.connected_flag=False#create flag in class
broker="10.10.10.3"
client = mqtt.Client("gatepi")             #create new instance 
client.on_connect=on_connect  #bind call back function
client.on_message=on_message #attach function to callback
client.loop_start()
print("Connecting to broker ",broker)
client.connect(broker)      #connect to broker
while not client.connected_flag: #wait in loop
    print("In wait loop")
    time.sleep(1)
print("in Main Loop")
client.subscribe("gate/#")
#client.loop_stop()    #Stop loop 
#client.disconnect() # disconnect