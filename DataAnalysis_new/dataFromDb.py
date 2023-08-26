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
                    hourly_data=self.generate_request("gethourlydata/"+ otherdata,{"op" : None})              
                    return hourly_data
                case 3:
                    daily_data=self.generate_request("getdailydata/"+ otherdata,{"op" : None})              
                    return daily_data
                case 4:
                    monthly_data=self.generate_request("getmonthlydata/"+ otherdata,{"op" : None})              
                    return monthly_data
                case 5:
                    yearly_data=self.generate_request("getyearlydata/"+ otherdata,{"op" : None})              
                    return yearly_data
                case 6:
                    house_hdata=self.generate_request("gethourlydata_byhouseID/"+ otherdata,{"op" : None})              
                    return house_hdata
                case 7:
                    house_ddata=self.generate_request("getdailydata_byhouseID/"+ otherdata,{"op" : None})              
                    return house_ddata
                case 8:
                    house_mdata=self.generate_request("getmonthlydata_byhouseID/"+ otherdata,{"op" : None})              
                    return house_mdata
                case 9:
                    house_ydata=self.generate_request("getyearlydata_byhouseID/"+ otherdata,{"op" : None})              
                    return house_ydata
                case 10:
                    houses_list=self.generate_request("gethouses_list/"+ otherdata,{"op" : None})              
                    return houses_list
                case _:
                    print("Invalid command")
                    err = True

    def putData(self,num_function,bodydata):       
        match num_function:
                case 1:
                    allData=self.generate_Put_request("putData",bodydata)                
                    return allData     
                case _:
                    print("Invalid command")
                    err = True