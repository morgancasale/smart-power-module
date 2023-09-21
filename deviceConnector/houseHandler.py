import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.Error_Handler import *

class HouseHandler():
    def genHouseSensor(self, houseID):
        try:
            house = {}
            house["houseID"] = houseID

            house["Resources"] = HouseHandler.getHouseResources(houseID)
            house["endPoints"] = HouseHandler.getHouseEndPoints(houseID)

            return house
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while generating house sensor" + str(e)
            )
        
    def getHouseResources(houseID):
        return [
            {
                "resourceID": "cioa"
            }
        ]