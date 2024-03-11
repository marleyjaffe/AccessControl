# db_utils.py
import os
import sqlite3

# create a default path to connect to and create (if necessary) a database
# called 'database.sqlite3' in the same directory as this script
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')

def db_connect(db_path=DEFAULT_PATH):
	con = sqlite3.connect(db_path)
	return con


def create_code(con, passedcode, passedname, passedaccesslevel):
	'''
	Name:			create_code

	Description:	Creates entry into code table

	Input:			con: 				SQLite Connection
					passedcode:			pin code to add to db
					passedname:			name to associate to pincode in DB
					passedaccesslevel:	AccessLevel (action type) to store with PinCode

	Actions:		Uses sqlite to insert new pincode and additional info into DB

	Return:			Returns new rowid. Returns False if code already exists

	TODO: 			Check if pincode exists in DB yet. Prevent multi entries with same pincode. Return False if already exists
	'''

	sql = """
		INSERT INTO codes (code, name, accesslevel)
		VALUES (?, ?, ?)"""
	cur = con.cursor()
	cur.execute(sql, (passedcode, passedname, passedaccesslevel))
	con.commit()
	return cur.lastrowid


def search_code(con, passedcode):
	'''
	Name:			search_code

	Description:	returns access level for passed code

	Input:			con: 				SQLite Connection
					passedcode:			pincode to search for

	Actions:		Checks if passedcode is a valid search value.
					Searches for passedcode in DB.
					Returns AccessLevel

	TODO: 			Decide if checks and returns should be independent functions
	'''

	if passedcode == "":
		print("empty code passed to function. exiting search function safely")
		return None
	#Check if passedcode var is type string. If not, casts as a string
	elif not isinstance(passedcode, str):
		print("var not string. converting")
		passedcode = str(passedcode)
	sql = "SELECT code, name, accesslevel FROM codes WHERE code = " + passedcode
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute(sql)
	result = cur.fetchone()
	if result is not None:
		returnedCode, returnedName, returnedAccessLevel = result['code'], result['name'], result['accesslevel']
		print("Code: ", returnedCode, " Name is: ", returnedName, " Level is: ", returnedAccessLevel)
		return returnedAccessLevel
	else:
		print("No results found in table. Exiting function")
		return

def update_AccessLevel(con, passedCode, newAccessLevel):
	'''
	Name:			update_AccessLevel

	Description:	Updates PinCode AccessLevel

	Input:			con: 				SQLite Connection
					passedcode:			pincode to update
					newAccessLevel:		AccessLevel to update pincode to

	Actions:		Checks if passedcode is valid.
					SQL update accesslevel where pincode = passed value.
					
	Return:			Return False if passed code is not in db
					Returns True if function success
	'''

	if search_code(con, passedCode) is None:
		return False
	else:
		sql = """
			UPDATE codes 
			SET accesslevel = ?
			WHERE code = ?"""
		cur = con.cursor()
		cur.execute(sql, (newAccessLevel, passedCode))
		con.commit()
		return True

def update_name(con, passedCode, newName):
	'''
	Name:			update_name

	Description:	Updates PinCode name

	Input:			con: 				SQLite Connection
					passedcode:			pincode to update
					newName:			name to update pincode to

	Actions:		Checks if passedcode is valid.
					SQL update name where pincode = passed value.
	
	Return:			Return False if passed code is not in db
					Returns True if function success
	'''

	if search_code(con, passedCode) is None:
		return False
	else:
		sql = """
			UPDATE codes 
			SET name = ?
			WHERE code = ?"""
		cur = con.cursor()
		cur.execute(sql, (newName, passedCode))
		con.commit()
		return True

'''
removes code from sqlite db
'''
def delete_code(con, passedCode):
	'''
	Name:			delete_code

	Description:	removes code row from DB

	Input:			con: 				SQLite Connection
					passedcode:			pincode to update

	Actions:		Checks if passedcode is valid.
					SQL delete row

	Return:			Return False if passed code is not in db
					Returns True if function success
	'''

	if search_code(con, passedCode) is None:
		return False
	else:
		sql = " DELETE FROM codes WHERE code = ?"
		cur = con.cursor()
		cur.execute(sql, (passedCode,))
		con.commit()
		return True

'''
prints and returns all entries in the codes table
'''
def all_codes(con):
	'''
	Name:			all_codes

	Description:	returns all codes in DB

	Input:			con: 				SQLite Connection
					passedcode:			pincode to update

	Actions:		Select * from Codes table
					prints all code rows

	Return:			Returns all results
	'''

	sql = "SELECT * FROM codes"
	#con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute(sql)
	results = cur.fetchall()
	for row in results:
		print(row)
	return results

'''
creates new ringer entries
'''
def create_ring(con, passedcode, passedname, passednumber, passedoption):
	sql = """
		INSERT INTO ring (code, name, number, option)
		VALUES (?, ?, ?, ?)"""
	cur = con.cursor()
	cur.execute(sql, (passedcode, passedname, passednumber, passedoption))
	con.commit()
	return cur.lastrowid


'''
Passed code should be formatted: 'A'
'''
def search_ring(con, passedcode):
	sql = "SELECT code, name, number, option FROM ring WHERE code = " + passedcode
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute(sql)
	result = cur.fetchone()
	returnedCode, returnedName, returnedPhoneNumber, returnedCommunicationPreference = result['code'], result['name'], result['number'], result['option']
	print("Code: ", returnedCode, " Name is: ", returnedName, " number is: ", returnedPhoneNumber)
	return returnedPhoneNumber, returnedCommunicationPreference

'''
Returns all set rings
'''
def all_rings(con):
	sql = "SELECT * FROM ring"
	#con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute(sql)
	results = cur.fetchall()
	for row in results:
		print(row)
	return results

'''
Used for troubleshooting
'''
def all_tables(con):
	cur = con.cursor()
	cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
	print(cur.fetchall())

'''
Used for direct interaction into SQLite Database
In terminal run the below commands while in the application directory:

python3
from db_utils import *
con = db_connect()
cur = con.cursor()

'''





