from utility import *

class EndPoint:
    def __init__(self, endPointData):
        self.endPointKeys = ["endPointID", "endPointName", "commProtocol", "IPAddress", "MQTTTopics"]
        self.connTables = ["DeviceEndP_conn"]

        self.checkKeys(endPointData)
        self.checkValues(endPointData)

        self.endPointID = endPointData["endPointID"]
        self.endPointName = endPointData["endPointName"]

        if(not isinstance(endPointData["commProtocol"], list)): endPointData["commProtocol"] = [endPointData["commProtocol"]]
        self.commProtocol = endPointData["commProtocol"]

        self.IPAddress = endPointData["IPAddress"]

        if(not isinstance(endPointData["MQTTTopics"], list)): endPointData["MQTTTopics"] = [endPointData["MQTTTopics"]]
        self.MQTTTopics = endPointData["MQTTTopics"]

        self.Online = self.Ping(self.endPoints)
        self.lastUpdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def to_dict(self):
        return {"endPointID": self.endPointID, "endPointName": self.endPointName, 
                "commProtocol": self.commProtocol, "IPAddress": self.IPAddress, 
                "MQTTTopics": self.MQTTTopics, "Online": self.Online, 
                "lastUpdate": self.lastUpdate}

    def checkKeys(self, endPointData):
        if(not all(key in self.endPointKeys for key in endPointData.keys())):
            raise web_exception(400, "Missing one or more keys")

    def checkValues(self, endPointData):
        if(not isinstance(endPointData["endPointID"], str)):
            raise web_exception(400, "\"endPointID\" value must be string")

        if(not isinstance(endPointData["endPointName"], str)):
            raise web_exception(400, "\"endPointName\" value must be string")
            
        if(not("MQTT" in endPointData["commProtocol"] or "REST" in endPointData["commProtocol"])):
            raise web_exception(400, "\"commProtocol\" must be MQTT and/or REST")

        if(not all(isinstance(ptrc, str) for ptrc in endPointData["commProtocol"])):
            raise web_exception(400, "\"commProtocol\" value must be a list of strings")

        if("REST" in endPointData["commProtocol"] and endPointData["IPAddress"] == None):
            raise web_exception(400, "\"IPAddress\" must not be null if commProtocol is REST")
        if("REST" in endPointData["commProtocol"] and not("MQTT" in endPointData["commProtocol"]) and endPointData["MQTTTopics"] != None):
            raise web_exception(400, "\"MQTTTopics\" must be null if commProtocol is REST")

        if(endPointData["commProtocol"] == "MQTT" and endPointData["MQTTTopics"] == None):
            raise web_exception(400, "\"MQTTTopics\" parameter must not be null if commProtocol is MQTT")
        if("MQTT" in endPointData["commProtocol"] and not("REST" in endPointData["commProtocol"]) and endPointData["IPAddress"] != None):
            raise web_exception(400, "\"IPAddress\" must be null if commProtocol is MQTT")

        if(("REST" in endPointData["commProtocol"] and "MQTT" in endPointData["commProtocol"]) and (endPointData["IPAddress"] == None or endPointData["MQTTTopics"] == None)):
            raise web_exception(400, "\"IPAddress\" and \"MQTTTopiscs\" must not be null if commProtocol are MQTT and REST")

        if(endPointData["IPAddress"] != None and not isinstance(endPointData["IPAddress"], str)): # TODO Check if IP address is valid
            raise web_exception(400, "\"IPAddress\" value must be string")
    
        if(endPointData["MQTTTopics"] != None and len(endPointData["MQTTTopics"]) == 0 and not all(isinstance(topic, str) for topic in endPointData["MQTTTopics"])): 
            raise web_exception(400, "\"MQTTTopics\" must be a list of strings not empty")

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
            raise web_exception(400, "An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while checking the consistency of the end-point with ID \"" + self.endPointID + "\" in the database: " + e)
        

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
                self.Online = self.Ping(self.endPoints)
                save_entry2DB(DBPath, "endPoints", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving end-point with ID \"" + self.endPointID + "\" to the DB: " + e)

    def DB_to_dict(DBPath, EP):
        try:
            query = "SELECT * FROM EndPoints WHERE endPointID = \"" + EP["endPointID"] + "\""
            data = DBQuery_to_dict(DBPath, query)[0]
            return data
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving end-point with ID \"" + EP["endPointID"] + "\" from the DB: " + e)

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["DeviceEndP_conn"]

        query = "SELECT * FROM EndPoints"
        data = DBQuery_to_dict(DBPath, query)
        
        if(not isinstance(data, list)) : data = [data]

        for entry in data:
            if(not check_presence_inConnectionTables(DBPath, connTables, "endPointID", entry["endPointID"])):
                delete_entry_fromDB(DBPath, "EndPoints", "endPointID", entry["endPointID"])

    def Ping(self, endPoints):
        return True