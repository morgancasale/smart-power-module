from REST import *
from MQTT import *
from register import *


class ServiceBase(object):
    def __init__(self,config_address=None, init_rest_func=None,init_MQTT_func = None, GET=None, POST=None, PUT=None, DELETE=None, PATCH=None,Notifier=None, SubTopics=None):
        self.methods = ["MQTT", "REST"]
        self.RESTserver = None
        self.MQTTserver = None
    
    def check_and_loadConfigs(self): # TODO chek if file exists, check if all needed configs are there
        
        try:
            configs = json.load(open(self.config_file, 'r'))

            self.configs = configs["CONFIG"]
            self.checkParams()
            self.validateParams()



        except Exception as e:
            print(e)    
    
    
    def checkParams(self):
        config_params = ["serviceName", "serviceID", "activatedMethod"]
        if(not all(key in config_params for key in self.configs.keys())):
            raise self.errorHandler.MissingDataError("Misssing parameters in config file")
   
    def validateParams(self):
        if(not isinstance(self.configs["serviceName"], str)):
            raise self.errorHandler.MissingDataError("serviceName parameter must be a string")
        
        if(not isinstance(self.configs["serviceID"], str)):
            raise self.errorHandler.MissingDataError("serviceID parameter must be a string")
            
        for method in self.methods:
            if (method in self.configs["activatedMethod"].keys()):
                if (not isinstance(self.configs["activatedMethod"][method], bool)):
                    raise self.errorHandler.MissingDataError(
                        method + " parameter must be a boolean")

if __name__ == "__main__":
    Service = ServiceBase()
    if(Service.configs["activatedMethod"]["REST"]):
        Service.RESTserver = RESTServer(Service.configs["REST"], Service.initREST, Service.GET, Service.POST, Service.PUT, Service.DELETE, Service.PATCH)
        Service.RESTserver.openRESTServer(Service.RESTserver)
    if (Service.configs["activatedMethod"]["MQTT"]):
        Service.MQTTserver = MQTTServer(Service.configs["MQTT"], Service.initMQTT, Service.SubTopics, Service.Notifier)
        Service.MQTTserver.openMQTTServer(Service.MQTTserver)
       