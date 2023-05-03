import cherrypy


from ServiceComponent1 import *

class WebPage(object):
    exposed = True
    
   
    def POST (self,*uri,**params):
         output = "POST response: \n"
         output += ("BODY: %s" % cherrypy.request.body.read())
         return output
         
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
   