from requests import *
import time
import json

from threading import Thread, current_thread
from queue import Queue

from .utility import *
from .Error_Handler import *

class Register(Thread):
    def __init__(self, threadID, threadName, events, generalConfigs, config_file):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.events = events

        try:
            self.configs = generalConfigs["REGISTRATION"]
            self.generalConfigs = generalConfigs
            self.config_file = config_file

            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()

            self.check_and_loadConfigs()

            self.endPoints = []
            cond = (self.generalConfigs["REST"]["endPointID"] == None and self.generalConfigs["MQTT"]["endPointID"] == None)
            if(self.generalConfigs["CONFIG"]["activatedMethod"]["REST"]) : self.generateRESTEndPoint()
            if(self.generalConfigs["CONFIG"]["activatedMethod"]["MQTT"]) : self.generateMQTTEndPoint()
                    
            cond |= (self.generalConfigs["REST"]["endPointID"] == self.generalConfigs["MQTT"]["endPointID"])
            cond &= self.generalConfigs["CONFIG"]["activatedMethod"]["REST"] and self.generalConfigs["CONFIG"]["activatedMethod"]["MQTT"]
            if(cond):
                self.joinEndPoints()

            if(self.configs["serviceID"] == None):
                self.configs["serviceID"] = self.generateServiceID()
        
        except HTTPError as e:
            self.events["stopEvent"].set()
            raise HTTPError(status=e.status, message="An error occurred while initializing registration: \u0085\u0009" + e._message)
        except Exception as e:
            self.events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError("An error occurred while initializing registration: \u0085\u0009" + str(e))

    def run(self):
        self.KeepAlive()

    def check_and_loadConfigs(self):
        try:
            self.checkParams()
            self.validateParams()
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while loading registration configs: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while loading registration configs: \u0085\u0009" + str(e))


    def checkParams(self):
        self.config_params = ["enabled", "serviceName", "serviceID", "catalogAddress", "catalogPort", "T_Registration"]

        if(not all(param in self.configs for param in self.config_params)):
            raise self.clientErrorHandler.BadRequest("Missing parameters in config file")
    
    def validateParams(self):
        for key in self.config_params:
            match key:
                case "enabled":
                    if(not isinstance(self.configs["enabled"], bool)):
                        raise self.clientErrorHandler.BadRequest("enabled parameter must be a boolean")
                    self.enabled = self.configs["enabled"]
                case ("serviceName", "serviceID", "catalogAddress"):
                    if(not isinstance(self.configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(key + " parameter must be a string")
                    match key:
                        case "serviceID":
                            self.serviceID = self.configs["serviceID"]
                        case "serviceName":
                            self.serviceName = self.configs["serviceName"]
                        case "catalogAddress":
                            self.catalogAddress = self.configs["catalogAddress"]
                case "catalogPort":
                    if(not isinstance(self.configs["catalogPort"], int)): #TODO check port validity
                        raise self.clientErrorHandler.BadRequest("catalogPort parameter must be an integer")
                    self.catalogPort = self.configs["catalogPort"]
                case "T_Registration":
                    if(not isinstance(self.configs["T_Registration"], (int, float)) or self.configs["T_Registration"] < 0):
                        raise self.clientErrorHandler.BadRequest("T_Registration parameter must be a positive number")
                    self.T_Registration = self.configs["T_Registration"]
    
    def updateConfigFile(self, key, dict):
        try:
            with open(self.config_file, "r") as file:
                configs = json.load(file)
            configs[key].update(dict)
            with open(self.config_file, "w") as file:
                json.dump(configs, file, indent=4)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(
                "An error occurred while updating the configuration file: \u0085\u0009" + str(e)
            )

    def generateServiceID(self):
        existence = True
        while(existence):
            newID = "S" + randomB64String(6)

            url = self.configs["catalogAddress"] + ":" + str(self.configs["catalogPort"])+ "/checkPresence"
            params = {
                "table" : "Services",
                "keyName" : "serviceID",
                "keyValue" : newID
            }

            response = get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            existence = json.loads(response.text)["result"]

        self.updateConfigFile("REGISTRATION", {"serviceID":newID})

        return newID
    
    def generateEndPointID(self):
        existence = True
        while(existence):
            newID = "E" + randomB64String(6)

            url = self.configs["catalogAddress"] + ":" + str(self.configs["catalogPort"])+ "/checkPresence"
            params = {
                "table" : "EndPoints",
                "keyName" : "endPointID",
                "keyValue" : newID
            }

            response = get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            existence = json.loads(response.text)["result"]

        return newID
    
    def generateRESTEndPoint(self):
        if(self.generalConfigs["REST"]["endPointID"] == None):
            self.generalConfigs["REST"]["endPointID"] = self.generateEndPointID()
            self.updateConfigFile("REST", {"endPointID": self.generalConfigs["REST"]["endPointID"]})
        
        self.endPoints.append({
            "endPointID" : self.generalConfigs["REST"]["endPointID"],
            "endPointName" : self.generalConfigs["REST"]["endPointName"],
            "protocols" : ["REST"],
            "IPAddress" : self.generalConfigs["REST"]["IPAddress"],
            "port" : self.generalConfigs["REST"]["port"], 
            "CRUDMethods" : []
        })

        for key, value in self.generalConfigs["REST"]["CRUDMethods"].items():
            if(value):
                self.endPoints[0]["CRUDMethods"].append(key)

    def generateMQTTEndPoint(self):         
        if(self.generalConfigs["MQTT"]["endPointID"] == None):
            self.generalConfigs["MQTT"]["endPointID"] = self.generateEndPointID()
            self.updateConfigFile("MQTT", {"endPointID": self.generalConfigs["MQTT"]["endPointID"]})
        
        self.endPoints.append({
            "endPointID" : self.generalConfigs["MQTT"]["endPointID"],
            "endPointName" : self.generalConfigs["MQTT"]["endPointName"],
            "protocols" : ["MQTT"],
            "clientID" : self.generalConfigs["MQTT"]["clientID"],
            "MQTTTopics" : self.generalConfigs["MQTT"]["MQTTTopics"],
            "QOS" : self.generalConfigs["MQTT"]["QOS"]
        })

    def joinEndPoints(self):
        self.endPoints[0]["clientID"] = self.generalConfigs["MQTT"]["clientID"]
        self.endPoints[0]["protocols"].append("MQTT")        
        self.endPoints[0]["MQTTTopics"] = self.generalConfigs["MQTT"]["MQTTTopics"]
        self.endPoints[0]["QOS"] = self.generalConfigs["MQTT"]["QOS"]
        del self.endPoints[1]
        self.updateConfigFile("MQTT", {"endPointID": self.endPoints[0]["endPointID"]})

    def KeepAlive(self):
        serverErrorHandler = Server_Error_Handler()

        firstRun = True
        while not self.events["stopEvent"].is_set():
            try:
                url = self.configs["catalogAddress"] + ":" + str(self.configs["catalogPort"]) + "/setService"
                service = {
                    "serviceID" : self.configs["serviceID"],
                    "serviceName" : self.configs["serviceName"]
                }
                
                cond = "houseID" in self.generalConfigs["CONFIG"] and self.generalConfigs["CONFIG"]["houseID"] != None
                if(cond):
                    service["houseID"] = self.generalConfigs["CONFIG"]["houseID"]

                cond = "houseID" in self.generalConfigs["CONFIG"] and self.generalConfigs["CONFIG"]["houseID"] != None
                if(cond):
                    service["userID"] = self.generalConfigs["CONFIG"]["userID"]

                cond = "deviceID" in self.generalConfigs["CONFIG"] and self.generalConfigs["CONFIG"]["deviceID"] != None
                if(cond):
                    service["deviceID"] = self.generalConfigs["CONFIG"]["deviceID"]

                cond = "resourceID" in self.generalConfigs["CONFIG"] and self.generalConfigs["CONFIG"]["resourceID"] != None    
                if(cond):
                    service["resourceID"] = self.generalConfigs["CONFIG"]["resourceID"]

                service["endPoints"] = self.endPoints

                headers = {'Content-Type': "application/json", 'Accept': "application/json"}

                response = put(url, headers=headers, data=json.dumps([service]))
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, str(response.text))
                
            except HTTPError as e:
                self.events["stopEvent"].set()
                raise HTTPError(status = e.status, message="An error occurred while sending keep alive request: \u0085\u0009" + e._message)
            except Exception as e:
                self.events["stopEvent"].set()
                raise serverErrorHandler.InternalServerError("An error occurred while sending keep alive request: \u0085\u0009" + str(e))
            
            if(firstRun):
                firstRun = False
                print("REGISTRATION - Thread %s registered service for the first time" % current_thread().ident)
                self.events["startEvent"].set()
            
            time.sleep(self.configs["T_Registration"]*60)