from app import *
import json
import datetime as datetime
import threading
import os
import time
import sys
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *

client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/dataGenerationAndElimination/res_catalog_serviceConfig.json")

json_data = json.load(open('dataGenerationAndElimination\res_catalog_serviceConfig.json', 'r'))
catalog_address = json_data['REST']['IPAddress']
catalog_port = json_data['REST']['port']

url="http://%s:%s/getInfo"%(catalog_address, str(catalog_port))
params={
   "table" : "EndPoints",
   "keyName" : "endPointName",
   "keyValue" : "deviceConnector"
}  

response = requests.get(url, params=params)


response = response.json()[0]
endpoint = response
ip_address = endpoint.get('IPAddress')
port = endpoint.get('port')

url_dc= "http://" + str(ip_address)+ ":" + str(port) + "/getRole"
params_dc={
            "MAC": "67:5A:8E:7B:4C:9J",
            "autoBroker": "true",
            "autoTopics": "true"
}  
requests.get(url_dc, params=params_dc)







