/*
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
*/

from db_utils import *
from StreetAutomation import *

keypad = input("Enter Access Code")


if __name__ == '__main__' :
    '''
    Setup Lock
    '''
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
	'''
	Setup database connection
	'''
	con = db_connect()
	cur = con.cursor()

	accessLevel = searchCode(con,keypad)

	if accessLevel = "gate":
