import requests
from pprint import pprint
import json

class DBRequest:
    def __init__(self):
        pass

    def generate_request(self, cmd, param):
        response = requests.get("http://localhost:8080/" + cmd, params = param)
        return response
    
    def patch_request(self, cmd, param):
        response = requests.patch("http://localhost:8080/" + cmd, params = param)
        return response

    def print_response(self):
        responseDict = json.loads(self.getResponse.text)
        pprint(responseDict, indent = 4)


    def getData(self,num_function,passed_data):
        match num_function:
                case 1:
                    allData=self.generate_request("getlastPower/"+passed_data,{"op" : None})                
                    return allData
                    
                case 2:
                    allData=self.generate_request("getMaxPowerHouse/"+passed_data,{"op" : None})                            
                    return allData
                    
                case 3:
                    allData=self.generate_request("getAlldbbyID/"+passed_data,{"op" : None})
                    return allData
                    
                case 4:
                    allData=self.generate_request("getLastUpdate/"+passed_data,{"op" : None})
                    return allData                
                    
                case _:
                    print("Invalid command")
                    err = True
                    
    def updateData(self,num_function,passed_data):       
         match num_function:
                case 1:
                    allData=self.patch_request("updateModule/"+passed_data,{"op" : None})                
                    return allData     
                case _:
                    print("Invalid command")
                    err = True    
