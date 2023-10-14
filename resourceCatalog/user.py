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
            self.lastUpdate = time.time()
    
    def checkKeys(self, userData):
        if(not all(key in self.userKeys for key in userData.keys())):
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")

    def checkSaveValues(self, userData):
        for key in userData.keys():
            match key:
                case ("userID" | "Name" | "Surname" | "Email"):
                    if(not isinstance(userData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="User's \"" + key + "\"'s value must be a string")
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
                        raise Client_Error_Handler.BadRequest(message=userData["Email"] +" isn't a valid email address")
                    self.email = userData["Email"]
                case "deviceID":
                    if(not all(isinstance(deviceID, str) for deviceID in userData["deviceID"])):
                        raise Client_Error_Handler.BadRequest(message="User's \"deviceID\" value must be a list of strings")
                    self.deviceID = userData["deviceID"]


                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.userData.keys():
            result[key] = self.userData[key]

        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise Client_Error_Handler.BadRequest(message="A user with ID \"" + self.userID + "\" already exists in the database")
            
            if("deviceID" in self.userData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID)):
                        raise Client_Error_Handler.NotFound(message="A device with ID \"" + deviceID + "\" does not exist in the database")

                    self.lastUpdate = time.time()
                    save_entry2DB(DBPath, "UserDevice_conn", {"userID": self.userID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Users", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving user with ID \"" + 
                self.userID + "\" to the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving user with ID \"" + 
                self.userID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def updateDB(self, DBPath):
        deviceIDs = []
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise Client_Error_Handler.BadRequest(message="A user with ID \"" + self.userID + "\" does not exist in the database")
            
            self.lastUpdate = time.time()

            if("deviceID" in self.userData.keys()):
                data = {"table": "UserDevice_conn", "refID": "userID", "connID": "deviceID", "refValue": self.userID, "connValues": self.deviceID}
                updateConnTable(DBPath, data)
            
            update_entry_inDB(DBPath, "Users", "userID", self.to_dict())
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while updating user with ID \"" + self.userID + "\" in the DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while updating user with ID \"" + 
                self.userID + "\" in the DB:\u0085\u0009" + str(e)
            )

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", params["userID"])):
                raise HTTPError(status=400, message="A user with ID \"" + params["userID"] + "\" does not exist in the database")

            delete_entry_fromDB(DBPath, "UserDevice_conn", "userID", params["userID"])
            Device.cleanDB(DBPath)
            delete_entry_fromDB(DBPath, "Users", "userID", params["userID"])
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while deleting user with ID \"" + 
                params["userID"] + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while deleting user with ID \"" + 
                params["userID"] + "\" from the DB:\u0085\u0009" + str(e)
            )
            
        return True

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving user with ID \"" + 
                self.userID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving user with ID \"" + 
                self.userID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def DB_to_dict(DBPath, user, verbose = True):
        try:
            userID = user["userID"]
            userData = {"userID": userID, "Name": user["Name"], "Surname": user["Surname"], "Email": user["Email"]}

            userData["Devices"] = []
            if(check_presence_inDB(DBPath, "UserDevice_conn", "userID", userID)):
                query = "SELECT * FROM UserDevice_conn WHERE userID = \"" + userID + "\""
                user_dev_conns = DBQuery_to_dict(DBPath, query)
                
                devicesIDs = "(\"" + "\", \"".join([user_dev_conn["deviceID"] for user_dev_conn in user_dev_conns]) + "\")"
                query = "SELECT * FROM Devices WHERE deviceID in " + devicesIDs
                devices = DBQuery_to_dict(DBPath, query)

            for device in devices:
                if(verbose):
                    userData["Devices"].append(Device.DB_to_dict(DBPath, device))
                else:
                    userData["Devices"].append(device["deviceID"])

            return userData
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while retrieving user with ID \"" + 
                userID + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while retrieving user with ID \"" +
                userID + "\" from the DB:\u0085\u0009" + str(e)
            )