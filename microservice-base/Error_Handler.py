class web_exception(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

class Error_Handler:
    def __init__(self, error):
        pass

    def webErrorNotImplemented():
        return 402
    
    def MissingDataError(msg):
        return web_exception(403, msg)