from utility import *
from user import *

from cherrypy import HTTPError

class House:
    def __init__(self, houseData, newHouse = False):
        self.houseKeys = ["houseID", "houseName"]
        self.connTables = ["HouseUser_conn", "HouseDev_conn"]

        if(newHouse) : self.checkKeys(houseData)
        self.checkSaveValues(houseData)

        self.houseData = houseData

        if(newHouse):
            self.lastUpdate = time.time()
    
    def checkKeys(self, houseData):
        if(not all(key in houseData.keys() for key in self.houseKeys)):
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")

    def checkSaveValues(self, houseData):
        for key in houseData.keys():
            match key:
                case ("houseID" | "houseName"):
                    if(not isinstance(houseData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Home's \"" + key + "\" parameter must be a string")
                    match key:
                        case "houseID":
                            self.houseID = houseData["houseID"]
                        case "houseName":
                            self.name = houseData["houseName"]
                case "userID":
                    if(not all(isinstance(deviceID, str) for deviceID in houseData["houseID"])):
                        raise Client_Error_Handler.BadRequest(message="House's \"userID\" parameter must be a list of strings")
                    self.userID = houseData["userID"]
                case "deviceID":
                    if(not all(isinstance(deviceID, str) for deviceID in houseData["deviceID"])):
                        raise Client_Error_Handler.BadRequest(message="House's \"deviceID\" parameter must be a list of strings")
                    self.deviceID = houseData["deviceID"]

                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.houseData.keys():
            match key:
                case ("houseID" | "houseName"):
                    result[key] = self.houseData[key]

        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Houses", "houseID", self.houseID)):
                raise Client_Error_Handler.BadRequest(message="An house with ID \"" + self.houseID + "\" already exists in the database")
            
            self.lastUpdate = time.time()

            if("userID" in self.houseData.keys()):
                for userID in self.userID:
                    if(not check_presence_inDB(DBPath, "Users", "userID", userID)):
                        raise Client_Error_Handler.NotFound(message="An user with ID \"" + userID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[0], {"houseID": self.houseID, "userID": userID, "lastUpdate": self.lastUpdate})

            if("deviceID" in self.houseData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID, False)):
                        raise Client_Error_Handler.NotFound(message="A device with ID \"" + deviceID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[1], {"houseID": self.houseID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Houses", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving house with ID \"" + 
                self.houseID + "\" to the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving house with ID \"" + 
                self.houseID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Houses", "houseID", self.houseID)):
                raise Client_Error_Handler.NotFound(message="An house with ID \"" + self.houseID + "\" does not exist in the database")
            
            self.lastUpdate = time.time()
            
            update_entry_inDB(DBPath, "Houses", "houseID", self.to_dict())

            if("userID" in self.houseData.keys()):
                data = {"table" : self.connTables[0], "refID" : "houseID", "connID" : "userID", "refValue" : self.houseID, "connValues" : self.userID}
                updateConnTable(DBPath, data)
            
            if("deviceID" in self.houseData.keys()):
                data = {"table" : self.connTables[1], "refID" : "houseID", "connID" : "deviceID", "refValue" : self.houseID, "connValues" : self.deviceID}
                updateConnTable(DBPath, data)
                
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while updating house with ID \"" + 
                self.houseID + "\" in the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while updating house with ID \"" + 
                self.houseID + "\" in the DB:\u0085\u0009" + str(e)
            )

    def deleteFromDB(DBPath, params):
        try:
            connTables = ["HouseUser_conn", "HouseDev_conn"]
            if(not check_presence_inDB(DBPath, "Houses", "houseID", params["houseID"])):
                raise Client_Error_Handler.NotFound(message="An house with ID \"" + params["houseID"] + "\" does not exist in the database")

            for connTable in connTables:
                delete_entry_fromDB(DBPath, connTable, "houseID", params["houseID"])
            Device.cleanDB(DBPath)

            delete_entry_fromDB(DBPath, "Houses", "houseID", params["houseID"])
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while deleting house with ID \"" + 
                params["houseID"] + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while deleting house with ID \"" + 
                params["houseID"] + "\" from the DB:\u0085\u0009" + str(e)
            )
        
        return True

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Houses", "houseID", self.houseID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving house with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving house with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def DB_to_dict(DBPath, house, verbose = True):
        try:
            connTables = ["HouseUser_conn", "HouseDev_conn"]
            tableshouseNames = ["Users", "Devices"]
            varsIDs = ["userID", "deviceID"]

            houseID = house["houseID"]
            houseData = {"houseID": houseID, "houseName": house["houseName"], "Users": [], "Devices": []}

            for i in range(len(connTables)):
                if(check_presence_inDB(DBPath, connTables[i], "houseID", houseID)):
                    query = "SELECT * FROM " + connTables[i] + " WHERE houseID = \"" + houseID + "\""
                    house_entry_conns = DBQuery_to_dict(DBPath, query)
                    
                    entryIDs = "(\"" + "\", \"".join([house_entry_conn[varsIDs[i]] for house_entry_conn in house_entry_conns]) + "\")"
                    query = "SELECT * FROM " + tableshouseNames[i] + " WHERE " + varsIDs[i] + " in " + entryIDs
                    results = DBQuery_to_dict(DBPath, query)

                    for result in results:
                        if(i == 0):
                            if(verbose):
                                houseData["Users"].append(User.DB_to_dict(DBPath, result, verbose = False))
                            else:
                                houseData["Users"].append(result["userID"])
                        else:
                            if(verbose):
                                houseData["Devices"].append(Device.DB_to_dict(DBPath, result, verbose = False))
                            else:
                                houseData["Devices"].append(result["deviceID"])

            return houseData
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while retrieving house with ID \"" + 
                houseID + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while retrieving house with ID \"" +
                houseID + "\" from the DB:\u0085\u0009" + str(e)
            )