'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
'''

from db_utils import *
from StreetAutomation import *

if __name__ == '__main__' :

    '''
    Setup Lock object for package drop
    '''
	exPkgLck = lock("package", 11)

	#set pin num variables
	oPIN = 12
	cPIN = 13
	sPIN = 15

	'''
	create gate object
	'''
	gate = gate("gate1", ["open" = oPIN, "close" = cPIN, "stop" = sPIN])

	'''
	Setup database connection
	'''
	con = db_connect()
	cur = con.cursor()

	keypad = input("Enter Access Code")

	accessLevel = searchCode(con,keypad)

	if accessLevel = "gate":
		print("gate open")
		#gate.open()
		lock.open(15)
	elif accessLevel = "owner":
		print("owner")
		#gate.PersonOpen()
		lock.open(15)
	elif acccessLevel = "lock":
		print("lock open")
		lock.open(30)
	else:
		#flash lights like an angry old man
	











