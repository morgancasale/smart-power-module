import cherrypy
import connect_db as cdb
import APIs

class Server():
    exposed = True
    connessione=cdb.Connect("Data_DB/data.db")

    def GET(self, *uri):        
        apiConn=APIs.api_server(self.connessione)
        result= apiConn.handleRequestGET(uri[0],uri[1])
        return result


if __name__ == "__main__":
    # Standard configuration to serve the url "localhost:8080"
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    webService = Server()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
