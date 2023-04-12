from endPoint import *
from resourceClass import *
from utility import *
from deviceScheduling import *

from cherrypy import HTTPError

class HouseSettings:
    def __init__(self, settingsData, newSettings = True):
        self.settingsKeys = [
            "houseID", "houseName", "powerLimit"
        ]

        if(newSettings) : self.checkKeys(settingsData)
        self.checkSaveValues(settingsData)

    def checkKeys(self, settingsData):
        if(not all(key in self.settingsKeys for key in settingsData.keys())):
            raise HTTPError(status=400, message="Missing one or more keys")
        
    def checkSaveValues(self, settingsData):
        for key in settingsData.keys():
            match key:
                case ("houseID" | "houseName"):
                    if(not isinstance(settingsData[key], str)):
                        raise HTTPError(status=400, message="House settings' \"" + key + "\" value must be string")
                    match key:
                        case "houseID": self.houseID = settingsData["houseID"]
                        case "houseName": self.houseName = settingsData["houseName"]
                        
                case "powerLimit":
                    if(not isinstance(settingsData[key], (int, float)) or settingsData[key] < 0):
                        raise HTTPError(status=400, message="House settings' \"" + key + "\" value must be a positive number")
                    self.powerLimit = settingsData["powerLimit"]

    def to_dict(self):
        result = {}
        for key in self.settingsKeys:
            result[key] = getattr(self, key)
            
        return result
    
    def save2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Houses", "houseID", self.houseID)):
                raise HTTPError(status=400, message="House ID not found in DB")
            
            update_entry_inDB(DBPath, "HouseSettings", "houseID", self.to_dict())
            update_entry_inDB(DBPath, "Houses", "houseID", {"houseID": self.houseID, "HouseName": self.houseName})
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while saving house settings for house with ID \"" + self.houseID + "\" to the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=500, message="An error occurred while saving house settings for house with ID \"" + self.houseID + "\" to the DB:\n\t" + str(e))
        
    def updateDB(self, DBPath):
        self.save2DB(DBPath)
    
    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "HouseSettings", "houseID", params["houseID"])):
                raise HTTPError(status=400, message="Settings for this House not found in DB")
            
            delete_entry_fromDB(DBPath, "HouseSettings", "houseID", params["houseID"])
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while deleting house settings for house with ID \"" + params["houseID"] + "\" from the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=500, message="An error occurred while deleting house settings for house with ID \"" + params["houseID"] + "\" from the DB:\n\t" + str(e))
        
    def cleanDB(DBPath):
        query = "SELECT * FROM HouseSettings"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Houses", "houseID", entry["houseID"])):
                    HouseSettings.deleteFromDB(DBPath, {"houseID" : entry["houseID"]})
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while cleaning house settings from the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=500, message="An error occurred while cleaning house settings from the DB:\n\t" + str(e))
        
    def DB_to_dict(DBPath, house):
        try:
            houseID = house["houseID"]
            query = "SELECT * FROM HouseSettings WHERE houseID = \"" + houseID + "\""
            houseSettings = DBQuery_to_dict(DBPath, query)[0]

            return houseSettings
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while retrieving house settings for house with ID \"" + houseID + "\" from the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=500, message="An error occurred while retrieving house settings for house with ID \"" + houseID + "\" from the DB:\n\t" + str(e))