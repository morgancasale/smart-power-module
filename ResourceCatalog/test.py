import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

a = ServiceBase("ResourceCatalog/serviceConfig.json")

clientErrorHandler = Client_Error_Handler()

print("!")