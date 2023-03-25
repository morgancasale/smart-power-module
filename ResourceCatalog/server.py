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

    def GET(self, *uri, **params):
        try:
            return self.resourceCatalog.handleGetRequest(uri[0], [params])
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)

    def POST(self, *path):
        try:
            return self.resourceCatalog.handlePostRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)

    def PUT(self, *path):
        try:
            return self.resourceCatalog.handlePutRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)
    
    def PATCH(self, *path):
        try:
            return self.resourceCatalog.handlePatchRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)

    def DELETE(self, *path):
        try:
            self.resourceCatalog.handleDeleteRequest(path[0], cherrypy.request.json)
        except web_exception as e:
            raise cherrypy.HTTPError(e.code, e.message)


def start_webpage():
    #Standard configuration to serve the url "localhost:8080"
    conf={
        '/':{
            'request.dispatch' : cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True,
            "tools.json_in.on": True,
            "request.methods_with_bodies": ("POST", "PUT", "PATCH", "DELETE"),
        }
    }
    webService = ResourceCatalog_server("db.sqlite")
    cherrypy.tree.mount(webService,'/',conf)
    cherrypy_cors.install()
    cherrypy.config.update({
        'server.socket_host' : '192.168.2.145',
        'server.socket_port': 8099,
        'cors.expose.on': True
        })
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == "__main__":
    start_webpage()
