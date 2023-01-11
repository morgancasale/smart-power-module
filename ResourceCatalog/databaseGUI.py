from device import *
import requests
from pprint import pprint
import json

class DatabaseGUI:
    def __init__(self):
        pass

    def generate_request(self, cmd, param):
        self.getResponse = requests.get("http://localhost:8080/" + cmd, params = param)

    def print_response(self):
        responseDict = json.loads(self.getResponse.text)
        pprint(responseDict, indent = 4)

    def menu(self):
        err = True
        while err:
            err = False
            print('''Choose operation from the list: 
            1. Get all Devices
            2. Search Device by deviceID
            3. Register new Device
            4. Get all Users
            5. Search User by userID
            6. Register new User
            7. exit
            Choice: ''')
            choice = input()

            match choice:
                case "1":
                    self.generate_request("getAllDevices", {"op" : None})
                case "2":
                    print("Enter deviceID: ")
                    self.generate_request("getDeviceByID", {"op" : input()})
                case "3":
                    print("Enter new device data: ")
                    self.generate_request("regDevice", {"op" : input()})
                case "4":
                    self.generate_request("getAllUsers", {"op" : None})
                case "5":
                    print("Enter userID: ")
                    self.generate_request("getUserByID", {"op" : input()})
                case "6":
                    print("Enter new user data: ")
                    self.generate_request("regUser", {"op" : input()})   

                case ["exit", "7"]:
                    exit()

                case _:
                    print("Invalid command")
                    err = True