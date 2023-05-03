import json

class ESP_data():
    def loadDevice(self):
        with open('device.json', 'r+') as f:
            self.data = json.load(f)
