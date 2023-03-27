class web_exception(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

class Client_Error_Handler:
    def __init__(self):
        pass
    def BadRequest(msg):
        #errore di sintassi nella richiesta
        return web_exception(400, msg)
    def Unauthorized(msg):
        #non sei autenticato come cliente
        return web_exception(401, msg)
    def Forbidden(msg):
        #non sei autorizzato a fare questa richiesta
        return web_exception(403, msg)
    def NotFound(msg):
        #non esiste la risorsa richiesta
        return web_exception(404, msg)
    def MethodNotAllowed(msg):
        #client non autorizzato ad usare il metodo specificato
        return web_exception(405, msg)
    # def NotAcceptable(msg):
    #     #tu non accetti il formato della risposta
    #     return web_exception(406, msg)
   
    def RequestTimeout(msg):
        #server utilizza troppo tempo per richiesta quindi ciao
        return web_exception(408, msg)

    def ImATeapot():
        
        return web_exception(418, "The server refuses the attempt to brew coffee with a teapot, God save the Queen!")                             
    
    def TooManyRequests(msg):
        #server non può gestire troppe richieste insieme
        return web_exception(429, msg)

class Server_Error_Handler:
    
    def __init__(self):
        pass
    def InternalServerError(msg):
        #errore interno del server inaspettato
        return web_exception(500, msg)
    def NotImplemented(msg):
        #server non può eseguire la richiesta, nome sbagliato o metodo non supportato
        return web_exception(501, msg)
    def ServiceUnavailable(msg):
        #server non può eseguire la richiesta,server not ready is down or overloaded
        return web_exception(503, msg)
    
