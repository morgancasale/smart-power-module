import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *



if __name__ == "__main__":
    service = ServiceBase("test/fraPubFile.json")
    service.start()
#testare errori:
 #1. non accettaere più topic
 #2. autobrocker
 #3. topic non in lista
    topics = ["/bro/99/1", "/morgy/99/1", "/ciao/97/1", "/bro/97/1"]
    while(True):
     
        time.sleep(5)
        service.MQTT.publish("/bro/99/1", "1")
        time.sleep(5)
        service.MQTT.publish("/morgy/99/1", "2")
        time.sleep(5)
        service.MQTT.publish("/ciao/97/1", "3")
        time.sleep(5)
        service.MQTT.publish("/bro/97/1", "4")
        time.sleep(10)