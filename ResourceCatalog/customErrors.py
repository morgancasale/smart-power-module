class web_exception(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class web_exception(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)