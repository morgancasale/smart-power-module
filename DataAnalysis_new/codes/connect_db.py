import sqlite3 
from sqlite3 import Error

class Connect():
    def __init__(self,DBPath):
         self.DBPath = DBPath
    
    def create_connection(self):
        conn = None
    
        try:
            conn = sqlite3.connect(self.DBPath)
        except Error as err:
            print(err)

        return conn