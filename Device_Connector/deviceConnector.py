import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

from socketHandler import SocketHandler

class DeviceConnector():
    def __init__(self):
        self.baseTopic = "homeassistant/"
        self.system = "smartSockets" #self.system mi fa schifo come termine centra nulla

        self.regSocket_toCatalog = SocketHandler.regSocket_toCatalog # mi salvo queste funzioni
        self.regSocket_toHA = SocketHandler.regSocket_toHA           # perchè utilizzano i metodi
        self.delSocket_fromHA = SocketHandler.delSocket_fromHA       # del servizio

        self.service = ServiceBase("Device_Connector/deviceConnector.json", GET=self.regSocket_toCatalog, init_REST_func=self.REST_init, Notifier=notifier)


    

    