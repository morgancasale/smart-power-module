import os
import time
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

    
def notify(self, topic, payload):
    print("Topic: %s, Payload: %s" % (topic, payload))


     
a = ServiceBase("ResourceCatalog/fraSubFile.json",Notifier = notify)

clientErrorHandler = Client_Error_Handler()

a.MQTT.subscribe("/bro/#")

if __name__ == "__main__":
    while(True):
       pass
       time.sleep(3)
    

   