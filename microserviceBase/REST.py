import cherrypy
import cherrypy_cors
import json

from threading import Thread
from queue import Queue
import ctypes


from .Error_Handler import *

class RESTServer(Thread):
    global allowedMethods

    def __init__(self, threadID, threadName, startQueue, configs, init_func=None, GETHandler=None, POSTHandler=None, PUTHandler=None, DELETEHandler=None, PATCHHandler=None):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.startQueue = startQueue
        
        self.configParams = ["endPointID", "endPointName", "IPAddress", "port", "CRUDMethods"]
        self.CRUDMethods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        try:
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.configs = configs

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

            if(init_func != None): init_func()

            
            
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while enabling REST server: \n\t" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while enabling REST server: \n\t" + str(e))

    def run(self):
        print("REST - Waiting for registration...")
        self.startQueue.get()
        self.openRESTServer()

    def stopAllThreads(self):
        for thread_id in [1,3]:
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print('Exception raise failure')

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
            raise self.clientErrorHandler.MethodNotAllowed("GET method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def POST(self, *uri, **params):
        if(self.POSTHandler != None):
            return self.POSTHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed("POST method is not allowed")
    
    @cherrypy_cors.tools.expose_public()
    def PUT(self, *uri, **params):
        if(self.PUTHandler != None):
            return self.PUTHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed("PUT method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def DELETE(self, *uri, **params):
        if(self.DELETEHandler != None):
            return self.DELETEHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed("DELETE method is not allowed")
        
    @cherrypy_cors.tools.expose_public()
    def PATCH(self, *uri, **params):
        if(self.PATCHHandler != None):
            return self.PATCHHandler(self, *uri, **params)
        else:
            raise self.clientErrorHandler.MethodNotAllowed("PATCH method is not allowed")

    def checkParams(self):
        if(not all(key in self.configParams for key in self.configs.keys())):
            raise self.clientErrorHandler.BadRequest("Missing parameters in config file")
        
    def validateParams(self):
        for key in self.configParams:
            match key:
                case ("endPointID", "endPointName", "IPAddress"):
                    if(not isinstance(self.configs[key], str)):
                        raise self.clientErrorHandler.BadRequest(key + " parameter must be a string")
                case "port":
                    if(not isinstance(self.configs[key], int)):
                        raise self.clientErrorHandler.BadRequest(key + " parameter must be a integer")
                case "CRUDMethods":
                    if(not any(key in self.CRUDMethods for key in self.configs["CRUDMethods"].keys())):
                        raise self.clientErrorHandler.BadRequest("At least one CRUD method must be specified")
                    for method in self.CRUDMethods:
                        if(method in self.configs["CRUDMethods"].keys()):
                            if(not isinstance(self.configs["CRUDMethods"][method], bool)):
                                raise self.clientErrorHandler.BadRequest(method + " parameter value must be a boolean")        

    def check_and_loadConfigs(self):        
        try:
            self.checkParams()
            self.validateParams()
            
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error ocurred while loading REST configs: " + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error ocurred while loading REST configs: \n\t" + str(e))

    

    def openRESTServer(self):
        conf={
            '/':{
                "request.dispatch" : cherrypy.dispatch.MethodDispatcher(),
                "request.methods_with_bodies": ("POST", "PUT", "PATCH", "DELETE"),

                "tools.sessions.on" : True,            
                "tools.json_in.on": True
            }
        }

        webServices = self
        cherrypy_cors.install()
        
        cherrypy.config.update({
            'server.socket_host': webServices.configs["IPAddress"],
            'server.socket_port': webServices.configs["port"],
            'cors.expose.on': True
        })
        
        cherrypy.quickstart(webServices,'/',conf)
