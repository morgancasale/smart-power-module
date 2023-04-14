import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

a = ServiceBase("ResourceCatalog/serviceConfingFRA.json", )

if __name__ == "__main__":

    while(True):
        a.MQTT.publish("/bro/99/1", "ciao")
        time.sleep(3)