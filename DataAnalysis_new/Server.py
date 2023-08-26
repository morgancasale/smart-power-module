import cherrypy
import connect_db as cdb
import APIs

class Server():
    exposed = True
    connessione=cdb.Connect("Data_DB/testDB.db")

    def GET(self, *uri):        
        apiConn=APIs.api_server(self.connessione)
        result= apiConn.handleRequestGET(uri[0],uri[1])
        return result
        
    def PUT(self, *uri):
        apiConn=APIs.api_server(self.connessione)
        result=apiConn.handlePutRequest(uri[0], cherrypy.request.json)
        return result    


if __name__ == "__main__":
    # Standard configuration to serve the url "localhost:8080"
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True,
            "tools.json_in.on": True,
            "request.methods_with_bodies": ( "PUT", "PATCH", "DELETE")
        }
    }
    webService = Server()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
#Per provare microservice base    
# if __name__ == "__main__":
#     # Standard configuration to serve the url "localhost:8080"    
#     server = ServiceBase("serviceConfig_example.json", GET=GET(), POST=POST(), PUT=PUT())
