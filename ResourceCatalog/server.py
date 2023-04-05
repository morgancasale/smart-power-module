import cherrypy
import cherrypy_cors
import os
from resourceCatalog import *

class ResourceCatalog_server(object):
    def __init__(self, DBPath):
        if(not os.path.isfile(DBPath)):
            raise cherrypy.HTTPError(400, "Database file not found")
    
        self.resourceCatalog = ResourceCatalog(DBPath)

    exposed=True
    
    @cherrypy_cors.tools.preflight(allowed_methods=["GET", "DELETE", "POST", "PUT", "PATCH"])
    def OPTIONS(self, *uri, **params):
        pass
    
    @cherrypy_cors.tools.expose_public()
    def GET(self, *uri, **params):
        try:
            return self.resourceCatalog.handleGetRequest(uri[0], [params])
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)

    @cherrypy_cors.tools.expose_public()
    def POST(self, *path):
        try:
            return self.resourceCatalog.handlePostRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)
    
    #@cherrypy_cors.tools.expose_public()
    def PUT(self, *path):
        try:
            return self.resourceCatalog.handlePutRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)
    
    @cherrypy_cors.tools.expose_public()
    def PATCH(self, *path):
        try:
            return self.resourceCatalog.handlePatchRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)

    @cherrypy_cors.tools.expose_public()
    def DELETE(self, *path):
        try:
            self.resourceCatalog.handleDeleteRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)


def start_webpage():
    conf={
        '/':{
            'request.dispatch' : cherrypy.dispatch.MethodDispatcher(),
            "request.methods_with_bodies": ("POST", "PUT", "PATCH", "DELETE"),

            'tools.sessions.on' : True,            
            "tools.json_in.on": True
        }
    }
    webService = ResourceCatalog_server("db.sqlite")
    cherrypy_cors.install()

    cherrypy.config.update({
        'server.socket_host' : '192.168.2.145',
        'server.socket_port': 8099,
        'cors.expose.on': True
    })

    cherrypy.quickstart(webService,'/',conf)

if __name__ == "__main__":
    start_webpage()
