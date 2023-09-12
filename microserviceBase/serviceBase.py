from .REST import *
from .MQTT import *
from .register import *

from .Error_Handler import *

from threading import Event
import dns.resolver

IN_DOCKER = os.environ.get("IN_DOCKER", False)

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

            self.configParams = {
                "CONFIG": {
                    "activatedMethod": ["REST", "MQTT"],
                    "HomeAssistant": ["enabled", "token", "autoHA", "HA_mDNS", "address", "port"]
                },
                "REGISTRATION": ["enabled", "serviceID", "serviceName", "catalogAddress", "catalogPort", "T_Registration"]
            }

            self.check_and_loadConfigs()

            if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"] and self.generalConfigs["CONFIG"]["HomeAssistant"]["autoHA"]):
                self.getHAEndpoint()
            
            # Wait for the catalog to be ready
            cond = bool(IN_DOCKER)
            cond &= self.generalConfigs["REGISTRATION"]["enabled"]
            cond &= self.generalConfigs["REGISTRATION"]["serviceName"] != "ResourceCatalog"
            if(cond):
                time.sleep(5)

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
            if(self.generalConfigs["CONFIG"]["activatedMethod"]["MQTT"]):
                self.MQTT = MQTTServer(
                    3, "MQTTThread", self.events, self.generalConfigs["MQTT"], self.generalConfigs,
                    self.config_file, self.init_MQTT_func, self.Notifier
                )
                self.MQTT.start()
            
            self.REST = None
            if(self.generalConfigs["CONFIG"]["activatedMethod"]["REST"]):
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

            self.checkParams()
            self.validateParams()
        
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while loading configs: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while loading configs: \u0085\u0009" + str(e))
        
    def checkParams(self):
        message = "Missing parameters in config file"
        for key in self.generalConfigs.keys():
            if(key == "CONFIG" or key == "REGISTRATION"):
                if(key not in self.configParams.keys()):
                    raise self.clientErrorHandler.BadRequest(message = message)

                if type(self.configParams[key]) is dict:
                    for subKey in self.configParams[key]:
                        if(subKey not in self.generalConfigs[key]):
                            raise self.clientErrorHandler.BadRequest(message = message)
                        a = sorted(self.generalConfigs[key][subKey].keys())
                        b = sorted(self.configParams[key][subKey])
                        diff = list(set(a)-set(b))
                        if(len(list(set(b).intersection(diff)))>0):
                            raise self.clientErrorHandler.BadRequest(message = message)
                elif type(self.configParams[key]) is list:
                    a = sorted(self.configParams[key])
                    b = sorted(self.generalConfigs[key].keys())
                    diff = list(set(a)-set(b))
                    if(len(list(set(b).intersection(diff))) > 0):
                        print("pesce")
                        raise self.clientErrorHandler.BadRequest(message = message)
                
    def validate_HA_Params(self):
        configs = self.generalConfigs["CONFIG"]["HomeAssistant"]
        params = ["enabled", "token", "address", "port"] 
        if(not all(key in configs.keys() for key in params)):
            raise self.clientErrorHandler.BadRequest(message="Missing parameters in HomeAssistant configs")
        
        for key in configs.keys():
            match key:
                case ("enabled" | "autoHA"):
                    if(not isinstance(configs["enabled"], bool)):
                        raise self.clientErrorHandler.BadRequest(message="HomeAssistant enabled parameter must be a boolean")
                case ("token" | "baseTopic" | "system"):
                    if(not isinstance(configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(message="HomeAssistant " + key + " parameter must be a string")
                    self.HAToken = configs[key]
                case "HA_mDNS":
                    if(not isinstance(configs[key], str)):
                        message = "HomeAssistant " + key + " parameter must be a string"
                        raise self.clientErrorHandler.BadRequest(message=message)
                    trueIP = "http://"+self.resolvemDNS(configs[key])
                    self.updateConfigFile(["CONFIG", "HomeAssistant"], {"address": trueIP})
                    self.HAIP = trueIP
                case "address":
                    cond = configs[key] != None
                    cond &= not isinstance(configs[key], str)
                    if(cond):
                        raise self.clientErrorHandler.BadRequest(message="HomeAssistant " + key + " parameter must be a string")
                    self.HAIP = configs[key]
                case "port":
                    if(configs[key] != None):
                        cond = not isinstance(configs["port"], int)
                        cond |= configs["port"] < 0 or configs["port"] > 65535
                        if(cond):
                            raise self.clientErrorHandler.BadRequest(message="HomeAssistant port parameter must be an integer between 0 and 65535")
                    self.HAPort = configs[key]
                    
                case ("address" | "port"):
                    cond = not configs["autoHA"]
                    cond &= (configs["address"] == None or configs["port"] == None)
                    if(cond):
                        raise self.clientErrorHandler.BadRequest(message="HomeAssistant address and port parameters must be specified if autoHA is not enabled")
    
    def validate_registrationParams(self):
        configs = self.generalConfigs["REGISTRATION"]
        params = ["enabled", "serviceID", "serviceName", "catalogAddress", "catalogPort", "T_Registration"]
        if(not all(key in configs.keys() for key in params)):
            raise self.clientErrorHandler.BadRequest(message="Missing parameters in REGISTRATION configs")
        
        for key in configs.keys():
            match key:
                case ("enabled"):
                    if(not isinstance(configs[key], bool)):
                        raise self.clientErrorHandler.BadRequest(message="REGISTRATION enabled parameter must be a boolean")
                case ("serviceID" | "serviceName" | "catalog_mDNS" | "catalogAddress"):
                    if(not isinstance(configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(message="REGISTRATION " + key + " parameter must be a string")
                    if(configs["enabled"]):
                        if(key == "catalog_mDNS" and not IN_DOCKER):
                            trueIP = "http://" + self.resolvemDNS(configs[key])
                            print("Resolved mDNS: " + trueIP)
                            self.generalConfigs["REGISTRATION"]["catalogAddress"] = trueIP
                            self.updateConfigFile(["REGISTRATION"], {"catalogAddress": trueIP})
                        if(key == "catalogAddress" and IN_DOCKER):
                            try:
                                trueIP = "http://" + socket.gethostbyname("resourcecatalog")
                                print("Resolved catalog: " + trueIP)
                                self.generalConfigs["REGISTRATION"]["catalogAddress"] = trueIP
                                self.updateConfigFile(["REGISTRATION"], {"catalogAddress": trueIP})
                            except Exception:
                                continue

                case ("catalogPort"):
                    cond = not isinstance(configs[key], int)
                    cond |= configs[key] < 0 or configs[key] > 65535
                    if(cond):
                        raise self.clientErrorHandler.BadRequest(message="REGISTRATION port parameter must be an integer between 0 and 65535")
                
                case ("T_Registration"):
                    cond = not isinstance(configs[key], (int, float))
                    cond |= configs[key] < 0
                    if(cond):
                        raise self.clientErrorHandler.BadRequest(message="REGISTRATION T_Registration parameter must be a positive number")
        
        print("Catalog address: " + self.generalConfigs["REGISTRATION"]["catalogAddress"])
        
    def validateParams(self):
        for key in self.configParams:
            configs = self.generalConfigs[key]
            match key:
                case "CONFIG":
                    for subKey in self.configParams[key]:
                        match subKey:
                            case "activatedMethod":
                                methods = sorted(["REST", "MQTT"])
                                
                                if (methods != sorted(configs["activatedMethod"].keys())):
                                    raise self.clientErrorHandler.BadRequest(message="Missing methods in activatedMethod parameter")

                                err_cond = not isinstance(configs["activatedMethod"]["REST"], bool)
                                err_cond = err_cond or not isinstance(configs["activatedMethod"]["MQTT"], bool)
                                if(err_cond):
                                    raise self.clientErrorHandler.BadRequest(message="activatedMethod parameters must be boolean")
                            case ("houseID", "userID", "resourceID", "deviceID"):
                                if(configs[key] != None):
                                    if(not isinstance(configs[key], list)):
                                        raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a list or null")
                                    if(not all(isinstance(item, str) for item in configs[key])):
                                        raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a list of strings")
                            case "HomeAssistant":
                                self.validate_HA_Params()
                case "REGISTRATION":
                    self.validate_registrationParams()      

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
        if(not self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
            raise self.clientErrorHandler.BadRequest(message="Home Assistant connection is not enabled")

        try:
            url = "%s:%s/api/services/notify/persistent_notification" % (
                self.generalConfigs["CONFIG"]["HomeAssistant"]["address"], 
                self.generalConfigs["CONFIG"]["HomeAssistant"]["port"]
            )

            headers = {
                "Authorization": "Bearer " + self.generalConfigs["CONFIG"]["HomeAssistant"]["token"],
                'content-type': "application/json",
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
        except HTTPError as e:            
            raise HTTPError(status=e.status, message="An error occurred while notifying Home Assistant: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while notifying Home Assistant: \u0085\u0009" + str(e))
    
    def resolvemDNS(self, mDNS):
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ["224.0.0.251"]
            resolver.port = 5353
            sol = resolver.resolve(mDNS, "A")
            return str(sol[0].to_text())
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while resolving mDNS: \u0085\u0009" + str(e))


if __name__ == "__main__":
    Service = ServiceBase()