import cherrypy
import cherrypy_cors
import os
import requests
import socket
import sqlite3 as sq
import pandas as pd

from threading import Thread, Event, current_thread

from .Error_Handler import *

IN_DOCKER = os.environ.get("IN_DOCKER", False)

class RESTServer(Thread):
    global allowedMethods

    def __init__(self, threadID, threadName, events, configs, generalConfigs,
                 init_func=None, add_funcs = None, MQTTService=None,
                 GETHandler=None, POSTHandler=None, PUTHandler=None, 
                 DELETEHandler=None, PATCHHandler=None):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.events = events
        
        self.configParams = ["endPointID", "endPointName", "IPAddress", "port", "CRUDMethods"]
        self.CRUDMethods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        try:
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.configs = configs
            self.generalConfigs = generalConfigs

            self.checkInputFunctions(init_func, add_funcs,
                GETHandler, POSTHandler, PUTHandler, 
                DELETEHandler, PATCHHandler
            )

            self.check_and_loadConfigs()

            if("GET" in self.configs["CRUDMethods"].keys() and self.configs["CRUDMethods"]["GET"]) :
                self.GETHandler = GETHandler
                allowedMethods.append("GET")
            if("POST" in self.configs["CRUDMethods"].keys() and self.configs["CRUDMethods"]["POST"]) : 
                self.POSTHandler = POSTHandler
                allowedMethods.append("POST")
            if("PUT" in self.configs["CRUDMethods"].keys() and self.configs["CRUDMethods"]["PUT"]) : 
                self.PUTHandler = PUTHandler
                allowedMethods.append("PUT")
            if("DELETE" in self.configs["CRUDMethods"].keys() and self.configs["CRUDMethods"]["DELETE"]) : 
                self.DELETEHandler = DELETEHandler
                allowedMethods.append("DELETE")
            if("PATCH" in self.configs["CRUDMethods"].keys() and self.configs["CRUDMethods"]["PATCH"]) : 
                self.PATCHHandler = PATCHHandler
                allowedMethods.append("PATCH")

            if(add_funcs != None): self.add_funcs = add_funcs
            if(init_func != None): init_func(self)
            if(MQTTService != None): self.MQTTService = MQTTService

            if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
                if(IN_DOCKER): 
                    self.HADB_path = "DB/HADB.db"
                else:
                    self.HADB_path = "homeAssistant/HADB/HADB.db"    
            
        except HTTPError as e:
            events["stopEvent"].set()
            raise HTTPError(status=e.status, message="An error occurred while enabling REST server: \u0085\u0009" + e._message)
        except Exception as e:
            events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while enabling REST server: \u0085\u0009" + str(e))

    def run(self):
        try:
            print("REST - Thread %s waiting for registration..." % current_thread().ident)
            self.events["startEvent"].wait()

            thread = Thread(target=self.waitStop)
            thread.start()

            self.openRESTServer()            

        except HTTPError as e:
            self.events["stopEvent"].set()
            raise HTTPError(status=e.status, message="An error occurred while running REST server: \u0085\u0009" + e._message)
        except Exception as e:
            self.events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while running REST server: \u0085\u0009" + str(e))
   
    def waitStop(self):
        self.events["stopEvent"].wait()
        cherrypy.engine.exit()
        exit()

    exposed = True

    allowedMethods = []
    @cherrypy_cors.tools.preflight(allowed_methods = allowedMethods)
    def OPTIONS(self, *uri, **params):
        pass

    @cherrypy_cors.tools.expose_public()
    def GET(self, *uri, **params):
        if(self.GETHandler != None):
            return self.GETHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed(message="GET method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def POST(self, *uri, **params):
        if(self.POSTHandler != None):
            return self.POSTHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed(message="POST method is not allowed")
    
    @cherrypy_cors.tools.expose_public()
    def PUT(self, *uri, **params):
        if(self.PUTHandler != None):
            return self.PUTHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed(message="PUT method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def DELETE(self, *uri, **params):
        if(self.DELETEHandler != None):
            return self.DELETEHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed(message="DELETE method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def PATCH(self, *uri, **params):
        if(self.PATCHHandler != None):
            return self.PATCHHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed(message="PATCH method is not allowed")

    def checkInputFunctions(self,init_func, add_funcs,
        GETHandler, POSTHandler, PUTHandler, 
        DELETEHandler, PATCHHandler):
        try:
            if(init_func != None and not callable(init_func)):
                raise self.clientErrorHandler.BadRequest(message="Parameter init_func must be a function")
            
            if(add_funcs != None):
                if(not isinstance(add_funcs, dict)):
                    raise self.clientErrorHandler.BadRequest(message="Parameter add_funcs must be a dictionary")
                if(not all(callable(func) for func in add_funcs.values())):
                    raise self.clientErrorHandler.BadRequest(message="Parameter add_funcs must be a dictionary of functions")
                
            if(GETHandler != None and not callable(GETHandler)):
                raise self.clientErrorHandler.BadRequest(message="Parameter GETHandler must be a function")
            if(POSTHandler != None and not callable(POSTHandler)):
                raise self.clientErrorHandler.BadRequest(message="Parameter POSTHandler must be a function")
            if(PUTHandler != None and not callable(PUTHandler)):
                raise self.clientErrorHandler.BadRequest(message="Parameter PUTHandler must be a function")
            if(DELETEHandler != None and not callable(DELETEHandler)):
                raise self.clientErrorHandler.BadRequest(message="Parameter DELETEHandler must be a function")
            if(PATCHHandler != None and not callable(PATCHHandler)):
                raise self.clientErrorHandler.BadRequest(message="Parameter PATCHHandler must be a function")
        except HTTPError as e:
            raise HTTPError(status=e.status, message = e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while checking input functions: \u0085\u0009" + str(e))
        
    def checkParams(self):
        if(not all(key in self.configParams for key in self.configs.keys())):
            raise self.clientErrorHandler.BadRequest(message="Missing parameters in config file")
        
    def validateParams(self):
        for key in self.configParams:
            match key:
                case ("endPointID" | "endPointName" | "IPAddress"):
                    if(not isinstance(self.configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a string")
                    match key:
                        case "endPointID":
                            self.endPointID = self.configs[key]
                        case "endPointName": self.endPointName = self.configs[key]
                        case "IPAddress":
                            self.IPAddress = self.configs[key]

                            if(not IN_DOCKER and self.IPAddress == "127.0.0.1" or self.IPAddress == "localhost"):
                                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                s.settimeout(0)
                                s.connect(('10.254.254.254', 1))
                                localIP = s.getsockname()[0]
                                #localIP = socket.gethostbyname(socket.gethostname())
                                self.IPAddress = localIP
                            
                            if(IN_DOCKER):
                                DOCKER_IP = os.environ.get("DOCKER_IP", None)
                                if(DOCKER_IP != None):
                                    self.IPAddress = DOCKER_IP
                case "port":
                    if(not isinstance(self.configs[key], int)):
                        raise self.clientErrorHandler.BadRequest(message=key + " parameter must be a integer")
                    self.port = self.configs[key]
                case "CRUDMethods":
                    if(not any(key in self.CRUDMethods for key in self.configs["CRUDMethods"].keys())):
                        raise self.clientErrorHandler.BadRequest(message="At least one CRUD method must be specified")
                    for method in self.CRUDMethods:
                        if(method in self.configs["CRUDMethods"].keys()):
                            if(not isinstance(self.configs["CRUDMethods"][method], bool)):
                                raise self.clientErrorHandler.BadRequest(message=method + " parameter value must be a boolean")
                    self.CRUDMethods = self.configs["CRUDMethods"]        

    def check_and_loadConfigs(self):        
        try:
            self.checkParams()
            self.validateParams()
            
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error ocurred while loading REST configs: " + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error ocurred while loading REST configs: \u0085\u0009" + str(e))

    def getMQTTBroker(self):
        try:
            url = self.generalConfigs["REGISTRATION"]["catalogAddress"] + ":"
            url += str(self.generalConfigs["REGISTRATION"]["catalogPort"])+ "/getInfo"
            params = {
                "table": "EndPoints",
                "keyName": "endPointName",
                "keyValue": "MQTTBroker"
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            return response.json()[0]
        except HTTPError as e:
            raise self.clientErrorHandler.BadRequest(message="An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while getting MQTT broker: \u0085\u0009" + str(e))

    def openRESTServer(self):
        conf={
            '/':{
                "request.dispatch" : cherrypy.dispatch.MethodDispatcher(),
                "request.methods_with_bodies": ("POST", "PUT", "PATCH"),

                "tools.sessions.on" : True,            
                "tools.json_in.on": True
            }
        }

        webServices = self
        cherrypy_cors.install()
        
        cherrypy.config.update({
            'server.socket_host': webServices.IPAddress,
            'server.socket_port': webServices.port,
            'cors.expose.on': True
        })
        
        cherrypy.quickstart(webServices,'/',conf)

    def getMetaHAIDs(self, deviceID):
        if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
            try:
                conn = sq.connect(self.HADB_path)

                deviceID = deviceID.lower()
                query = "SELECT * FROM states_meta WHERE entity_id LIKE '%"+deviceID+"%'"
                selectedData = pd.read_sql_query(query, conn).to_dict(orient="records")
                conn.close()

                result = []
                for data in selectedData:
                    result.append({
                        "metaID": data["metadata_id"],
                        "entityID": data["entity_id"].split(deviceID+"_")[1]
                    })
                
                return result
            except Exception as e:
                raise self.serverErrorHandler.InternalServerError(message="An error occurred while getting Home Assistant IDs: \u0085\u0009" + str(e))
        else:
            raise self.clientErrorHandler.BadRequest(message="Home Assistant is not enabled")

