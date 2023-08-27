from .REST import *
from .MQTT import *
from .register import *

from .Error_Handler import *

from threading import Event

class ServiceBase(object):
    def __init__(self, config_file=None, 
                 init_REST_func=None, add_REST_funcs = None, 
                 init_MQTT_func = None, add_MQTT_funcs = None, 
                 GET=None, POST=None, PUT=None, DELETE=None, PATCH=None, 
                 Notifier=None):
        try: 
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.config_file = config_file

            self.init_REST_func = init_REST_func
            self.add_REST_funcs = add_REST_funcs

            self.init_MQTT_func = init_MQTT_func
            self.add_MQTT_funcs = add_MQTT_funcs

            self.GET = GET
            self.POST = POST
            self.PUT = PUT
            self.DELETE = DELETE
            self.PATCH = PATCH

            self.Notifier = Notifier

            self.configParams = ["activatedMethod", "HomeAssistant", "houseID", "userID", "deviceID", "resourceID"]

            self.check_and_loadConfigs()

            if(self.configs["HomeAssistant"]["enabled"] and self.configs["HomeAssistant"]["autoHA"]):
                self.getHAEndpoint()

            self.events = {
                "startEvent" : Event(),
                "stopEvent" : Event()
            }
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while initializing the service: \u0085\u0009" + e._message)
        
    def start(self):
        try:
            if(self.generalConfigs["REGISTRATION"]["enabled"]):
                self.registerService = Register(1, "RegThread", self.events, self.generalConfigs, self.config_file)
                self.registerService.start()
            else:
                print("Registration is disabled, starting service...")
                self.events["startEvent"].set()

            self.MQTT = None
            if(self.configs["activatedMethod"]["MQTT"]):
                self.MQTT = MQTTServer(
                    3, "MQTTThread", self.events, self.generalConfigs["MQTT"], self.generalConfigs,
                    self.config_file, self.init_MQTT_func, self.Notifier
                )
                self.MQTT.start()
            
            self.REST = None
            if(self.configs["activatedMethod"]["REST"]):
                self.REST = RESTServer(
                    2, "RESTThread", self.events, self.generalConfigs["REST"], self.generalConfigs,
                    self.init_REST_func, self.add_REST_funcs, self.MQTT,
                    self.GET, self.POST, self.PUT, self.DELETE, self.PATCH
                )
                self.REST.start()
                        
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while enabling the service: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while enabling the service: \u0085\u0009" + str(e))

    def stop(self):
        self.events["stopEvent"].set()
    
    def check_and_loadConfigs(self):
        try:
            self.generalConfigs = json.load(open(self.config_file, 'r'))

            self.configs = self.generalConfigs["CONFIG"]
            self.checkParams()
            self.validateParams()
        
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while loading configs: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while loading configs: \u0085\u0009" + str(e))
        
    def checkParams(self):
        if(not all(key in self.configParams for key in list(self.configs.keys()))):
            raise self.clientErrorHandler.BadRequest(message="Missing parameters in config file")
   
    def validateParams(self):
        for key in self.configParams:
            match key:
                case "activatedMethod":
                    methods = ["REST", "MQTT"]
                    
                    if (not all(key in methods for key in self.configs["activatedMethod"].keys())):
                        raise self.clientErrorHandler.BadRequest(message="Missing methods in activatedMethod parameter")

                    err_cond = not isinstance(self.configs["activatedMethod"]["REST"], bool)
                    err_cond = err_cond or not isinstance(self.configs["activatedMethod"]["MQTT"], bool)
                    if(err_cond):
                        raise self.clientErrorHandler.BadRequest(message="activatedMethod parameters must be boolean")
                case ("houseID", "userID", "resourceID", "deviceID"):
                    if(self.configs[key] != None):
                        if(not isinstance(self.configs[key], list)):
                            raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a list or null")
                        if(not all(isinstance(item, str) for item in self.configs[key])):
                            raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a list of strings")
                case "HomeAssistant":
                    params = ["enabled", "token", "address", "port"] 
                    if(not all(key in self.configs["HomeAssistant"].keys() for key in params)):
                        raise self.clientErrorHandler.BadRequest(message="Missing parameters in HomeAssistant configs")
                    for key in self.configs["HomeAssistant"].keys():
                        match key:
                            case ("enabled" | "autoHA"):
                                if(not isinstance(self.configs["HomeAssistant"]["enabled"], bool)):
                                    raise self.clientErrorHandler.BadRequest(message="HomeAssistant enabled parameter must be a boolean")
                            case ("token" | "baseTopic" | "system"):
                                if(not isinstance(self.configs["HomeAssistant"][key], str)):
                                    raise self.clientErrorHandler.BadRequest(message="HomeAssistant " + key + " parameter must be a string")
                                self.HAToken = self.configs["HomeAssistant"][key]
                            case "address":
                                cond = self.configs["HomeAssistant"][key] != None
                                cond &= not isinstance(self.configs["HomeAssistant"][key], str)
                                if(cond):
                                    raise self.clientErrorHandler.BadRequest(message="HomeAssistant " + key + " parameter must be a string")
                                self.HAIP = self.configs["HomeAssistant"][key]
                            case "port":
                                if(self.configs["HomeAssistant"][key] != None):
                                    cond = not isinstance(self.configs["HomeAssistant"]["port"], int)
                                    cond |= self.configs["HomeAssistant"]["port"] < 0 or self.configs["HomeAssistant"]["port"] > 65535
                                    if(cond):
                                        raise self.clientErrorHandler.BadRequest(message="HomeAssistant port parameter must be an integer between 0 and 65535")
                                self.HAPort = self.configs["HomeAssistant"][key]
                                
                            case ("address" | "port"):
                                cond = not self.configs["HomeAssistant"]["autoHA"]
                                cond &= (self.configs["HomeAssistant"]["address"] == None or self.configs["HomeAssistant"]["port"] == None)
                                if(cond):
                                    raise self.clientErrorHandler.BadRequest(message="HomeAssistant address and port parameters must be specified if autoHA is not enabled")

    def updateConfigFile(self, keys, dict):
        if(not isinstance(keys, list)): keys = [keys]
        try:
            with open(self.config_file, "r") as file:
                configs = json.load(file)
            config = configs
            for key in keys:
                config = config[key]
            config.update(dict)
            with open(self.config_file, "w") as file:
                json.dump(configs, file, indent=4)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message=
                "An error occurred while updating the configuration file: \u0085\u0009" + str(e)
            )

    def getHAEndpoint(self):
        try:
            url = self.generalConfigs["REGISTRATION"]["catalogAddress"] + ":" 
            url += str(self.generalConfigs["REGISTRATION"]["catalogPort"])+ "/getInfo"
            params = {
                "table" : "EndPoints",
                "keyName" : "endPointName",
                "keyValue" : "HomeAssistant"
            }

            response = get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            response = response.json()[0]

            self.updateConfigFile(["CONFIG", "HomeAssistant"], {"address": response["IPAddress"], "port": response["port"]})

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while getting Home Assistant endpoint: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while getting Home Assistant endpoint: \u0085\u0009" + str(e))


    def notifyHA(self, payload):
        r"""Allows to trigger a notification in Home Assistant
            The method expects a dictionary with the following structure:
            >>> {
            >>>    "title": "Notification title",
            >>>    "message": "Notification message"
            >>> }
        """
        if(not self.configs["HomeAssistant"]["enabled"]):
            raise self.clientErrorHandler.BadRequest(message="Home Assistant connection is not enabled")

        try:
            url = "%s:%s/api/services/notify/persistent_notification" % (
                self.configs["HomeAssistant"]["address"], 
                self.configs["HomeAssistant"]["port"]
            )

            headers = {
                "Authorization": "Bearer " + self.configs["HomeAssistant"]["token"],
                'content-type': "application/json",
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
        except HTTPError as e:            
            raise HTTPError(status=e.status, message="An error occurred while notifying Home Assistant: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while notifying Home Assistant: \u0085\u0009" + str(e))
            


if __name__ == "__main__":
    Service = ServiceBase()
    
       