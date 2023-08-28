import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
import sqlite3
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt

from microserviceBase.serviceBase import *

class DataAnalysis():

    def __init__(self):
        self.conn1 = sqlite3.connect("Data_DB/testDB.db")
        self.curs1 = self.conn1.cursor()
        self.conn2 = sqlite3.connect("Data_DB/db.sqlite")
        self.curs2 = self.conn2.cursor()        
        self.client = ServiceBase("codes/serviceConfig_example.json")
        self.client.start()
    
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
                topic='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(format_statistic,houseID)
                msg='{"energy": %f}' % (result_df['state'].iloc[i])
                print(topic)
                print(msg)
                self.client.MQTT.Publish(topic, msg)
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
                    topic='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(format_statistic,houseID)
                    msg='{"energy": %f}' % (result_df['state'].iloc[i])
                    print(topic)
                    print(msg)
                    self.client.MQTT.Publish(topic, msg)
                #self.client.MQTT.stop()
                return result_df
            else:
                return None
    
    def getalldata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.energy%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
        matrix = np.array(rows)
        df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        condition = df['entity'].str.match(r'^sensor\.energy(_[0-9]+)?$')
        df = df[condition]
        result=self.process_df(df)
        return result

    def compute_data(self,df,time_format,avg,statistic_format):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime(time_format)
        if avg==True:
            result = df.groupby(['device_id', 'formatted_timestamp']).mean(numeric_only=True).reset_index()    
        else:
            result = df.groupby(['device_id', 'formatted_timestamp']).sum(numeric_only=True).reset_index()    
        if not result.empty:
                for i in range(len(result)):
                    topic='/homeassistant/sensor/smartSocket/data_analysis/%s/%s/state' %(statistic_format,result['device_id'].iloc[i])
                    msg='{"energy": %f}' % (result['sensor.energy'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                #self.client.MQTT.stop() 
                return result
        else:
                return None

    def compute_hourlyavgdata(self):
        base_df=self.getalldata()
        self.compute_data(base_df,'%Y-%m-%d %H:00:00',True,'hourly_avg')
    
    def compute_hourlytotdata(self):
        base_df=self.getalldata()
        self.compute_data(base_df,'%Y-%m-%d %H:00:00',False,'hourly_tot')
        
    
    def get_hourlydata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_tothourly%' "
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
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
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totdaily%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
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
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.energy_totmonthly%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
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
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_tothourly%'"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                FROM HouseDev_conn\
                WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()
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
            for row2 in rows2:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))    
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_tothourly')
        result=self.process_df_house(df,'hourly',houseID,'hourly_tot')
        self.findmax(result,'D','day',houseID,'hourly_tot_max')


    def compute_dailyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.energy_totdaily%'"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                            FROM HouseDev_conn\
                            WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()
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
            for row2 in rows2:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))            

        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totdaily')
        result=self.process_df_house(df,'daily',houseID,'daily_tot')
        self.findmax(result,'M','month',houseID,'daily_tot_max')
        
    
    def compute_monthlyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totmonthly%'"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                FROM HouseDev_conn\
                WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()
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
            for row2 in rows2:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))  
        
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totmonthly')
        result=self.process_df_house(df,'monthly',houseID,'monthly_tot')
        self.findmax(result,'Y','year',houseID,'monthly_tot_max')
    
    def compute_yearlyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.energy_totyearly%'"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                FROM HouseDev_conn\
                WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()
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
            for row2 in rows2:
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
        query="SELECT houseID\
                FROM Houses"
        self.curs2.execute(query)
        rows = self.curs2.fetchall()
        houses_list= [item[0] for item in rows]
        for houseID in houses_list:
            self.compute_hourlyDataHouse(houseID)
            self.compute_dailyDataHouse(houseID)
            self.compute_monthlyDataHouse(houseID)
            self.compute_yearlyDataHouse(houseID)
        

