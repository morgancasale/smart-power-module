import cherrypy
import json
import Error_Handler

class RESTServer(object):
    def __init__(self, config_file, init_func=None, GET=None, POST=None, PUT=None, DELETE=None, PATCH=None):
        self.crud_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        try:
            self.errorHandler = Error_Handler()
            self.config_file = config_file

            self.check_and_loadConfigs()

            if(self.configs["Active"]):
                if(self.configs["crud"]["GET"]) : self.GET = GET
                if(self.configs["crud"]["POST"]) : self.POST = POST
                if(self.configs["crud"]["PUT"]) : self.PUT = PUT
                if(self.configs["crud"]["DELETE"]) : self.DELETE = DELETE
                if(self.configs["crud"]["PATCH"]) : self.PATCH = PATCH

                init_func()
            
        except Exception as e:
            print(e)

    exposed = True

    def checkParams(self):
        config_params = ["active", "port", "crud"]

        if(not all(key in config_params for key in self.configs.keys())):
            raise self.errorHandler.MissingDataError("Misssing parameters in config file")
        
        if(not any(key in self.crud_methods for key in self.configs["crud"].keys())):
            raise self.errorHandler.MissingDataError("At least one CRUD method must be enabled")
        
    def validateParams(self):
        if(not isinstance(self.configs["active"], bool)):
            raise self.errorHandler.MissingDataError("Active parameter must be a boolean")
        
        if(not isinstance(self.configs["port"], int)):
            raise self.errorHandler.MissingDataError("Port parameter must be a integer")
        
        for method in self.crud_methods:
            if(method in self.configs["crud"].keys()):
                if(not isinstance(self.configs["crud"][method], bool)):
                    raise self.errorHandler.MissingDataError(method + " parameter must be a boolean")
        

    def check_and_loadConfigs(self): # TODO chek if file exists, check if all needed configs are there
        
        try:
            configs = json.load(open(self.config_file, 'r'))

            self.configs = configs["REST"]
            self.checkParams()
            self.validateParams()



        except Exception as e:
            print(e)

    

def openRESTServer(config_file, init_func, GET=None, POST=None, PUT=None, DELETE=None, PATCH=None):
    conf = {
        '/':{
            'request.dispatch' : cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True,
            "tools.json_in.on": True,
            "request.methods_with_bodies": ("POST", "PUT", "PATCH", "DELETE"),
        }
    }

    webServices = RESTServer(config_file, init_func, GET=GET, POST=POST, PUT=PUT, DELETE=DELETE, PATCH=PATCH)

    if(webServices.configs["Active"]):
        cherrypy.tree.mount(webServices, '/', conf)
        cherrypy.config.update({'server.socket_port': webServices.configs["REST"]["port"]})
        cherrypy.engine.start()
        cherrypy.engine.block()

