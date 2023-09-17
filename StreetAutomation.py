#StreetAutomation.py
#https://pi4j.com/1.2/pins/model-b-rev2.html

import RPi.GPIO as GPIO

import time

#pin numbers (BOARD) or the Broadcom GPIO numbers (BCM)
GPIO.setmode(GPIO.BOARD)


class lock:
	def __init__(self, name, gpioNumber):
		self.name = name
		self.pin = gpioNumber
		GPIO.setup(self.pin,GPIO.OUT)
		GPIO.output(self.pin,GPIO.HIGH)
		pass

	def open(self, unlocktime=15):
		print("Opening " + self.name + " for: " + str(unlocktime) + "sec")
		GPIO.output(self.pin,GPIO.LOW)
		time.sleep(unlocktime)
		print("Locking " + self.name + " trigger")
		GPIO.output(self.pin,GPIO.HIGH)

class gate:
	personTime = 10
	toggle_length = .3

	def __init__(self, name, pins):
		self.name = name
		self.pinArray = pins
		for x in pins:
			GPIO.setup(self.pinArray[x],GPIO.OUT)
			GPIO.output(self.pinArray[x],GPIO.HIGH)
		pass

	def open(self):
		print("OPEN FUNCTION STARTING " + self.name)
		GPIO.output(self.pinArray["open"],GPIO.LOW)
		time.sleep(self.toggle_length)
		print("Releasing " + self.name + " trigger")
		GPIO.output(self.pinArray["open"],GPIO.HIGH)
		pass

	def close(self):
		print("CLOSE FUNCTION STARTING " + self.name)
		GPIO.output(self.pinArray["close"],GPIO.LOW)
		time.sleep(self.toggle_length)
		print("Releasing " + self.name + " trigger")
		GPIO.output(self.pinArray["close"],GPIO.HIGH)
		pass

	def stop(self, stoptime=toggle_length):
		print("STOP FUNCTION STARTING " + self.name + " for: " + str(stoptime) + "sec")
		GPIO.output(self.pinArray["stop"],GPIO.LOW)
		time.sleep(stoptime)
		print("Releasing " + self.name + " trigger")
		GPIO.output(self.pinArray["stop"],GPIO.HIGH)
		pass

	def personOpen(self, openLength=4):
		print("PERSONOPEN FUNCTION STARTING " + self.name + " for: " + str(self.personTime) + "sec")
		self.open()
		time.sleep(openLength)
		self.stop(self.personTime)
		print("Closing " + self.name)
		self.close()
		pass

def gpioCleanup():
	GPIO.cleanup()
	print("cleaned up rpi GPIO pins")


if __name__ == '__main__' :

	exPkgLck = lock("package", 11)

	print(exPkgLck.name)
	print(exPkgLck.pin) 
	exPkgLck.open(15)

	#set pin num variables
	oPIN = 12
	cPIN = 13
	sPIN = 15

	gate = gate("gate1", {"open": oPIN, "close": cPIN, "stop": sPIN})

	print(gate.name + " opening")
	gate.open()
	time.sleep(1)
	print(gate.name + " closing")
	gate.close()
	time.sleep(1)
	print(gate.name + " stop")
	gate.stop(2)
	time.sleep(1)
	print(gate.name + " close")
	gate.close()
	GPIO.cleanup()
