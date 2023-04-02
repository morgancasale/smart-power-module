from utility import *

class EndPoint:
    def __init__(self, endPointData, newEndPoint = False):
        self.endPointKeys = ["endPointID", "endPointName", "commProtocol", "IPAddress", "RESTPort", "MQTTPort", "MQTTTopics"]
        self.connTables = ["DeviceEndP_conn"]
        

        if(newEndPoint) : self.checkKeys(endPointData)
        self.checkSaveValues(endPointData)

        self.endPointData = endPointData

        if(newEndPoint):
            self.Online = self.Ping()
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")


    def to_dict(self):
        result = {}

        for key in self.endPointData.keys():
            if(key in self.endPointKeys): #TODO forse inutile
                result[key] = self.endPointData[key]

        result["Online"] = self.Online
        result["lastUpdate"] = self.lastUpdate

        return result

    def checkKeys(self, endPointData):
        if(not all(key in self.endPointKeys for key in endPointData.keys())):
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, endPointData):
        for key in endPointData.keys():
            match key:
                case ("endPointID" | "endPointName"):
                    if(not isinstance(endPointData[key], str)):
                        raise web_exception(400, "End-point's \"" + key + "\" value must be string")
                    match key:
                        case "endPointID":
                            self.endPointID = endPointData["endPointID"]
                        case "endPointName":
                            self.endPointName = endPointData["endPointName"]
                case "commProtocol":
                    if(not("MQTT" in endPointData[key] or "REST" in endPointData[key])):
                        raise web_exception(400, "\"commProtocol\" must be MQTT and/or REST")

                    if(not all(isinstance(prtcl, str) for prtcl in endPointData[key])):
                        raise web_exception(400, "\"commProtocol\" value must be a list of strings")

                    if("REST" in endPointData[key] and endPointData["IPAddress"] == None):
                        raise web_exception(400, "\"IPAddress\" must not be null if commProtocol is REST")
                    if("REST" in endPointData[key] and not("MQTT" in endPointData[key]) and endPointData["MQTTTopics"] != None):
                        raise web_exception(400, "\"MQTTTopics\" must be null if commProtocol is REST")

                    if("MQTT" in endPointData[key] and endPointData["MQTTTopics"] == None):
                        raise web_exception(400, "\"MQTTTopics\" parameter must not be null if commProtocol is MQTT")
                    if("MQTT" in endPointData[key] and not("REST" in endPointData[key]) and endPointData["IPAddress"] != None):
                        raise web_exception(400, "\"IPAddress\" must be null if commProtocol is MQTT")
                    
                    if(not isinstance(endPointData["commProtocol"], list)) : endPointData["commProtocol"] = [endPointData["commProtocol"]]
                    self.commProtocol = endPointData["commProtocol"]
                case "IPAddress":
                    if(endPointData[key] != None and not isinstance(endPointData[key], str)): # TODO Check if IP address is valid
                        raise web_exception(400, "\"IPAddress\" value must be string")
                    self.IPAddress = endPointData["IPAddress"]
                case "RESTPort":
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)): # TODO Check if port is valid
                        raise web_exception(400, "\"RESTPort\" value must be integer")
                    
                    if(endPointData[key] == None and "REST" in endPointData["commProtocol"]):
                        raise web_exception(400, "\"RESTPort\" must not be null if commProtocol is REST")
                    if(endPointData[key] != None and not "REST" in endPointData["commProtocol"]):
                        raise web_exception(400, "\"RESTPort\" must be null if commProtocol is not REST")
                    
                    if(endPointData["MQTTPort"] == endPointData[key]):
                        raise web_exception(400, "\"RESTPort\" and \"MQTTPort\" must be different")
                case "MQTTPort":
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)): # TODO Check if port is valid
                        raise web_exception(400, "\"MQTTPort\" value must be integer")
                    
                    if(endPointData[key] == None and "MQTT" in endPointData["commProtocol"]):
                        raise web_exception(400, "\"MQTTPort\" must not be null if commProtocol is MQTT")
                    if(endPointData[key] != None and not "MQTT" in endPointData["commProtocol"]):
                        raise web_exception(400, "\"MQTTPort\" must be null if commProtocol is not MQTT")
                    
                    if(endPointData["RESTPort"] == endPointData[key]):
                        raise web_exception(400, "\"RESTPort\" and \"MQTTPort\" must be different")
                case "MQTTTopics":
                    cond = endPointData[key] != None and len(endPointData[key]) == 0
                    cond &= not all(isinstance(topic, str) for topic in endPointData[key])
                    if(cond): 
                        raise web_exception(400, "\"MQTTTopics\" must be a list of strings not empty")
                    
                    if(not isinstance(endPointData["MQTTTopics"], list)) : endPointData["MQTTTopics"] = [endPointData["MQTTTopics"]]
                    self.MQTTTopics = endPointData["MQTTTopics"]
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")

    def check_consistency_inDB(self, DBPath):
        try:
            query = "SELECT * FROM endPoints WHERE endPointID = \"" + self.endPointID + "\""
            data = DBQuery_to_dict(DBPath, query)[0]
            try:
                data["MQTTTopics"] = json.loads(data["MQTTTopics"].replace("'", "\""))
            except:
                pass

            if(not(isinstance(data["MQTTTopics"], list))):
                data["MQTTTopics"] = [data["MQTTTopics"]]
            
            result = True
            if(not all(prtc in data["commProtocol"] for prtc in self.commProtocol)):  
                result = False
            if(data["IPAddress"] != self.IPAddress):
                result = False
            if(not all(topic in data["MQTTTopics"] for topic in self.MQTTTopics)):
                result = False
                
            return result
        except web_exception as e:
            raise web_exception(400, "An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database:\n\t" + str(e))

    def save2DB(self, DBPath): # TODO Check if all error cases are covered
        try:
            if(check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                if(not self.check_consistency_inDB(DBPath)):
                    raise web_exception(400, "An end-point with ID \"" + self.endPointID + "\" already exists in the database with different parameters")

                if(self.IPAddress != None and check_presence_inConnectionTables(DBPath, self.connTables, "endPointID", self.endPointID)):
                    raise web_exception(400, "An end-point with ID \"" + self.endPointID + "\" is already used in another connection")
            else:
                if(self.IPAddress != None and check_presence_inDB(DBPath, "endPoints", "IPAddress", self.IPAddress)):
                    raise web_exception(400, "IP Address \"" + self.IPAddress + "\" is already used by another end-point")
                self.Online = self.Ping()
                save_entry2DB(DBPath, "endPoints", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB:\n\t" + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB:\n\t" + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "endPoints", "endPointID", self.endPointID)):
                raise web_exception(400, "End-point with ID \"" + self.endPointID + "\" not found in the database")

            if("IPAddress" in self.endPointData.keys() and check_presence_inDB(DBPath, "endPoints", "IPAddress", self.IPAddress)):
                raise web_exception(400, "IP Address \"" + self.IPAddress + "\" is already used by another end-point")

            self.Online = self.Ping()
            self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_entry_inDB(DBPath, "endPoints", "endPointID", self.to_dict())

            entry = {
                "endPointID": self.endPointID, "lastUpdate": self.lastUpdate
            }
            update_entry_inDB(DBPath, "DeviceEndP_conn", "endPointID", entry)
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating end-point with ID \"" + self.endPointID + "\" in the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating end-point with ID \"" + self.endPointID + "\" in the DB:\n\t" + str(e))

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving endPoint with ID \"" + self.deviceID + "\" to the DB:\n\t" + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving endPoint with ID \"" + self.deviceID + "\" to the DB:\n\t" + str(e))
    
    def DB_to_dict(DBPath, EP):
        try:
            query = "SELECT * FROM EndPoints WHERE endPointID = \"" + EP["endPointID"] + "\""
            data = DBQuery_to_dict(DBPath, query)[0]
            data["Online"] = bool(data["Online"])
            return data
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving end-point with ID \"" + EP["endPointID"] + "\" from the DB:\n\t" + str(e))

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["DeviceEndP_conn"]

        query = "SELECT * FROM EndPoints"
        data = DBQuery_to_dict(DBPath, query)
        
        if(not isinstance(data, list)) : data = [data]

        for entry in data:
            if(not check_presence_inConnectionTables(DBPath, connTables, "endPointID", entry["endPointID"])):
                delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])

    def deleteFromDB(DBPath, entry):
        try:
            if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])):
                raise web_exception(400, "End-point with ID \"" + entry["endPointID"] + "\" not found in the database")

            delete_entry_fromDB(DBPath, "DeviceEndP_conn", "endPointID", entry["endPointID"])
            delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting end-point with ID \"" + entry["endPointID"] + "\" from the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting end-point with ID \"" + entry["endPointID"] + "\" from the DB:\n\t" + str(e))
        
        return True

    def setOnlineStatus(newEPIDs):
        allEPIDs = getIDs_fromDB(DBPath, "EndPoints", "endPointID")

        missingEPIDs = list(set(allEPIDs) - set(newEPIDs))

        entry = {"endPointID": missingEPIDs, "Online": False, "lastUpdate": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

        update_entry_inDB(DBPath, "EndPoints", "endPointID", entry)

    def Ping(self):
        #TODO check devices that use this endpoint, ping them and return True if at least one is online
        return True