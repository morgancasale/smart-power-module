#bisogna decidere che tabelle usare per gli switch, ora ho creato delle tabelle di prova
#posso scrivere in modo più compatto ma devo fare la connessione ogni volta
import sqlite3 as sq
import json


def add_entryDB(DB, query, cursor, sqliteConnection):
    cursor.execute(query)
    sqliteConnection.commit()
    print("Record inserted")
    

conf=json.load(open('device.json'))
switches=conf["Data"]["Active"]["Switches"]
passive=conf["Data"]["Passive"]
module_ID=conf["deviceID"]

myTable1 = "switches_possible_config"
myTable2="realTimeData"

sqliteConnection = sq.connect("data.db")
cursor = sqliteConnection.cursor()
print("Connected to SQLite")
#query2= f"insert into {myTable2}(device_ID, Voltage, Current, Power, timestamp) values('{module_ID}', \
#      {passive['Voltage']}, {passive['Current']}, {passive['Power']}, '{passive['timestamp']}' )"
#add_entryDB('data.db', myTable2, keys2,values2)
for i in range(len(switches)):
    query1 = f"insert into {myTable1}(modulo_ID, switch_ID, switch_state) values('{module_ID}', {i+1}, {switches[i]})"
    add_entryDB('data.db', query1, cursor, sqliteConnection)

cursor.close()














    
    
    
    