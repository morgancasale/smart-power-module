from utility import *

class EndPoint:
    def __init__(self, endPointData, newEndPoint = False):
        self.endPointKeys = ["endPointID", "endPointName", "protocols", "IPAddress", "port", "clientID", "CRUDMethods", "MQTTTopics", "QOS"]
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
            result[key] = self.endPointData[key]

        result["Online"] = self.Online
        result["lastUpdate"] = self.lastUpdate

        return result

    def checkKeys(self, endPointData):
        if(not all(key in self.endPointKeys for key in endPointData.keys())):
            raise HTTPError(status=400, message="Missing one or more keys")

    def checkSaveValues(self, endPointData):
        for key in endPointData.keys():
            match key:
                case ("endPointID" | "endPointName"):
                    if(not isinstance(endPointData[key], str)):
                        raise HTTPError(status=400, message="End-point's \"" + key + "\" value must be string")
                    match key:
                        case "endPointID":
                            self.endPointID = endPointData["endPointID"]
                        case "endPointName":
                            self.endPointName = endPointData["endPointName"]

                case "protocols":
                    if(not("MQTT" in endPointData[key] or "REST" in endPointData[key])):
                        raise HTTPError(status=400, message="\"protocols\" must be MQTT and/or REST")

                    if(not all(isinstance(prtcl, str) for prtcl in endPointData[key])):
                        raise HTTPError(status=400, message="\"protocols\" value must be a list of strings")

                    if("REST" in endPointData[key] and endPointData["IPAddress"] == None):
                        raise HTTPError(status=400, message="\"IPAddress\" must not be null if protocols is REST")
                    if("REST" in endPointData[key] and not("MQTT" in endPointData[key]) and endPointData["MQTTTopics"] != None):
                        raise HTTPError(status=400, message="\"MQTTTopics\" must be null if protocols is REST")

                    if("MQTT" in endPointData[key] and endPointData["MQTTTopics"] == None):
                        raise HTTPError(status=400, message="\"MQTTTopics\" parameter must not be null if protocols is MQTT")
                    
                    cond = "MQTT" in endPointData[key] and not("REST" in endPointData[key])
                    cond &= "IPAddress" in endPointData.keys() and endPointData["IPAddress"] != None
                    if(cond):
                        raise HTTPError(status=400, message="\"IPAddress\" must be null if protocols is MQTT")
                    
                    if(not isinstance(endPointData["protocols"], list)) : endPointData["protocols"] = [endPointData["protocols"]]
                    self.protocols = endPointData["protocols"]

                case "IPAddress":
                    if(endPointData[key] != None and not isinstance(endPointData[key], str)): # TODO Check if IP address is valid
                        raise HTTPError(status=400, message="\"IPAddress\" value must be string")
                    self.IPAddress = endPointData["IPAddress"]

                case ("port"):
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)): # TODO Check if port is valid
                        raise HTTPError(status=400, message="\"" + key + "\" value must be integer")
                    self.port = endPointData["port"]

                case "QOS":
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)):
                        raise HTTPError(status=400, message="\"" + key + "\" value must be integer")
                    if(endPointData[key] != None and not (endPointData[key] in [0,1,2])):
                        raise HTTPError(status=400, message="\"" + key + "\" value must be 0, 1 or 2")
                    self.QOS = endPointData[key]

                case "clientID":
                    if(not("MQTT" in endPointData["protocols"]) and endPointData[key] == None):
                        raise HTTPError(status=400, message="\"clientID\" must not be null if protocols is MQTT")
                    if(not isinstance(endPointData[key], str)):
                        raise HTTPError(status=400, message="\"clientID\" value must be string")
                    self.clientID = endPointData["clientID"]

                case "CRUDMethods":
                    methods = endPointData[key]
                    if(not isinstance(methods, list)):
                        raise HTTPError(status=400, message="\"CRUDMethods\" value must be a list")
                    if(not all(isinstance(method, str) for method in methods)):
                        raise HTTPError(status=400, message="\"CRUDMethods\" value must be a list of strings")
                    if(not all(method in ["GET", "POST", "PUT", "DELETE", "PATCH"] for method in methods)):
                        raise HTTPError(status=400, message="Unexpected method in \"" + key +"\".")

                case "MQTTTopics":
                    topics = endPointData[key]
                    if(not isinstance(topics, dict)):
                        raise HTTPError(status=400, message="\"" + key + "\" must be a dictionary")
                    if(not all(key in ["pub", "sub"] for key in topics.keys())):
                        raise HTTPError(status=400, message="\"" + key + "\" must have parameters \"pub\" and \"sub\"")
                    
                    if(topics["sub"] != None and not isinstance(topics["sub"], list)):
                        raise HTTPError(status=400, message="Subscription \"" + key + "\" must be a list")
                    if(topics["sub"] != None and not all(isinstance(topic, str) for topic in topics["sub"])):
                        raise HTTPError(status=400, message="Subscription \"" + key + "\" must be a list of strings")
                    
                    if(topics["pub"] != None and not isinstance(topics["pub"], list)):
                        raise HTTPError(status=400, message="Publication \"" + key + "\" must be a list")
                    if(topics["pub"] != None and not all(isinstance(topic, str) for topic in topics["pub"])):
                        raise HTTPError(status=400, message="Publication \"" + key + "\" must be a list of strings")
                    
                    self.MQTTTopics = endPointData[key]
                    
                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")

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
            if(not all(prtcl in data["protocols"] for prtcl in self.protocols)):  
                result = False
            if(data["IPAddress"] != self.IPAddress):
                result = False
            if(not all(topic in data["MQTTTopics"] for topic in self.MQTTTopics)):
                result = False
                
            return result
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database:\u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database:\u0085\u0009" + str(e))

    def save2DB(self, DBPath): # TODO Check if all error cases are covered
        try:
            if(check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                if(not self.check_consistency_inDB(DBPath)):
                    raise HTTPError(status=400, message="An end-point with ID \"" + self.endPointID + "\" already exists in the database with different parameters")

                if(self.IPAddress != None and check_presence_inConnectionTables(DBPath, self.connTables, "endPointID", self.endPointID)):
                    raise HTTPError(status=400, message="An end-point with ID \"" + self.endPointID + "\" is already used in another connection")
            else:
                foundEndPoints = []
                if("IPAddress" in self.endPointData.keys()):
                    foundEndPoints = DBQuery_to_dict(DBPath, "SELECT * FROM endPoints WHERE (\"IPAddress\", \"port\") = (\"" + self.IPAddress + "\", \"" + str(self.port) + "\")")
                if(len(foundEndPoints) > 0 and foundEndPoints[0] != None and foundEndPoints[0]["endPointID"] != self.endPointID):
                    raise HTTPError(status=400, message="IP Address \"" + self.IPAddress + "\" and port \"" + str(self.port) + "\" are already used by another end-point")
                self.Online = self.Ping()
                self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_entry2DB(DBPath, "endPoints", self.to_dict())
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB:\u0085\u0009" + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "endPoints", "endPointID", self.endPointID)):
                raise HTTPError(status=400, message="End-point with ID \"" + self.endPointID + "\" not found in the database")
            
            if("IPAddress" in self.endPointData.keys()):
                foundEndPoints = DBQuery_to_dict(DBPath, "SELECT * FROM endPoints WHERE (\"IPAddress\", \"port\") = (\"" + self.IPAddress + "\", \"" + str(self.port) + "\")")
                if(len(foundEndPoints) > 0 and foundEndPoints[0] != None and foundEndPoints[0]["endPointID"] != self.endPointID):
                    raise HTTPError(status=400, message="IP Address \"" + self.IPAddress + "\" and port \"" + str(self.port) + "\" are already used by another end-point")

            self.Online = self.Ping()
            self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_entry_inDB(DBPath, "endPoints", "endPointID", self.to_dict())

            entry = {
                "endPointID": self.endPointID, "lastUpdate": self.lastUpdate
            }
            update_entry_inDB(DBPath, "DeviceEndP_conn", "endPointID", entry)
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while updating end-point with ID \"" + self.endPointID + "\" in the DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while updating end-point with ID \"" + self.endPointID + "\" in the DB:\u0085\u0009" + str(e))

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving endPoint with ID \"" + self.endPointID + "\" to the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving endPoint with ID \"" + self.endPointID + "\" to the DB:\u0085\u0009" + str(e))
    
    def DB_to_dict(DBPath, EP):
        try:
            query = "SELECT * FROM EndPoints WHERE endPointID = \"" + EP["endPointID"] + "\""
            data = DBQuery_to_dict(DBPath, query)[0]
            data["Online"] = bool(data["Online"])
            return data
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while retrieving end-point with ID \"" + EP["endPointID"] + "\" from the DB:\u0085\u0009" + str(e))

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
                raise HTTPError(status=400, message="End-point with ID \"" + entry["endPointID"] + "\" not found in the database")

            delete_entry_fromDB(DBPath, "DeviceEndP_conn", "endPointID", entry["endPointID"])
            delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while deleting end-point with ID \"" + entry["endPointID"] + "\" from the DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while deleting end-point with ID \"" + entry["endPointID"] + "\" from the DB:\u0085\u0009" + str(e))
        
        return True

    def setOnlineStatus(newEPIDs):
        allEPIDs = getIDs_fromDB(DBPath, "EndPoints", "endPointID")

        missingEPIDs = list(set(allEPIDs) - set(newEPIDs))

        entry = {"endPointID": missingEPIDs, "Online": False, "lastUpdate": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

        update_entry_inDB(DBPath, "EndPoints", "endPointID", entry)

    def Ping(self):
        #TODO check devices that use this endpoint, ping them and return True if at least one is online
        return True