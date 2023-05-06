import os
import time
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
from dataHandler import *

    
def notify(self,topic, payload):
    print("Topic: %s, Payload: %s" % (topic, payload))


     


if __name__ == "__main__":
    a = ServiceBase("test/fraSubFile.json", Notifier = notify)
    a.start()
    clientErrorHandler = Client_Error_Handler()
    topics = [ 'homeassistant/sensor/smartSocket/D1/state'
    ]
    a.MQTT.Subscribe(topics)
    time.sleep(5*10)
    a.MQTT.changeSubTopic(["/ciao/97/1"])

#testare errori:
    #1. accettaere più topic
    #2. autobrocker
    #3. topic non in lista
    #4. wildcards
    while(True):
       pass
       time.sleep(3)
    

   