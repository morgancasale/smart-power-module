from requests import *
import time
import json

from threading import Thread

from utility import *
from Error_Handler import *

class Register(Thread):
    def __init__(self, threadID, threadName, configs):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        
        self.configs = configs
        self.clientErrorHandler = Client_Error_Handler()
        self.serverErrorHandler = Server_Error_Handler()

        self.check_and_loadConfigs()

        if(self.configs["serviceID"] == None):
            self.configs["serviceID"] = self.generateServiceID()

    def run(self):
        self.KeepAlive()

    def check_and_loadConfigs(self):
        try:
            self.checkParams()
            self.validateParams()
        except web_exception as e:
            raise web_exception(e.code, "An error occurred while loading registration configs: \n\t" + e.message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while loading registration configs: \n\t" + str(e))


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
                case ("serviceName", "serviceID", "catalogAddress"):
                    if(not isinstance(self.configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(key + " parameter must be a string")
                case "catalogPort":
                    if(not isinstance(self.configs["catalogPort"], int)): #TODO check port validity
                        raise self.clientErrorHandler.BadRequest("catalogPort parameter must be an integer")
                case "T_Registration":
                    if(not isinstance(self.configs["T_Registration"], (int, float)) or self.configs["T_Registration"] < 0):
                        raise self.clientErrorHandler.BadRequest("T_Registration parameter must be a positive number")
    
    def generateServiceID(self):
        existence = True
        while(existence):
            newID = "S" + randomB64String(6)

            url = self.configs["catalogAddress"] + ":" + str(self.configs["catalogPort"])+ "/checkPresence"
            params = {
                "table" : "Services",
                "keyNames" : "serviceID",
                "keyValues" : newID
            }

            response = get(url, params=params)
            if(response.status_code != 200):
                raise web_exception(response.status_code, str(response.content))
            
            existence = json.loads(response.content)["result"]

        return newID

    def KeepAlive(self):
        serverErrorHandler = Server_Error_Handler()
        while True:
            try:
                url = self.configs["catalogAddress"] + ":" + str(self.configs["catalogPort"]) + "/setService"
                service = {
                    "serviceID" : self.configs["serviceID"],
                    "serviceName" : self.configs["serviceName"]
                }
                headers = {'Content-Type': "application/json", 'Accept': "application/json"}

                response = put(url, headers=headers, data=json.dumps([service]))
                if(response.status_code != 200):
                    raise web_exception(response.status_code, str(response.content))
                
            except web_exception as e:    
                raise web_exception(e.code, "An error occurred while sending keep alive request: \n\t" + e.message)
            except Exception as e:
                raise serverErrorHandler.InternalServerError("An error occurred while sending keep alive request: \n\t" + str(e))
            
            time.sleep(self.configs["T_Registration"]*60)