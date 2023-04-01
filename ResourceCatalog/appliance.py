from utility import *

class Appliance:
    def __init__(self, applianceData, newAppliance = False):
        self.applianceKeys = [
            "applianceType", "maxPower", "standyPowerMax", 
            "functioningRangeMin", "functioningRangeMax"
        ]

        if(newAppliance) : self.checkKeys(applianceData)
        self.checkSaveValues(applianceData)

    def checkKeys(self, applianceData):
        if(not all(key in self.applianceKeys for key in applianceData.keys())):
            raise web_exception(400, "Missing one or more keys")
        
    def checkSaveValues(self, applianceData):
        for key in applianceData.keys():
            match key:
                case "applianceType":
                    if(not isinstance(applianceData[key], str)):
                        raise web_exception(400, "Appliance settings' \"" + key + "\" value must be string")
                    self.applianceType = applianceData["applianceType"]
                case ("maxPower" | "standyPowerMax" | "functioningRangeMin" | "functioningRangeMax"):
                    if(not isinstance(applianceData[key], (int, float)) or applianceData[key] < 0):
                        raise web_exception(400, "Appliance settings' \"" + key + "\" value must be a positive number")
                    self.maxPower = applianceData[key]
                
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
                
    def to_dict(self):
        result = {}
        for key in self.applianceKeys:
            result[key] = getattr(self, key)
        
        return result
    
    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                raise web_exception(400, "Appliance \"" + self.applianceType + "\" already exists in DB")
            
            save_entry2DB(DBPath, "AppliancesInfo", self.to_dict())
        
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving the appliance \"" + self.applianceType + "\" in DB: \n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving the appliance \"" + self.applianceType + "\" in DB: \n\t" + str(e))
    
    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                raise web_exception(400, "Appliance \"" + self.applianceType + "\" does not exist in DB")
            
            update_entry_inDB(DBPath, "AppliancesInfo", "applianceType", self.to_dict())
        
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating the appliance \"" + self.applianceType + "\" in DB: \n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating the appliance \"" + self.applianceType + "\" in DB: \n\t" + str(e))
    
    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        
        except web_exception as e:
            raise web_exception(400, "An error occurred while setting the appliance \"" + self.applianceType + "\" in DB: \n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while setting the appliance \"" + self.applianceType + "\" in DB: \n\t" + str(e))
    
    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", params["applianceType"])):
                raise web_exception(400, "Appliance \"" + params["applianceType"] + "\" does not exist in DB")
            
            delete_entry_fromDB(DBPath, "AppliancesInfo", params["applianceType"])
        
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting the appliance \"" + params["applianceType"] + "\" from DB: \n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting the appliance \"" + params["applianceType"] + "\" from DB: \n\t" + str(e))

    def DB_to_dict(DBPath, appliance):
        try:
            query = "SELECT * FROM AppliancesInfo WHERE applianceType = \"" + appliance["applianceType"] + "\""
            applianceData = DBQuery_to_dict(DBPath, query)
        
            return applianceData
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving the appliance \"" + appliance["applianceType"] + "\" from DB: \n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving the appliance \"" + appliance["applianceType"] + "\" from DB: \n\t" + str(e))