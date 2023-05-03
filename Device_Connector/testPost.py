import cherrypy


from ServiceComponent1 import *

class WebPage(object):
    exposed = True
    
   
    def POST (self,*uri,**params):
         mystring = "POST response\n"
         mystring += ("URI: %s; PARAMS: %s" % (str(uri), str(params)))
         mystring += ("BODY: %s" % cherrypy.request.body.read())
         return mystring
if __name__ == "__main__":
    #Standard configuration to serve the url "localhost:8080"
    conf={
        '/':{
            'request.dispatch' : cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on' : True
        }
    }
    webService=WebPage()
    cherrypy.tree.mount(webService,'/',conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
   