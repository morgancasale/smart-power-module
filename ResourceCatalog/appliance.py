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
            raise HTTPError(status=400, message="Missing one or more keys")
        
    def checkSaveValues(self, applianceData):
        for key in applianceData.keys():
            match key:
                case "applianceType":
                    if(not isinstance(applianceData[key], str)):
                        raise HTTPError(status=400, message="Appliance settings' \"" + key + "\" value must be string")
                    self.applianceType = applianceData["applianceType"]
                case ("maxPower" | "standyPowerMax" | "functioningRangeMin" | "functioningRangeMax"):
                    if(not isinstance(applianceData[key], (int, float)) or applianceData[key] < 0):
                        raise HTTPError(status=400, message="Appliance settings' \"" + key + "\" value must be a positive number")
                    self.maxPower = applianceData[key]
                
                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")
                
    def to_dict(self):
        result = {}
        for key in self.applianceKeys:
            result[key] = getattr(self, key)
        
        return result
    
    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                raise HTTPError(status=400, message="Appliance \"" + self.applianceType + "\" already exists in DB")
            
            save_entry2DB(DBPath, "AppliancesInfo", self.to_dict())
        
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + str(e))
    
    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                raise HTTPError(status=400, message="Appliance \"" + self.applianceType + "\" does not exist in DB")
            
            update_entry_inDB(DBPath, "AppliancesInfo", "applianceType", self.to_dict())
        
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while updating the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while updating the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + str(e))
    
    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", self.applianceType)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while setting the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while setting the appliance \"" + self.applianceType + "\" in DB: \u0085\u0009" + str(e))
    
    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "AppliancesInfo", "applianceType", params["applianceType"])):
                raise HTTPError(status=400, message="Appliance \"" + params["applianceType"] + "\" does not exist in DB")
            
            delete_entry_fromDB(DBPath, "AppliancesInfo", params["applianceType"])
        
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while deleting the appliance \"" + params["applianceType"] + "\" from DB: \u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while deleting the appliance \"" + params["applianceType"] + "\" from DB: \u0085\u0009" + str(e))

    def DB_to_dict(DBPath, appliance):
        try:
            query = "SELECT * FROM AppliancesInfo WHERE applianceType = \"" + appliance["applianceType"] + "\""
            applianceData = DBQuery_to_dict(DBPath, query)
        
            return applianceData
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while retrieving the appliance \"" + appliance["applianceType"] + "\" from DB: \u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while retrieving the appliance \"" + appliance["applianceType"] + "\" from DB: \u0085\u0009" + str(e))