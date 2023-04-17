import os
import time
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

    
def notify(topic, payload):
    print("Topic: %s, Payload: %s" % (topic, payload))


     
a = ServiceBase("test/service_test.json", Notifier = notify)

while(True):
    a.MQTT.publish("/test/pub/1", "ciao")
    time.sleep(10)
