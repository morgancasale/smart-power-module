from utility import *
from device import *

import re

class User:
    def __init__(self, userData, newUser = False):
        self.userKeys = ["userID", "Name", "Surname", "Email"]

        if(newUser) : self.checkKeys(userData)
        self.checkValues(userData)

        self.userID = userData["userID"]
        self.name = userData["Name"]
        self.surname = userData["Surname"]
        self.email = userData["Email"]
    
    def checkKeys(self, userData):
        if(not all(key in self.userKeys for key in userData.keys())):
            raise web_exception(400, "Missing one or more keys")

    def checkValues(self, userData):
        for key in userData.keys():
            match key:
                case ("userID" | "Name" | "Surname" | "Email"):
                    if(not isinstance(userData[key], str)):
                        raise web_exception(400, "User's \"" + key + "\" value must be string")
                case "Email":
                    email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
                    if(re.match(email_pattern, userData["Email"]) == None): 
                        raise web_exception(400, userData["Email"] +" isn't a valid email address")
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        return {"userID": self.userID, "Name": self.name,
                "Surname": self.surname, "Email": self.email}

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise web_exception(400, "A user with ID \"" + self.userID + "\" already exists in the database")
            
            save_entry2DB(DBPath, "Users", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving user with ID \"" + self.userID + "\" to the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving user with ID \"" + self.userID + "\" to the DB: " + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise web_exception(400, "A user with ID \"" + self.userID + "\" does not exist in the database")
            
            update_entry_inDB(DBPath, "Users", "userID", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating user with ID \"" + self.userID + "\" in the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating user with ID \"" + self.userID + "\" in the DB: " + str(e))

    def deletefromDB(params, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", params["userID"])):
                raise web_exception(400, "A user with ID \"" + params["userID"] + "\" does not exist in the database")

            delete_entry_fromDB(DBPath, "UserDevice_conn", "userID", params["userID"])
            Device.cleanDB(DBPath)
            delete_entry_fromDB(DBPath, "Users", "userID", params["userID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting user with ID \"" + params["userID"] + "\" from the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting user with ID \"" + params["userID"] + "\" from the DB: " + str(e))

    def DB_to_dict(DBPath, user):
        try:
            userID = user["userID"]
            userData = {"userID": userID, "Name": user["Name"], "Surname": user["Surname"], "Email": user["Email"], "Devices": []}

            query = "SELECT * FROM UserDevice_conn WHERE userID = \"" + userID + "\""
            users = DBQuery_to_dict(DBPath, query)
            
            UsersIDs = "(\"" + "\", \"".join([user["deviceID"] for user in users]) + "\")"
            query = "SELECT * FROM Devices WHERE deviceID in " + UsersIDs
            devices = DBQuery_to_dict(DBPath, query)

            for device in devices:
                userData["Devices"].append(Device.DB_to_dict(DBPath, device))

            return userData
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving user with ID \"" + userID + "\" from the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving user with ID \"" + userID + "\" from the DB: " + str(e))
