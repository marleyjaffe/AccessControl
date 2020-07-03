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
	gate = gate("gate1", {"open": oPIN, "close": cPIN, "stop": sPIN})

	'''
	Setup database connection
	'''
	con = db_connect()
	cur = con.cursor()

	try:
		while True:

			keypad = input("Enter Access Code: ")

			accessLevel = search_code(con, keypad)

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
				#flash lights like an angry old man
				pass
	finally:
		gpioCleanup()
