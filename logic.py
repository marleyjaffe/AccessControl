'''
https://stackabuse.com/a-sqlite-tutorial-with-python/

Ring Phone Number
Text Message
Trigger Home Assistant Event (MQTT)
'''

from db_utils import *
from StreetAutomation import *
	
#set pin num variables
oPIN = 12
cPIN = 13
sPIN = 15
lPIN = 11

def setup():
	'''
	Setup Lock object for package drop
	'''
	exPkgLck = lock("package", 11)

	'''
	Setup gate object
	'''
	gate = gate("gate1", {"open": oPIN, "close": cPIN, "stop": sPIN})

	'''
	Setup database connection
	'''
	con = db_connect()
	cur = con.cursor()

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
		while True:

			keypad = input("Enter Access Code: ")
			setup()
			logic(keypad)
			
	finally:
		gpioCleanup()







