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
import numpy as np

import requests

from microserviceBase.serviceBase import *

class DataAnalysis():

    def __init__(self):
        try:
            config_file = "data_analysis.json"
            if(not IN_DOCKER):
                config_file = "Data_Analysis/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()
            testDB_loc = "testDB.db"
            if(not IN_DOCKER):
                testDB_loc = "Data_Analysis/" + testDB_loc
            self.DBConn = sqlite3.connect(testDB_loc)
            self.DBCurs = self.DBConn.cursor()  

            while(True):
                self.process_data()
                time.sleep(5*60)

        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

    
    def process_df(self,df):
        df['attribute'] = df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
        df['device_id'] = df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
        df['device_id'] = df['device_id'].apply(lambda x: f"D{x}")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['state'] = df['state'].astype(float)
        new_columns=['device_id','attribute','state','timestamp']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        pivot_df = df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
        return pivot_df
    
    def process_df_house(self,df,format_sensor,houseID,format_statistic):
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_{format_sensor}_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        if not result_df.empty:
            for i in range(len(result_df)):
                topic1='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(format_statistic,houseID)
                msg1='{"energy": %f}' % (result_df['state'].iloc[i])
                self.client.MQTT.Publish(topic1, msg1)

                topic2='/homeassistant/sensor/smartSocket/data_analysis/%s_cost/%s/state' %(format_statistic,houseID)
                msg2='{"energy": %f}' % (result_df['state'].iloc[i]*self.cost)
                self.client.MQTT.Publish(topic2, msg2)
            #self.client.MQTT.stop()
            return result_df
        else:
            return None
    
    def findmax(self,df,period,metric,houseID,format_statistic):
        if df is not None:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df[metric] = df['timestamp'].dt.to_period(period)
            max_state_df = df.groupby([metric, 'entity_id'])[['state']].max().reset_index()
            result_df = df.merge(max_state_df, on=[metric, 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
            result_df['entity_id'] = result_df['entity_id'] + '_max'
            result_df = result_df.drop(columns=[metric])
            result_df['state'] = result_df['state'].astype(int)
            if not result_df.empty:
                for i in range(len(result_df)):
                    topic1='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(format_statistic,houseID)
                    msg1='{"energy": %f}' % (result_df['state'].iloc[i])
                    self.client.MQTT.Publish(topic1, msg1)

                    topic2='/homeassistant/sensor/smartSocket/data_analysis/%s_cost/%s/state' %(format_statistic,houseID)
                    msg2='{"energy": %f}' % (result_df['state'].iloc[i]*self.cost)
                    self.client.MQTT.Publish(topic2, msg2)
                #self.client.MQTT.stop()
                return result_df
            else:
                return None
    
    def getalldata(self):
        try:
            query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.energy%'"
            self.DBCurs.execute(query)
            rows = self.DBCurs.fetchall()        
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        matrix = np.array(rows)
        df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        condition = df['entity'].str.match(r'^sensor\.energy(_[0-9]+)?$')
        df = df[condition]
        result=self.process_df(df)
        return result
    

    def getdevHouse(self,houseID):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseDev_conn", "keyName": "houseID", "keyValue": houseID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)       

            house_devs_list = []
            for row in result:
                house_devs_list.append((row["houseID"], row["deviceID"]))
            return house_devs_list
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

    '''
        This function calculates the average or the total energy consumption for each device in a given time period (hourly, daily, monthly, yearly).
        The result is published on the MQTT broker.
        It takes as input:
            - df: the dataframe containing the data to be processed
            - time_format: the format of the timestamp
            - avg: a boolean value that indicates whether the average or the total energy consumption has to be calculated
            - statistic_format: the format of the statistic (hourly_avg, hourly_tot, daily_avg, daily_tot, monthly_avg, monthly_tot, yearly_avg, yearly_tot)
    '''
    def compute_data(self, df, time_format, avg, statistic_format):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime(time_format)
        if avg == True:
            result = df.groupby(['device_id', 'formatted_timestamp']).mean(numeric_only=True).reset_index()    
        else:
            result = df.groupby(['device_id', 'formatted_timestamp']).sum(numeric_only=True).reset_index()    
        if not result.empty:
            for i in range(len(result)):
                topic1='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(statistic_format,result['device_id'].iloc[i])
                msg1='{"energy": %f}' % (result['sensor.energy'].iloc[i])
                self.client.MQTT.Publish(topic1, msg1)

                topic2='/homeassistant/sensor/smartSocket/data_analysis/%s_cost/%s/state' %(statistic_format,result['device_id'].iloc[i])
                msg2='{"energy": %f}' % (result['sensor.energy'].iloc[i]*self.cost)
                self.client.MQTT.Publish(topic2, msg2)
            #self.client.MQTT.stop() 
            return result
        else:
            return None

    def compute_hourlyavgdata(self):
        base_df = self.getalldata()
        self.compute_data(base_df,'%Y-%m-%d %H:00:00',True,'hourly_avg')
    
    def compute_hourlytotdata(self):
        base_df=self.getalldata()
        self.compute_data(base_df,'%Y-%m-%d %H:00:00',False,'hourly_tot')
        
    
    def get_hourlydata(self):
        try:
            query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_tothourly%' "
            self.DBCurs.execute(query)
            rows = self.DBCurs.fetchall()        
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
        if rows!=[]:
            hourly_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            result_df=self.process_df(hourly_df)
            return result_df     
        else:
            return None

    
    def compute_dailyavgdata(self):
        hourly_df=self.get_hourlydata()
        hourly_df.rename(columns={'sensor.energy_tothourly':'sensor.energy'}, inplace=True)
        if hourly_df is not None:
            self.compute_data(hourly_df,'%Y-%m-%d 00:00:00',True,'daily_avg')
        else:
            return None
    
    def compute_dailytotdata(self):
        hourly_df=self.get_hourlydata()
        hourly_df.rename(columns={'sensor.energy_tothourly':'sensor.energy'}, inplace=True)
        if hourly_df is not None:
            self.compute_data(hourly_df,'%Y-%m-%d 00:00:00',False,'daily_tot')
        else:
            return None

    def get_dailydata(self):
        try:
            query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totdaily%'"
            self.DBCurs.execute(query)
            rows = self.DBCurs.fetchall()        
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)        
        if rows!=[]:
            daily_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            result_df=self.process_df(daily_df)
            return result_df     
        else:
            return None
        

    
    def compute_monthlyavgdata(self):
        daily_df=self.get_dailydata()
        daily_df.rename(columns={'sensor.energy_totdaily':'sensor.energy'}, inplace=True)
        if daily_df is not None:
            self.compute_data(daily_df,'%Y-%m-01 00:00:00',True,'monthly_avg')
        else:
            return None
    
    def compute_monthlytotdata(self):
        daily_df=self.get_dailydata()
        daily_df.rename(columns={'sensor.energy_totdaily':'sensor.energy'}, inplace=True)
        if daily_df is not None:
            self.compute_data(daily_df,'%Y-%m-01 00:00:00',False,'monthly_tot')
        else:
            return None
    

    def get_monthlydata(self):
        try:
            query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.energy_totmonthly%'"
            self.DBCurs.execute(query)
            rows = self.DBCurs.fetchall()        
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)        
        if rows!=[]:
            monthly_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            result_df=self.process_df(monthly_df)
            return result_df     
        else:
            return None

    def compute_yearlyavgdata(self):
        daily_df=self.get_monthlydata()
        daily_df.rename(columns={'sensor.energy_totmonthly':'sensor.energy'}, inplace=True)
        if daily_df is not None:
            self.compute_data(daily_df,'%Y-01-01 00:00:00',True,'yearly_avg')
        else:
            return None
    
    def compute_yearlytotdata(self):
        monthly_df=self.get_monthlydata()
        monthly_df.rename(columns={'sensor.energy_totmonthly':'sensor.energy'}, inplace=True)
        if monthly_df is not None:
            self.compute_data(monthly_df,'%Y-01-01 00:00:00',False,'yearly_tot')
        else:
            return None
    

    def compute_hourlyDataHouse(self,houseID):
        try:
            query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_tothourly%'"
            self.DBCurs.execute(query1)
            rows1 = self.DBCurs.fetchall()
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
        house_devs_list = self.getHouseDevList(houseID)
        combined_results = []   
        for row1 in rows1:
            entity_id= row1[0]
            state= row1[1]
            timestamp=row1[2]
            entity_id_parts = entity_id.split("_")
            if len(entity_id_parts) >= 2:
                if entity_id_parts[-2] == 'tothourly':
                    deviceID = 'D'+ entity_id_parts[-1]
                elif entity_id_parts[-1] == 'tothourly':
                    deviceID = 'D1'
                else:
                    deviceID = None
            else:
                deviceID = None
            for row2 in house_devs_list:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))    
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_tothourly')
        result=self.process_df_house(df,'hourly',houseID,'hourly_tot')
        self.findmax(result,'D','day',houseID,'hourly_tot_max')


    def compute_dailyDataHouse(self,houseID):
        try:
            query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                    FROM states2\
                    WHERE entity_id LIKE 'sensor.energy_totdaily%'"
            self.DBCurs.execute(query1)
            rows1 = self.DBCurs.fetchall()
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
        house_devs_list = self.getHouseDevList(houseID)
        combined_results = []   
        for row1 in rows1:
            entity_id= row1[0]
            state= row1[1]
            timestamp=row1[2]
            entity_id_parts = entity_id.split("_")
            if len(entity_id_parts) >= 2:
                if entity_id_parts[-2] == 'totdaily':
                    deviceID = 'D'+ entity_id_parts[-1]
                elif entity_id_parts[-1] == 'totdaily':
                    deviceID = 'D1'
                else:
                    deviceID = None
            else:
                deviceID = None
            for row2 in house_devs_list:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))            

        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totdaily')
        result=self.process_df_house(df,'daily',houseID,'daily_tot')
        self.findmax(result,'M','month',houseID,'daily_tot_max')
        
    
    def compute_monthlyDataHouse(self,houseID):
        try:
            query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totmonthly%'"
            self.DBCurs.execute(query1)
            rows1 = self.DBCurs.fetchall()
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
        house_devs_list = self.getHouseDevList(houseID)
        combined_results = []   
        for row1 in rows1:
            entity_id= row1[0]
            state= row1[1]
            timestamp=row1[2]
            entity_id_parts = entity_id.split("_")
            if len(entity_id_parts) >= 2:
                if entity_id_parts[-2] == 'totmonthly':
                    deviceID = 'D'+ entity_id_parts[-1]
                elif entity_id_parts[-1] == 'totmonthly':
                    deviceID = 'D1'
                else:
                    deviceID = None
            else:
                deviceID = None
            for row2 in house_devs_list:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))  
        
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totmonthly')
        result=self.process_df_house(df,'monthly',houseID,'monthly_tot')
        self.findmax(result,'Y','year',houseID,'monthly_tot_max')
    
    def compute_yearlyDataHouse(self,houseID):
        try:
            query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totyearly%'"
            self.DBCurs.execute(query1)
            rows1 = self.DBCurs.fetchall()
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
        house_devs_list = self.getHouseDevList(houseID)
        combined_results = []
        for row1 in rows1:
            entity_id= row1[0]
            state= row1[1]
            timestamp=row1[2]
            entity_id_parts = entity_id.split("_")
            if len(entity_id_parts) >= 2:
                if entity_id_parts[-2] == 'totyearly':
                    deviceID = 'D'+ entity_id_parts[-1]
                elif entity_id_parts[-1] == 'totyearly':
                    deviceID = 'D1'
                else:
                    deviceID = None
            else:
                deviceID = None
            for row2 in house_devs_list:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))  
        
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totyearly')
        self.process_df_house(df,'yearly',houseID,'yearly_tot')
    
    def process_data(self):
        self.compute_hourlyavgdata()
        self.compute_hourlytotdata()
        self.compute_dailyavgdata()
        self.compute_dailytotdata()
        self.compute_monthlyavgdata()
        self.compute_monthlytotdata()
        self.compute_yearlyavgdata()
        self.compute_yearlytotdata()
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
                self.compute_hourlyDataHouse(houseID)
                self.compute_dailyDataHouse(houseID)
                self.compute_monthlyDataHouse(houseID)
                self.compute_yearlyDataHouse(houseID)

        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

service = DataAnalysis()


