from cherrypy import HTTPError
class Client_Error_Handler:
    def __init__(self):
        pass
    def BadRequest(self, msg):
        #errore di sintassi nella richiesta
        return HTTPError(status=400, message=msg)
    def Unauthorized(self, msg):
        #non sei autenticato come cliente
        return HTTPError(status=401, message=msg)
    def Forbidden(self, msg):
        #non sei autorizzato a fare questa richiesta
        return HTTPError(status=403, message=msg)
    def NotFound(self, msg):
        #non esiste la risorsa richiesta
        return HTTPError(status=404, message=msg)
    def MethodNotAllowed(self, msg):
        #client non autorizzato ad usare il metodo specificato
        return HTTPError(status=405, message=msg)
    # def NotAcceptable(msg):
    #     #tu non accetti il formato della risposta
    #     return HTTPError(406, msg)
   
    def RequestTimeout(self, msg):
        #server utilizza troppo tempo per richiesta quindi ciao
        return HTTPError(status=408, message=msg)

    def ImATeapot():
        
        return HTTPError(status=418, message="The server refuses the attempt to brew coffee with a teapot, God save the Queen!")                             
    
    def TooManyRequests(self, msg):
        #server non può gestire troppe richieste insieme
        return HTTPError(status=429, message=msg)

class Server_Error_Handler:
    def __init__(self):
        pass
    def InternalServerError(self, msg):
        #errore interno del server inaspettato
        return HTTPError(status=500, message=msg)
    def NotImplemented(self, msg):
        #server non può eseguire la richiesta, nome sbagliato o metodo non supportato
        return HTTPError(status=501, message=msg)
    def ServiceUnavailable(self, msg):
        #server non può eseguire la richiesta,server not ready is down or overloaded
        return HTTPError(status=503, message=msg)
    
