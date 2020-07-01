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

	def open(self, time):
		print("Opening " + self.name + " for: " + time + "sec")
		GPIO.output(self.pin,GPIO.LOW)
		time.sleep(time)
		print("Locking " + self.name " trigger")
		GPIO.output(self.pin,GPIO.HIGH)
  		pass

class gate:
	personTime = 5

	def __init__(self, name, pins):
	    self.name = name
	    self.pinArray = pins
		for x in pins:
	  		GPIO.setup(self.pinArray[x],GPIO.OUT)
	  		GPIO.output(self.pinArray[x],GPIO.HIGH)
		pass

	def open(self):
		print("Opening " + self.name)
		GPIO.output(self.pinArray["open"],GPIO.LOW)
		time.sleep(.300)
		print("Releasing " + self.name + " trigger")
		GPIO.output(pinArray["open"],GPIO.HIGH)
  		pass

	def close(self):
		print("Closing " + self.name)
		GPIO.output(self.pinArray["close"],GPIO.LOW)
		time.sleep(.300)
		print("Releasing " + self.name + " trigger")
		GPIO.output(pinArray["close"],GPIO.HIGH)
  		pass

	def stop(self, time):
		print("Stopping " + self.name + " for: " + time + "sec")
		GPIO.output(self.pinArray["stop"],GPIO.LOW)
		time.sleep(time)
		print("Releasing " + self.name + " trigger")
		GPIO.output(pinArray["open"],GPIO.HIGH)
  		pass

  	def personOpen(self):
		print("Opening " + self.name + " for: " + personTime + "sec")
		open()
		stop(personTime)
		print("Closing " + self.name)
		close()
  		pass



if __name__ == '__main__' :
    
	exPkgLck = lock("package", 11)

	print(exPkgLck.name)
	print(exPkgLck.pin) 

	#set pin num variables
	oPIN = 12
	cPIN = 13
	sPIN = 15


	gate = gate("gate1", ["open" = oPIN, "close" = cPIN, "stop" = sPIN])

	print(gate.name + " opening")
	gate.open()
	time.sleep(1)
	print(gate.name + " closing")
	gate.close()
	time.sleep(1)
	print(gate.name + " stop")
	gate.stop()
	time.sleep(1)
	print(gate.name + " close")
	gate.close()
