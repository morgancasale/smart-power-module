from REST import *
from MQTT import *
from register import *

from Error_Handler import *


class ServiceBase(object):
    def __init__(self, config_file=None, init_REST_func=None, init_MQTT_func = None, GET=None, POST=None, PUT=None, DELETE=None, PATCH=None, Notifier=None, SubTopics=None):
        try: 
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.config_file = config_file

            self.check_and_loadConfigs()

            if(self.generalConfigs["REGISTRATION"]["enabled"]):
                self.registerService = Register(1, "RegThread", self.generalConfigs["REGISTRATION"])
                self.registerService.start()

            if(self.configs["activatedMethod"]["REST"]):
                self.REST = RESTServer(2, "RESTThread", self.generalConfigs["REST"], init_REST_func, GET, POST, PUT, DELETE, PATCH)
                self.REST.start()
            
            if(self.configs["activatedMethod"]["MQTT"]):
                self.MQTT = MQTTServer(3, "MQTTThread", self.generalConfigs["MQTT"], init_MQTT_func, Notifier, SubTopics)
                self.MQTT.start()
    
        except web_exception as e:
            raise web_exception(e.code, "An error occurred while enabling servers: \n\t" + e.message)


        
    
    def check_and_loadConfigs(self):
        try:
            self.generalConfigs = json.load(open(self.config_file, 'r'))

            self.configs = self.generalConfigs["CONFIG"]
            self.checkParams()
            self.validateParams()
        
        except web_exception as e:
            raise web_exception(e.code, "An error occurred while loading configs: \n\t" + e.message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while loading configs: \n\t" + str(e))
        
    
    
    def checkParams(self):
        config_params = ["activatedMethod"]
        if(not all(key in config_params for key in self.configs.keys())):
            raise self.clientErrorHandler.BadRequest("Missing parameters in config file")
   
    def validateParams(self):
        methods = ["REST", "MQTT"]
        
        if (not all(key in methods for key in self.configs["activatedMethod"].keys())):
            raise self.clientErrorHandler.BadRequest("Missing methods in activatedMethod parameter")

        err_cond = not isinstance(self.configs["activatedMethod"]["REST"], bool)
        err_cond = err_cond or not isinstance(self.configs["activatedMethod"]["MQTT"], bool)
        if(err_cond):
            raise self.clientErrorHandler.BadRequest("activatedMethod parameters must be boolean")
        


if __name__ == "__main__":
    Service = ServiceBase()
    
       