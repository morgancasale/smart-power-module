import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from utility import *

from microserviceBase.Error_Handler import *
class EndPoint:
    def __init__(self, endPointData, newEndPoint = False):
        self.endPointKeys = sorted([
            "endPointID", "endPointName", "protocols", 
            "IPAddress", "port", "clientID", "CRUDMethods", 
            "MQTTTopics", "MQTTUser", "MQTTPassword", "QOS"
        ])
        self.connTables = ["DeviceEndP_conn"]
        
        if(newEndPoint) : self.checkKeys(endPointData)
        self.checkSaveValues(endPointData)

        self.endPointData = endPointData

        if(newEndPoint):
            self.Online = self.Ping()
            self.lastUpdate = time.time()


    def to_dict(self):
        result = {}

        for key in self.endPointData.keys():
            result[key] = self.endPointData[key]

        result["Online"] = self.Online
        result["lastUpdate"] = self.lastUpdate

        return result

    def checkKeys(self, endPointData):
        if(self.endPointKeys != sorted(endPointData.keys())):
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")

    def checkSaveValues(self, endPointData):
        for key in endPointData.keys():
            match key:
                case ("endPointID" | "endPointName" | "MQTTUser" | "MQTTPassword"):
                    if(endPointData[key] != None and not isinstance(endPointData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="End-point's \"" + key + "\" value must be string")
                    match key:
                        case "endPointID":
                            self.endPointID = endPointData["endPointID"]
                        case "endPointName":
                            self.endPointName = endPointData["endPointName"]
                        case "MQTTUser":
                            self.MQTTUser = endPointData["MQTTUser"]
                        case "MQTTPassword":
                            self.MQTTPassword = endPointData["MQTTPassword"]

                case "protocols":
                    if(not("MQTT" in endPointData[key] or "REST" in endPointData[key])):
                        raise Client_Error_Handler.BadRequest(message="\"protocols\" must be MQTT and/or REST")

                    if(not all(isinstance(prtcl, str) for prtcl in endPointData[key])):
                        raise Client_Error_Handler.BadRequest(message="\"protocols\" value must be a list of strings")

                    if("REST" in endPointData[key] and endPointData["IPAddress"] == None):
                        raise Client_Error_Handler.BadRequest(message="\"IPAddress\" must not be null if protocols is REST")
                    if("REST" in endPointData[key] and not("MQTT" in endPointData[key]) and endPointData["MQTTTopics"] != None):
                        raise Client_Error_Handler.BadRequest(message="\"MQTTTopics\" must be null if protocols is REST")

                    if("MQTT" in endPointData[key] and endPointData["MQTTTopics"] == None):
                        raise Client_Error_Handler.BadRequest(message="\"MQTTTopics\" parameter must not be null if protocols is MQTT")
                    
                    cond = "MQTT" in endPointData[key] and not("REST" in endPointData[key])
                    cond &= "IPAddress" in endPointData.keys() and endPointData["IPAddress"] != None
                    if(cond):
                        raise Client_Error_Handler.BadRequest(message="\"IPAddress\" must be null if protocols is MQTT")
                    
                    if(not isinstance(endPointData["protocols"], list)) : endPointData["protocols"] = [endPointData["protocols"]]
                    self.protocols = endPointData["protocols"]

                case "IPAddress":
                    if(endPointData[key] != None and not isinstance(endPointData[key], str)): # TODO Check if IP address is valid
                        raise Client_Error_Handler.BadRequest(message="\"IPAddress\" value must be string")
                    self.IPAddress = endPointData["IPAddress"]

                case ("port"):
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)): # TODO Check if port is valid
                        raise Client_Error_Handler.BadRequest(message="\"" + key + "\" value must be integer")
                    self.port = endPointData["port"]

                case "QOS":
                    if(endPointData[key] != None and not isinstance(endPointData[key], int)):
                        raise Client_Error_Handler.BadRequest(message="\"" + key + "\" value must be integer")
                    if(endPointData[key] != None and not (endPointData[key] in [0,1,2])):
                        raise Client_Error_Handler.BadRequest(message="\"" + key + "\" value must be 0, 1 or 2")
                    self.QOS = endPointData[key]

                case "clientID":
                    if(not("MQTT" in endPointData["protocols"]) and endPointData[key] == None):
                        raise Client_Error_Handler.BadRequest(message="\"clientID\" must not be null if protocols is MQTT")
                    if(not isinstance(endPointData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="\"clientID\" value must be string")
                    self.clientID = endPointData["clientID"]

                case "CRUDMethods":
                    methods = endPointData[key]
                    if("REST" in endPointData["protocols"]):
                        if(not isinstance(methods, list)):
                            raise Client_Error_Handler.BadRequest(message="\"CRUDMethods\" value must be a list")
                        if(not all(isinstance(method, str) for method in methods)):
                            raise Client_Error_Handler.BadRequest(message="\"CRUDMethods\" value must be a list of strings")
                        if(not all(method in ["GET", "POST", "PUT", "DELETE", "PATCH"] for method in methods)):
                            raise Client_Error_Handler.BadRequest(message="Unexpected method in \"" + key +"\".")
                        self.CRUDMethods = methods
                case "MQTTTopics":
                    topics = endPointData[key]
                    if("MQTT" in endPointData["protocols"]):
                        if(not isinstance(topics, dict)):
                            raise Client_Error_Handler.BadRequest(message="\"" + key + "\" must be a dictionary")
                        if(not all(key in ["pub", "sub"] for key in topics.keys())):
                            raise Client_Error_Handler.BadRequest(message="\"" + key + "\" must have parameters \"pub\" and \"sub\"")
                        
                        if(topics["sub"] != None and not isinstance(topics["sub"], list)):
                            raise Client_Error_Handler.BadRequest(message="Subscription \"" + key + "\" must be a list")
                        if(topics["sub"] != None and not all(isinstance(topic, str) for topic in topics["sub"])):
                            raise Client_Error_Handler.BadRequest(message="Subscription \"" + key + "\" must be a list of strings")
                        
                        if(topics["pub"] != None and not isinstance(topics["pub"], list)):
                            raise Client_Error_Handler.BadRequest(message="Publication \"" + key + "\" must be a list")
                        if(topics["pub"] != None and not all(isinstance(topic, str) for topic in topics["pub"])):
                            raise Client_Error_Handler.BadRequest(message="Publication \"" + key + "\" must be a list of strings")
                        
                        self.MQTTTopics = endPointData[key]
                    
                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")

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
            raise HTTPError(
                status=e.status, message="An error occurred while checking the consistency of the end-point with ID \"" + 
                self.endPointID + "\" in the database:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while checking the consistency of the end-point with ID \"" + 
                self.endPointID + "\" in the database:\u0085\u0009" + str(e)
            )
        
    def save2DB(self, DBPath): # TODO Check if all error cases are covered
        try:
            if(check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                if(not self.check_consistency_inDB(DBPath)):
                    raise Client_Error_Handler.BadRequest(message="An end-point with ID \"" + self.endPointID + "\" already exists in the database with different parameters")

                if(self.IPAddress != None and check_presence_inConnectionTables(DBPath, self.connTables, "endPointID", self.endPointID)):
                    raise Client_Error_Handler.BadRequest(message="An end-point with ID \"" + self.endPointID + "\" is already used in another connection")
            else:
                foundEndPoints = []
                if("IPAddress" in self.endPointData.keys() and self.endPointData["IPAddress"] != None):
                    foundEndPoints = DBQuery_to_dict(DBPath, "SELECT * FROM endPoints WHERE (\"IPAddress\", \"port\") = (\"" + self.IPAddress + "\", \"" + str(self.port) + "\")")
                if(len(foundEndPoints) > 0 and foundEndPoints[0] != None and foundEndPoints[0]["endPointID"] != self.endPointID):
                    raise HTTPError(status=400, message="IP Address \"" + self.IPAddress + "\" and port \"" + str(self.port) + "\" are already used by another end-point")
                self.Online = self.Ping()
                self.lastUpdate = time.time()
                save_entry2DB(DBPath, "endPoints", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving end-point with ID \"" + 
                self.endPointID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving end-point with ID \"" + 
                self.endPointID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "endPoints", "endPointID", self.endPointID)):
                raise Client_Error_Handler.NotFound(message="End-point with ID \"" + self.endPointID + "\" not found in the database")
            
            if("IPAddress" in self.endPointData.keys()):
                foundEndPoints = DBQuery_to_dict(DBPath, "SELECT * FROM endPoints WHERE (\"IPAddress\", \"port\") = (\"" + self.IPAddress + "\", \"" + str(self.port) + "\")")
                if(len(foundEndPoints) > 0 and foundEndPoints[0] != None and foundEndPoints[0]["endPointID"] != self.endPointID):
                    raise Client_Error_Handler.BadRequest(message="IP Address \"" + self.IPAddress + "\" and port \"" + str(self.port) + "\" are already used by another end-point")

            self.Online = self.Ping()
            self.lastUpdate = time.time()
            update_entry_inDB(DBPath, "endPoints", "endPointID", self.to_dict())

            entry = {
                "endPointID": self.endPointID, "lastUpdate": self.lastUpdate
            }
            update_entry_inDB(DBPath, "DeviceEndP_conn", "endPointID", entry)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while updating end-point with ID \"" + 
                self.endPointID + "\" in the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while updating end-point with ID \"" + self.endPointID + "\" in the DB:\u0085\u0009" + str(e)
            )

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", self.endPointID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving endPoint with ID \"" + 
                self.endPointID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving endPoint with ID \"" + self.endPointID + "\" to the DB:\u0085\u0009" + str(e)
            )
    
    def DB_to_dict(DBPath, EP):
        try:
            query = "SELECT * FROM EndPoints WHERE endPointID = \"" + EP["endPointID"] + "\""
            data = DBQuery_to_dict(DBPath, query)[0]
            data["Online"] = bool(data["Online"])
            return data
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while retrieving end-point with ID \"" + EP["endPointID"] + "\" from the DB:\u0085\u0009" + str(e)
            )

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["DeviceEndP_conn"]

        try:
            query = "SELECT * FROM EndPoints"
            data = DBQuery_to_dict(DBPath, query)
            
            if(not isinstance(data, list)) : data = [data]

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "endPointID", entry["endPointID"])):
                    delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while cleaning the DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while cleaning the DB:\u0085\u0009" + str(e))
    

    def deleteFromDB(DBPath, entry):
        try:
            if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])):
                raise HTTPError(status=400, message="End-point with ID \"" + entry["endPointID"] + "\" not found in the database")

            delete_entry_fromDB(DBPath, "DeviceEndP_conn", "endPointID", entry["endPointID"])
            delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while deleting end-point with ID \"" + 
                entry["endPointID"] + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while deleting end-point with ID \"" + 
                entry["endPointID"] + "\" from the DB:\u0085\u0009" + str(e)
            )
        
        return True

    def setOnlineStatus(newEPIDs):
        try:
            allEPIDs = getIDs_fromDB(DBPath, "EndPoints", "endPointID")

            missingEPIDs = list(set(allEPIDs) - set(newEPIDs))

            entry = {"endPointID": missingEPIDs, "Online": False, "lastUpdate": time.time()}

            update_entry_inDB(DBPath, "EndPoints", "endPointID", entry)
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while setting online status:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while setting online status:\u0085\u0009" + str(e))
        

    def Ping(self):
        #TODO check devices that use this endpoint, ping them and return True if at least one is online
        return True