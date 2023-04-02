import cherrypy
import cherrypy_cors
import json

from threading import Thread

from Error_Handler import *

class RESTServer(Thread):
    def __init__(self, threadID, threadName, configs, init_func=None, GETHandler=None, POSTHandler=None, PUTHandler=None, DELETEHandler=None, PATCHHandler=None):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        
        self.crud_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        try:
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()
            self.configs = configs

            self.check_and_loadConfigs()

            if("GET" in self.configs["crud"] and self.configs["crud"]["GET"]) : self.GETHandler = GETHandler
            if("POST" in self.configs["crud"] and self.configs["crud"]["POST"]) : self.POSTHandler = POSTHandler
            if("PUT" in self.configs["crud"] and self.configs["crud"]["PUT"]) : self.PUTHandler = PUTHandler
            if("DELETE" in self.configs["crud"] and self.configs["crud"]["DELETE"]) : self.DELETEHandler = DELETEHandler
            if("PATCH" in self.configs["crud"] and self.configs["crud"]["PATCH"]) : self.PATCHHandler = PATCHHandler

            if(init_func != None): init_func()

            
            
        except web_exception as e:
            raise web_exception(e.code, "An error occurred while enabling REST server: \n\t" + e.message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while enabling REST server: \n\t" + str(e))

    def run(self):
        self.openRESTServer()

    exposed = True    

    @cherrypy_cors.tools.preflight(allowed_methods=["GET", "DELETE", "POST", "PUT", "PATCH"])
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
        config_params = ["address", "port", "crud"]

        if(not all(key in config_params for key in self.configs.keys())):
            raise self.clientErrorHandler.BadRequest("Misssing parameters in config file")
        
        if(not any(key in self.crud_methods for key in self.configs["crud"].keys())):
            raise self.clientErrorHandler.BadRequest("At least one CRUD method must be specified")
        
    def validateParams(self):
        if(not isinstance(self.configs["address"], str)):
            raise self.clientErrorHandler.BadRequest("Address parameter must be a string")
        
        if(not isinstance(self.configs["port"], int)):
            raise self.clientErrorHandler.BadRequest("Port parameter must be a integer")
        
        for method in self.crud_methods:
            if(method in self.configs["crud"].keys()):
                if(not isinstance(self.configs["crud"][method], bool)):
                    raise self.clientErrorHandler.BadRequest(method + " parameter value must be a boolean")
        

    def check_and_loadConfigs(self):        
        try:
            self.checkParams()
            self.validateParams()
            
        except web_exception as e:
            raise web_exception(e.code, "An error ocurred while loading REST configs: " + e.message)
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
            'server.socket_host': webServices.configs["address"],
            'server.socket_port': webServices.configs["port"],
            'cors.expose.on': True
        })
        
        cherrypy.quickstart(webServices,'/',conf)

