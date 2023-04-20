import os
import time
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

    
def notify(topic, payload):
    print("Topic: %s, Payload: %s" % (topic, payload))


     


if __name__ == "__main__":
    a = ServiceBase("test/fraSubFile.json", Notifier = notify)
    a.start()
    clientErrorHandler = Client_Error_Handler()
    topics = [    "/+/+/1",
    ]
    time.sleep(5)
    a.MQTT.subscribe(topics)

#testare errori:
    #1. accettaere più topic
    #2. autobrocker
    #3. topic non in lista
    #4. wildcards
    while(True):
       pass
       time.sleep(3)
    

   