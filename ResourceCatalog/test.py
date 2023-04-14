import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
from cherrypy import HTTPError

#a = ServiceBase("ResourceCatalog/serviceConfig.json")


try:
    raise HTTPError(status=500, message="errore")
except HTTPError as e:
    print(e.status)
    print(e._message)
except Exception as e:
    print("errore generico")

b = []

for c in b:
    print("cciao")