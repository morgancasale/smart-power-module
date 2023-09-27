import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from colorama import Fore

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import * 

class ServicesTracker():
    def __init__(self):
        configFile_loc = "onlineTracker.json"
        if(not IN_DOCKER):
            configFile_loc = "onlineTracker/" + configFile_loc
        
        self.service = ServiceBase(configFile_loc)

        catalogAddress = self.service.generalConfigs["REGISTRATION"]["catalogAddress"]
        catalogPort = self.service.generalConfigs["REGISTRATION"]["catalogPort"]

        self.service.start()

        self.OnlineStatusTracker(catalogAddress, catalogPort)

    def OnlineStatusTracker(self, catalogAddress, catalogPort):
        try:
            while True:
                watchDogTimer = 5*60

                url = "%s:%s/updateOnlineStatus"%(catalogAddress, catalogPort)
                params = [
                    {"table" : "Services", "timer" : watchDogTimer},
                    {"table" : "Devices", "timer" : watchDogTimer}, 
                    {"table" : "DeviceResource_conn", "timer" : watchDogTimer},
                    {"table" : "DeviceSettings", "timer" : watchDogTimer}
                ]

                headers = {"Content-Type" : "application/json"}
                response = requests.patch(url, headers=headers, data=json.dumps(params))
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, response.text)
                
                print(Fore.LIGHTGREEN_EX + "Online status Tracker:\n\t" + response.text + Fore.RESET)

                time.sleep(watchDogTimer)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while updating devices online status" + str(e)
            )
        
if __name__ == "__main__":
    ServicesTracker()