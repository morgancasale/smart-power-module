import cherrypy
import connect_db as cdb
import API
from serviceBase import ServiceBase

class Server():
    exposed = True
    connessione=cdb.Connect("Data_DB/testDB.db")

    def GET(self, *uri):        
        apiConn=API.api_server(self.connessione)
        result= apiConn.handleRequestGET(uri[0],uri[1])
        return result
    
    def POST(self, *uri):
       apiConn=API.api_server(self.connessione)
       result=apiConn.handlePostRequest(uri[0])
       return result       
    
    def PUT(self, *uri):
       apiConn=API.api_server(self.connessione)
       result=apiConn.handlePutRequest(uri[0], cherrypy.request.json)
       return result    
    
if __name__ == "__main__":
    # Standard configuration to serve the url "localhost:8080"    
    server = ServiceBase("serviceConfig_example.json", GET=GET(), POST=POST())