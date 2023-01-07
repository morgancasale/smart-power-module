from customErrors import *
import pandas as pd
import sqlite3 as sq
import json
import re
import datetime

DBPath = "db.sqlite"
broker = "broker.hivemq.com"

def check_presence_inDB(DBPath, table, keyNames, keyValues):
    try:
        if(not isinstance(keyNames, list)) : keyNames = [keyNames]
        if(not isinstance(keyValues, list)) : keyValues = [keyValues]

        keyNames = "(" + ", ".join(keyNames) + ")"
        keyValues = "(\"" + "\", \"".join(keyValues) + "\")"

        query = "SELECT COUNT(*)>0 as result FROM " + table + " WHERE " + keyNames + " = " + keyValues
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"]) #True if the keyValue is present in the DB
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))
    

def check_presence_ofColumnInDB(DBPath, table, columnName):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM pragma_table_info(\"" + table + "\") WHERE name=\"" + columnName + "\""
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

def check_presence_ofTableInDB(DBPath, table):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM sqlite_master WHERE (type, name) = (\"table\", \"" + table + "\")"
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

def check_presence_inConnectionTables(DBPath, tables, keyName, keyValue):
    try:
        result = True
        for table in tables:
            if(check_presence_ofColumnInDB(DBPath, table, keyName)):
                result &= check_presence_inDB(DBPath, table, keyName, keyValue)
        
        return result               
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

def save_entry2DB(DBPath, table, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "INSERT INTO " + table 
        query += "(\"" + "\", \"".join(entryData.keys()) + "\")"
        query += " VALUES "
        values = []
        for value in entryData.values():
            if(isinstance(value, list)):
                value = str(value)
            if(value == None):
                value = "NULL"
            if(isinstance(value, bool)):
                value = str(int(value))
            values.append(value)
        query += "(\"" + "\", \"".join(values) + "\")"

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while saving data to DB: " + str(e))

def update_entry_inDB(DBPath, table, keyName, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "UPDATE " + table + " SET "
    
        keys = "(\"" + ("\", \"").join(list(entryData.keys()))+"\")"
        query += keys + " = "

        values = []
        for value in entryData.values():
            if(isinstance(value, list)):
                value = str(value)
            if(isinstance(value, bool)):
                value = str(int(value))
            if(value == None):
                value = "NULL"
            values.append(value)
        values = "(\"" + ("\", \"").join(values) + "\")"
        query += values

        query += " WHERE " + keyName + " = \"" + entryData[keyName] + "\""

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, str(e))

def delete_entry_fromDB(DBPath, table, keyNames, keyValues):
    try:
        if(not isinstance(keyNames, list)) : keyNames = [keyNames]
        if(not isinstance(keyValues, list)) : keyValues = [keyValues]

        conn = sq.connect(DBPath)

        keyNames = "(" + ", ".join(keyNames) + ")"
        keyValues = "(\"" + "\", \"".join(keyValues) + "\")"
        query = "DELETE FROM " + table + " WHERE " + keyNames + " = " + keyValues
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while deleting data from DB: " + str(e))

def nested_dict_pairs_iterator(dict_obj):
    ''' This function accepts a nested dictionary as argument
        and iterate over all values of nested dictionaries
    '''
    # Iterate over all key-value pairs of dict argument
    for key, value in dict_obj.items():
        # Check if value is of dict type
        if isinstance(value, dict):
            # If value is dict then iterate over all its values
            for pair in nested_dict_pairs_iterator(value):
                yield (key, *pair)
        else:
            # If value is not dict type then yield the value
            yield (key, value)

def fix_jsonString(string):
    string = string.encode('unicode_escape').decode()
    string = string.replace(r"\\", "")
    string = string.replace(r']"', r"]")
    string = string.replace(r'"[', r'[')
    string = string.replace(r"'", r'"')
    return string

def DBQuery_to_dict(DBPath, query):
    conn = sq.connect(DBPath)
    result = pd.read_sql_query(query, conn)
    conn.close()

    data = result.to_json(orient="records")
    data = json.loads(fix_jsonString(data))
    if (len(data) == 0):
        return [None]
    return data

def Ping(DBPath, table, KeyName, KeyValue):
    #TODO: get endpoints from DB and ping them
    return True