from utility import *
from user import *

class House:
    def __init__(self, houseData, newHouse = False):
        self.houseKeys = ["houseID", "Name"]
        self.connTables = ["HouseUser_conn", "HouseDev_conn"]

        if(newHouse) : self.checkKeys(houseData)
        self.checkSaveValues(houseData)

        self.houseData = houseData

        if(newHouse):
            self.lastUpdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def checkKeys(self, houseData):
        if(not all(key in houseData.keys() for key in self.houseKeys)):
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, houseData):
        for key in houseData.keys():
            match key:
                case ("houseID" | "Name"):
                    if(not isinstance(houseData[key], str)):
                        raise web_exception(400, "Home's \"" + key + "\" parameter must be a string")
                    match key:
                        case "houseID":
                            self.houseID = houseData["houseID"]
                        case "Name":
                            self.name = houseData["Name"]
                case "userID":
                    if(not all(isinstance(deviceID, str) for deviceID in houseData["houseID"])):
                        raise web_exception(400, "House's \"userID\" parameter must be a list of strings")
                    self.userID = houseData["userID"]
                case "deviceID":
                    if(not all(isinstance(deviceID, str) for deviceID in houseData["deviceID"])):
                        raise web_exception(400, "House's \"deviceID\" parameter must be a list of strings")
                    self.deviceID = houseData["deviceID"]

                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.houseData.keys():
            match key:
                case ("houseID" | "Name"):
                    result[key] = self.houseData[key]

        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Houses", "houseID", self.houseID)):
                raise web_exception(400, "An house with ID \"" + self.houseID + "\" already exists in the database")
            
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            if("userID" in self.houseData.keys()):
                for userID in self.userID:
                    if(not check_presence_inDB(DBPath, "Users", "userID", userID)):
                        raise web_exception(400, "An user with ID \"" + userID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[0], {"houseID": self.houseID, "userID": userID, "lastUpdate": self.lastUpdate})

            if("deviceID" in self.houseData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID)):
                        raise web_exception(400, "A device with ID \"" + deviceID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[1], {"houseID": self.houseID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Houses", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving house with ID \"" + self.houseID + "\" to the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving house with ID \"" + self.houseID + "\" to the DB: " + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Houses", "houseID", self.userID)):
                raise web_exception(400, "An house with ID \"" + self.userID + "\" does not exist in the database")
            
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "Houses", "houseID", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating house with ID \"" + self.houseID + "\" in the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating house with ID \"" + self.houseID + "\" in the DB: " + str(e))

    def deleteFromDB(DBPath, params):
        try:
            connTables = ["HouseUser_conn", "HouseDev_conn"]
            if(not check_presence_inDB(DBPath, "Houses", "houseID", params["houseID"])):
                raise web_exception(400, "An house with ID \"" + params["houseID"] + "\" does not exist in the database")

            for connTable in connTables:
                delete_entry_fromDB(DBPath, connTable, "houseID", params["houseID"])
            Device.cleanDB(DBPath)

            delete_entry_fromDB(DBPath, "Houses", "houseID", params["houseID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting house with ID \"" + params["houseID"] + "\" from the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting house with ID \"" + params["houseID"] + "\" from the DB: " + str(e))

    def DB_to_dict(DBPath, house):
        try:
            connTables = ["HouseUser_conn", "HouseDev_conn"]
            tablesNames = ["Users", "Devices"]
            varsIDs = ["userID", "deviceID"]
            houseID = house["houseID"]
            houseData = {"houseID": houseID, "Name": house["Name"], "users": [], "Devices": []}

            for i in range(len(connTables)):
                if(check_presence_inDB(DBPath, connTables[i], "houseID", houseID)):
                    query = "SELECT * FROM " + "HouseUser_conn" + " WHERE houseID = \"" + houseID + "\""
                    houses = DBQuery_to_dict(DBPath, query)
                    
                    housesIDs = "(\"" + "\", \"".join([house["houseID"] for house in houses]) + "\")"
                    query = "SELECT * FROM " + tablesNames[i] + " WHERE " + varsIDs[i] + " in " + housesIDs
                    results = DBQuery_to_dict(DBPath, query)

                    for result in results:
                        if(i == 0):
                            houseData["Users"].append(User.DB_to_dict(DBPath, result))
                        else:
                            houseData["Devices"].append(Device.DB_to_dict(DBPath, result))

            return houseData
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving house with ID \"" + houseID + "\" from the DB: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving house with ID \"" + houseID + "\" from the DB: " + str(e))