from cherrypy import HTTPError
class Client_Error_Handler:
    '''def __init__(self):
        pass'''
    def BadRequest(self=None, message=None):
        #errore di sintassi nella richiesta
        return HTTPError(status=400, message=message)
    def Unauthorized(self=None, message=None):
        #non sei autenticato come cliente
        return HTTPError(status=401, message=message)
    def Forbidden(self=None, message=None):
        #non sei autorizzato a fare questa richiesta
        return HTTPError(status=403, message=message)
    def NotFound(self=None, message=None):
        #non esiste la risorsa richiesta
        return HTTPError(status=404, message=message)
    def MethodNotAllowed(self=None, message=None):
        #client non autorizzato ad usare il metodo specificato
        return HTTPError(status=405, message=message)
    # def NotAcceptable(message):
    #     #tu non accetti il formato della risposta
    #     return HTTPError(406, message)
   
    def RequestTimeout(self=None, message=None):
        #server utilizza troppo tempo per richiesta quindi ciao
        return HTTPError(status=408, message=message)

    def ImATeapot(self=None):
        return HTTPError(status=418, message="The server refuses the attempt to brew coffee with a teapot, God save the Queen!")                             
    
    def TooManyRequests(self=None, message=None):
        #server non può gestire troppe richieste insieme
        return HTTPError(status=429, message=message)

class Server_Error_Handler:
    '''def __init__(self):
        pass'''
    def InternalServerError(self=None, message=None):
        #errore interno del server inaspettato
        return HTTPError(status=500, message=message)
    def NotImplemented(self=None, message=None):
        #server non può eseguire la richiesta, nome sbagliato o metodo non supportato
        return HTTPError(status=501, message=message)
    def ServiceUnavailable(self=None, message=None):
        #server non può eseguire la richiesta, fserver not ready is down or overloaded
        return HTTPError(status=503, message=message)
    
