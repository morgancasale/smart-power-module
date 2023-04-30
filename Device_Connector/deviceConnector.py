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
         
        self.regSocket_toCatalog = SocketHandler.giveRole_toSocket # mi salvo queste funzioni 
        self.regSocket_toHA = SocketHandler.regSocket_toHA         # perchè utilizzano i metodi
        self.delSocket_fromHA = SocketHandler.delSocket_fromHA     # del servizio

        notifier = None

        self.service = ServiceBase("Device_Connector/deviceConnector.json", GET=self.regSocket_toCatalog, Notifier=notifier)

        self.service.start()


service = DeviceConnector()

    