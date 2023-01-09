from utility import *
from device import *

import re

class User:
    def __init__(self, userData, newUser = False):
        self.userKeys = ["userID", "Name", "Surname", "Email"]

        if(newUser) : self.checkKeys(userData)
        self.checkSaveValues(userData)

        self.userData = userData

        if(newUser):
            self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def checkKeys(self, userData):
        if(not all(key in self.userKeys for key in userData.keys())):
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, userData):
        for key in userData.keys():
            match key:
                case ("userID" | "Name" | "Surname" | "Email"):
                    if(not isinstance(userData[key], str)):
                        raise web_exception(400, "User's \"" + key + "\"'s value must be a string")
                    match key:
                        case "userID":
                            self.userID = userData["userID"]
                        case "Name":
                            self.name = userData["Name"]
                        case "Surname":
                            self.surname = userData["Surname"]
                case "Email":
                    email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
                    if(re.match(email_pattern, userData["Email"]) == None): 
                        raise web_exception(400, userData["Email"] +" isn't a valid email address")
                    self.email = userData["Email"]
                case "deviceID":
                    if(not all(isinstance(deviceID, str) for deviceID in userData["deviceID"])):
                        raise web_exception(400, "User's \"deviceID\" value must be a list of strings")
                    self.deviceID = userData["deviceID"]


                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.userData.keys():
            result[key] = self.userData[key]

        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise web_exception(400, "A user with ID \"" + self.userID + "\" already exists in the database")
            
            if("deviceID" in self.userData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID)):
                        raise web_exception(400, "A device with ID \"" + deviceID + "\" does not exist in the database")

                    self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    save_entry2DB(DBPath, "UserDevice_conn", {"userID": self.userID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Users", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving user with ID \"" + self.userID + "\" to the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving user with ID \"" + self.userID + "\" to the DB: " + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise web_exception(400, "A user with ID \"" + self.userID + "\" does not exist in the database")
            
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "Users", "userID", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating user with ID \"" + self.userID + "\" in the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating user with ID \"" + self.userID + "\" in the DB: " + str(e))

    def deleteFromDB(DBPath, params):
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
            
        return None

    def DB_to_dict(DBPath, user):
        try:
            userID = user["userID"]
            userData = {"userID": userID, "Name": user["Name"], "Surname": user["Surname"], "Email": user["Email"], "Devices": []}

            if(check_presence_inDB(DBPath, "UserDevice_conn", "userID", userID)):
                query = "SELECT * FROM UserDevice_conn WHERE userID = \"" + userID + "\""
                users = DBQuery_to_dict(DBPath, query)
                
                usersIDs = "(\"" + "\", \"".join([user["deviceID"] for user in users]) + "\")"
                query = "SELECT * FROM Devices WHERE deviceID in " + usersIDs
                devices = DBQuery_to_dict(DBPath, query)

            for device in devices:
                userData["Devices"].append(Device.DB_to_dict(DBPath, device))

            return userData
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving user with ID \"" + userID + "\" from the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving user with ID \"" + userID + "\" from the DB: " + str(e))
