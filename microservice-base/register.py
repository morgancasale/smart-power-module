import requests
import time

def KeepAlive(self):
        while True:
            try:
                requests.put(self.configs["ResourceCatalogAddress"] + "/setService", {})
            except Exception as e:
                raise e
            time.sleep(5*60)