import os
import time
import sys
IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

import sqlite3
import json
import pandas as pd
import requests

from microserviceBase.serviceBase import *

class DataAnalysis():

    def __init__(self): 
        try:
            config_file = "dataAnalysis.json"
            if(not IN_DOCKER):
                config_file = "dataAnalysis/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()
            
            self.sample_min = 10 

            HADB_loc = "homeAssistant/HADB/HADB.db"

            self.HADBConn = sqlite3.connect(HADB_loc)
            self.HADBCur = self.HADBConn.cursor()       
            
            while(True): 
                self.processdata()
                time.sleep(self.sample_min*60)

        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    
    """Retrieves information about devices registered in the catalog and selects only those "online" """
    def getOnlineDevicesInfo(self):
        try:    
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "Devices", "keyName": "deviceID", "keyValue": "*"}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            dev_online = [device for device in result if device["Online"]]
            return dev_online
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    
    """Retrieves the "online" devices associated with a particular house"""
    def getHouseDevList(self,houseID):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseDev_conn", "keyName": "houseID", "keyValue": houseID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            devices = self.getOnlineDevicesInfo()

            dev_online_list = set(device['deviceID'] for device in devices)
            house_onlinedev = [device for device in result if device['deviceID'] in dev_online_list]
            house_onlinedev_list = []
            for row in house_onlinedev:
                house_onlinedev_list.append((row["houseID"], row["deviceID"])) 
            return house_onlinedev_list
        
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

    """For each online device belonging to a specific home, it finds the associated metadata_ids.
    If the considered device is switched on, then it retrieves the metadata_id of the energy measurement 
    (basic,hourly,daily,... according to the 'attribute') for that device."""
    def selectMetaHAIDs(self,houseID,attribute):
        house_devices= self.getHouseDevList(houseID)
        devices_list=[]
        selectedMetaHAIDs=[] 
        for element in house_devices:
            devices_list.append(element[1])        
        for dev_id in devices_list:
            meta_data = self.client.getMetaHAIDs(dev_id)
            metaHAID=meta_data[attribute]
            selectedMetaHAIDs.append(metaHAID)
        return selectedMetaHAIDs
        
    """Gets the device_id from the metadata_id """
    def getDeviceID(self, metaHAID,s_measure):
        try:
            query = "SELECT entity_id FROM states_meta WHERE metadata_id = ?"
            self.HADBCur.execute(query,(metaHAID,))
            rows = self.HADBCur.fetchall()    
            if rows:
                entity_id = rows[0][0]
                parts = entity_id.split(".")
                if s_measure:
                    deviceID = (parts[1].split("_")[-3].title())
                else:
                    deviceID=(parts[1].split("_")[-2].title())
                return deviceID
        except HTTPError as e:
                message = "An error occurred while retriving info from catalog " + e._message
                raise HTTPError(status=e.status, message=message)
        except Exception as e:
                message = "An error occurred while retriving info from catalog " + str(e)
                raise Server_Error_Handler.InternalServerError(message=message)    
                
    """Calculates the statistics (average or sum of consumption) and an estimate of the cost for each device according to the input parameters."""
    def compute_data(self, df, time_format, avg, statistic_format,sm):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime(time_format)
        df['state'] = df['state'].astype(float)   
        if avg == True:
            result=df.groupby(['metadata_id', 'formatted_timestamp'])['state'].mean().reset_index()  
        else:
            result = df.groupby(['metadata_id', 'formatted_timestamp'])['state'].sum().reset_index()       
        if not result.empty:
            for i in range(len(result)):
                deviceID = self.getDeviceID(int(result['metadata_id'][i]), sm).lower()
                topic='homeassistant/sensor/smartSocket/%s/state' % deviceID

                msg='{"energy_%s": %f}' % (statistic_format, result['state'][i])
                self.client.MQTT.Publish(topic, msg)
            return result
        else:
            return None
            
    """
    Calculates the statistics (average or sum of consumption) and an estimate of 
    the cost for each house according to the input parameters.
    """
    def computedata_House(self,houseID, df, time_format, avg, statistic_format):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime(time_format)
        df['state'] = df['state'].astype(float)   
        if avg == True:
            result=df.groupby(['formatted_timestamp'])['state'].mean().reset_index()  
        else:
            result = df.groupby(['formatted_timestamp'])['state'].sum().reset_index()       
        if not result.empty:
            for i in range(len(result)):
                stateTopic='homeassistant/sensor/smartSocket/house/state'
                msg='{"energy_%s": %f}' % (statistic_format, result['state'][i])
                self.client.MQTT.Publish(stateTopic, msg)
            return result
        else:
            return None

    #TODO
    """
    Finds the device that consumed the most within a specified period (day, month, year)
    and the cost associated with that consumption.
    """
    def findmax(self,df,time_format,statistic_format,sm):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime(time_format)
        result = df.groupby('formatted_timestamp').apply(lambda x: x.loc[x['state'].idxmax()][['metadata_id', 'state']]).reset_index()
        result.columns = ['formatted_timestamp', 'metadata_id', 'state']     
        if not result.empty:
            for i in range(len(result)):
                deviceID = self.getDeviceID(int(result['metadata_id'][i]),sm).lower()
                topic1='homeassistant/sensor/smartSocket/%s/%s/state' %(statistic_format,deviceID)
                msg1='{"energy": %f}' % (result['state'][i])
                self.client.MQTT.Publish(topic1, msg1)
            return result
        else:
            return None
            
    '''Retrieves information from the database for the considered metadata_ids.'''   
    def getdata(self,houseID,attribute):
        try:
            selectedMetaHAIDs=self.selectMetaHAIDs(houseID,attribute)
            query = """SELECT metadata_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp
                        FROM states
                        WHERE metadata_id IN ({})
                        """.format(','.join('?' for _ in selectedMetaHAIDs))
            self.HADBCur.execute(query,selectedMetaHAIDs)
            rows = self.HADBCur.fetchall()       
            if rows!=[]:
                df = pd.DataFrame(rows, columns=['metadata_id','state', 'timestamp'])   
                filter=~df['state'].isin(['unknown', 'unavailable'])     
                result=df[filter]
                return result
            else:
                return None
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)   
        
    def compute_hourlyavgdata(self,houseID):
        base_df = self.getdata(houseID,'energy')
        if base_df is not None:
            self.compute_data(base_df,'%Y-%m-%d %H:00:00',True,'HAvg',False)
        else:
            return None
    
    def compute_hourlytotdata(self,houseID):
        base_df=self.getdata(houseID,'energy')
        if base_df is not None:
            self.compute_data(base_df,'%Y-%m-%d %H:00:00',False,'HTot',False)
        else:
            return None
    
    def compute_dailyavgdata(self,houseID):
        hourly_df=self.getdata(houseID,'hourly_total')
        if hourly_df is not None and not hourly_df.empty:
            self.compute_data(hourly_df,'%Y-%m-%d 00:00:00',True,'DAvg',True)
        else:
            return None
    
    def compute_dailytotdata(self,houseID):
        hourly_df=self.getdata(houseID,'hourly_total')
        if hourly_df is not None and not hourly_df.empty:
            self.compute_data(hourly_df,'%Y-%m-%d 00:00:00',False,'DTot',True)
        else:
            return None
    
    def compute_monthlyavgdata(self,houseID):
        daily_df=self.getdata(houseID,'daily_total')
        if daily_df is not None and not daily_df.empty:
            self.compute_data(daily_df,'%Y-%m-01 00:00:00',True,'MAvg',True)
        else:
            return None
    
    def compute_monthlytotdata(self,houseID):
        daily_df=self.getdata(houseID,'daily_total')
        if daily_df is not None and not daily_df.empty:
            self.compute_data(daily_df,'%Y-%m-01 00:00:00',False,'MTot',True)
        else:
            return None
    
    def compute_yearlyavgdata(self,houseID):
        monthly_df=self.getdata(houseID,'monthly_total')
        if monthly_df is not None and not monthly_df.empty:
            self.compute_data(monthly_df,'%Y-01-01 00:00:00',True,'YAvg',True)
        else:
            return None
    
    def compute_yearlytotdata(self,houseID):
        monthly_df=self.getdata(houseID,'monthly_total')
        if monthly_df is not None and not monthly_df.empty:
            self.compute_data(monthly_df,'%Y-01-01 00:00:00',False,'YTot',True)
        else:
            return None
    
    def compute_hourlydataHouse(self,houseID):
        df=self.getdata(houseID,'energy')
        if df is not None and not df.empty:
            self.computedata_House(houseID,df,'%Y-%m-%d %H:00:00',True,'HAvg')
            self.computedata_House(houseID,df,'%Y-%m-%d %H:00:00',False,'HTot')
            self.findmax(df,'%Y-%m-%d %H:00:00','hourly_tot_max',False)
        else:
            return None
    
    def compute_dailydataHouse(self,houseID):
        df=self.getdata(houseID,'hourly_total')
        if df is not None and not df.empty:
            self.computedata_House(houseID,df,'%Y-%m-%d 00:00:00',True,'DAvg')
            self.computedata_House(houseID,df,'%Y-%m-%d 00:00:00',False,'DTot')
            self.findmax(df,'%Y-%m-%d 00:00:00','daily_tot_max',True)
        else:
            return None
    
    def compute_monthlydataHouse(self,houseID):
        df=self.getdata(houseID,'daily_total')
        if df is not None and not df.empty:
            self.computedata_House(houseID,df,'%Y-%m-01 00:00:00',True,'MAvg')
            self.computedata_House(houseID,df,'%Y-%m-01 00:00:00',False,'MTot')
            self.findmax(df,'%Y-%m-01 00:00:00','monthly_tot_max',True)
        else:
            return None
    
    def compute_yearlydataHouse(self,houseID):
        df=self.getdata(houseID,'monthly_total')
        if df is not None and not df.empty:
            self.computedata_House(houseID,df,'%Y-01-01 00:00:00',True,'YAvg')
            self.computedata_House(houseID,df,'%Y-01-01 00:00:00',False,'YTot')
        else:
            return None
            
    """Computes operation and statistics for each house"""
    def processdata(self):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "Houses", "keyName": "houseID", "keyValue": "*"}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            house_list = [row["houseID"] for row in result]
            for houseID in house_list:
                self.compute_hourlyavgdata(houseID)
                self.compute_hourlytotdata(houseID)
                self.compute_hourlydataHouse(houseID)

                self.compute_dailyavgdata(houseID)
                self.compute_dailytotdata(houseID)
                self.compute_dailydataHouse(houseID)

                self.compute_monthlyavgdata(houseID)
                self.compute_monthlytotdata(houseID)
                self.compute_monthlydataHouse(houseID)

                self.compute_yearlyavgdata(houseID)
                self.compute_yearlytotdata(houseID)
                self.compute_yearlydataHouse(houseID)
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

if __name__ == "__main__":
    DA = DataAnalysis()
