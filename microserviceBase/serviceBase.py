from .REST import *
from .MQTT import *
from .register import *

from .Error_Handler import *

class ServiceBase(object):
    def __init__(self, config_file=None, init_REST_func=None, init_MQTT_func = None, GET=None, POST=None, PUT=None, DELETE=None, PATCH=None, Notifier=None):
        try: 
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.config_file = config_file

            self.configParams = ["activatedMethod", "houseID", "userID", "deviceID", "resourceID"]

            self.check_and_loadConfigs()

            queues = {
                "REST": Queue(),
                "MQTT": Queue()
            }

            if(self.generalConfigs["REGISTRATION"]["enabled"]):
                self.registerService = Register(1, "RegThread", queues, self.generalConfigs, config_file)
                self.registerService.start()
            else:
                queues["REST"].put(True)
                queues["MQTT"].put(True)

            if(self.configs["activatedMethod"]["REST"]):
                self.REST = RESTServer(2, "RESTThread", queues["REST"], self.generalConfigs["REST"], init_REST_func, GET, POST, PUT, DELETE, PATCH)
                self.REST.start()
            
            if(self.configs["activatedMethod"]["MQTT"]):
                self.MQTT = MQTTServer(3, "MQTTThread", queues["MQTT"], self.generalConfigs["MQTT"], config_file, init_MQTT_func, Notifier)
                self.MQTT.start()
    
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while enabling the servers: \n\t" + e._message)
    
    def check_and_loadConfigs(self):
        try:
            self.generalConfigs = json.load(open(self.config_file, 'r'))

            self.configs = self.generalConfigs["CONFIG"]
            self.checkParams()
            self.validateParams()
        
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while loading configs: \n\t" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while loading configs: \n\t" + str(e))
        
    
    
    def checkParams(self):
        if(not all(key in self.configParams for key in list(self.configs.keys()))):
            raise self.clientErrorHandler.BadRequest("Missing parameters in config file")
   
    def validateParams(self):
        for key in self.configParams:
            match key:
                case "activatedMethod":
                    methods = ["REST", "MQTT"]
                    
                    if (not all(key in methods for key in self.configs["activatedMethod"].keys())):
                        raise self.clientErrorHandler.BadRequest("Missing methods in activatedMethod parameter")

                    err_cond = not isinstance(self.configs["activatedMethod"]["REST"], bool)
                    err_cond = err_cond or not isinstance(self.configs["activatedMethod"]["MQTT"], bool)
                    if(err_cond):
                        raise self.clientErrorHandler.BadRequest("activatedMethod parameters must be boolean")
                case ("houseID", "userID", "resourceID", "deviceID"):
                    if(self.configs[key] != None):
                        if(not isinstance(self.configs[key], list)):
                            raise self.clientErrorHandler.BadRequest(key + " parameter must be a list or null")
                        if(not all(isinstance(item, str) for item in self.configs[key])):
                            raise self.clientErrorHandler.BadRequest(key + " parameter must be a list of strings")

        


if __name__ == "__main__":
    Service = ServiceBase()
    
       