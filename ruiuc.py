from pysqlite2 import dbapi2 as sqlite
from collections import defaultdict
import simplejson as json
import sys
import re

# simple site, simple concept
# only one db relation: unique_url <--> [crn], personal_string

STRING_TABLE_NAME = "ruiuc_string"
CRN_TABLE_NAME = "ruiuc_crn"
DATABASE_NAME = "/home/smiley325/projects/uiucredditfinder/uiuc_reddit.db"

def db_exists_check():
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + CRN_TABLE_NAME + "'")
    res = cursor.fetchall()
    
    if(len(res) <= 0):
        cursor.execute("CREATE TABLE " + CRN_TABLE_NAME + " (pk INTEGER PRIMARY KEY, uid VARCHAR(32), crn INTEGER)")
        
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + STRING_TABLE_NAME + "'")
    res = cursor.fetchall()
    
    if(len(res) <= 0):
        cursor.execute("CREATE TABLE " + STRING_TABLE_NAME + " (pk INTEGER PRIMARY KEY, uid VARCHAR(32), personal_string VARCHAR(1024))")
        
    connection.commit()
    connection.close()

def get_from_uid(uid):
    db_exists_check()
    
    # validate input data
    if re.search(r'[^a-zA-Z:,0-9\s]+', uid) is not None:
        return json.dumps({'error': 'sql'})
    
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
    
    # Return the JSON object {personal_string, [crn]}
    personal_string = ""
    crn_list = []
    
    cursor.execute("SELECT personal_string FROM " + STRING_TABLE_NAME + " WHERE uid IS \"" + uid + "\"")
    res = cursor.fetchall()
    
    if(len(res) <= 0):
        personal_string = ""
    else:
        personal_string = res[0][0]
        
    cursor.execute("SELECT crn FROM " + CRN_TABLE_NAME + " WHERE uid IS \"" + uid + "\"")
    res = cursor.fetchall()
    
    for row in res:
        crn_list.append(row[0])
    
    connection.close()
    return json.dumps({'personal_string': personal_string, 'crn_list': crn_list})
    
def get_from_crn(crn):
    db_exists_check()
    
    # validate input data
    if re.search(r'[^a-zA-Z:,0-9\s]+', crn) is not None:
        return json.dumps({'error': 'sql'})
        
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
    
    personal_string_list = []
    
    cursor.execute("SELECT ruiuc_string.personal_string FROM ruiuc_crn, ruiuc_string WHERE ruiuc_crn.uid = ruiuc_string.uid AND ruiuc_crn.crn = " + crn)
    res = cursor.fetchall()
    
    for row in res:
        personal_string_list.append(row[0])
        
    connection.close()
    return json.dumps({'personal_strings': personal_string_list})
    
def html_escape(text):
    text = text.replace('&', '&amp;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    text = text.replace(">", '&gt;')
    text = text.replace("<", '&lt;')
    return text
    
def put_to_uid(uid, crn_list_, personal_string):
    db_exists_check()
    
    personal_string = html_escape(personal_string)
    
    # validate input data
    if re.search(r'[^a-zA-Z:,&;#0-9\s]+', uid + crn_list_ + personal_string) is not None:
        return json.dumps({'error': 'sql'})
        
    crn_list = crn_list_.split(',')
    
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM " + STRING_TABLE_NAME + " WHERE uid=\"" + uid + "\"")
    res = cursor.fetchall()
    
    if(len(res) > 0):
        return json.dumps({'error': 'uidtaken'})
        
    cursor.execute("INSERT INTO " + STRING_TABLE_NAME + " (uid, personal_string) VALUES (\"" + uid + "\", \"" + personal_string + "\")")
    
    for crn in crn_list:
        cursor.execute("INSERT INTO " + CRN_TABLE_NAME + " (uid, crn) VALUES (\"" + uid + "\", " + crn + ")")
        
    connection.commit()
    connection.close()
    
    return json.dumps({'success': ''})
    