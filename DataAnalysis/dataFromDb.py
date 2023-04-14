import requests
from pprint import pprint
import json

class DBRequest:
    def __init__(self):
        pass

    def generate_request(self, cmd, param):
        response = requests.get("http://localhost:8080/" + cmd, params = param)
        return response

    def print_response(self):
        responseDict = json.loads(self.getResponse.text)
        pprint(responseDict, indent = 4)

    def generate_Put_request(self, cmd, param):
        response = requests.put("http://localhost:8080/" + cmd, json = param)
        return response


    def getData(self,num_function,otherdata):
        match num_function:
                case 1:
                    allData=self.generate_request("getAlldb/"+ otherdata,{"op" : None})
                    return allData
            
                case 2:
                    allData=self.generate_request("getAllbyDay/"+ otherdata,{"op" : None})              
                    return allData
                
                case 3:
                    allData=self.generate_request("getAllbyMonth/"+ otherdata,{"op" : None})              
                    return allData
             
                case 4:
                    allData=self.generate_request("getAllbyYear/"+ otherdata,{"op" : None})              
                    return allData
                
                case 5:
                    allData=self.generate_request("getHourlyDatabyHouseID/"+otherdata,{"op" : None})

                case 6:
                    allData=self.generate_request("getDailyDatabyHouseID/"+otherdata,{"op" : None})    
                
                case 7:
                    allData=self.generate_request("getMonthlyDatabyHouseID/"+otherdata,{"op" : None})    

                case 8:
                    allData=self.generate_request("getYearlyDatabyHouseID/"+otherdata,{"op" : None})        

                case _:
                    print("Invalid command")
                    err = True

    def putData(self,num_function,bodydata):       
         match num_function:
                case 1:
                    allData=self.generate_Put_request("putTest",bodydata)                
                    return allData     
                
                case 2:
                    allData=self.generate_Put_request("putTest2",bodydata)                
                    return allData   
                
                case 3:
                    allData=self.generate_Put_request("putTest3",bodydata)                
                    return allData   
                
                case 4:
                    allData=self.generate_Put_request("putTest4",bodydata)                
                    return allData  

                case _:
                    print("Invalid command")
                    err = True