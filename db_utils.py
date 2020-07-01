# db_utils.py
import os
import sqlite3

# create a default path to connect to and create (if necessary) a database
# called 'database.sqlite3' in the same directory as this script
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')

def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con

'''
Creates entry into code table
'''
def create_code(con, passedcode, passedname, passedaccesslevel):
    sql = """
        INSERT INTO codes (code, name, accesslevel)
        VALUES (?, ?, ?)"""
    cur = con.cursor()
    cur.execute(sql, (passedcode, passedname, passedaccesslevel))
    con.commit()
    return cur.lastrowid

'''
returns access level for passed code
TODO: Add no match logic
'''
def search_code(con, passedcode):
	sql = "SELECT code, name, accesslevel FROM codes WHERE code = " + passedcode
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute(sql)
	result = cur.fetchone()
	returnedCode, returnedName, returnedAccessLevel = result['code'], result['name'], result['accesslevel']
	print("Code: ", returnedCode, " Name is: ", returnedName, " Level is: ", returnedAccessLevel)
	return returnedAccessLevel

'''
prints and returns all entries in the codes table
'''
def all_codes(con):
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
Used for direct interaction into SQLite Database\

from db_utils import *
con = db_connect()
cur = con.cursor()
'''





