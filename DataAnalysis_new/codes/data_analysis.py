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
    
    def getalldata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
        matrix = np.array(rows)
        df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        condition = df['entity'].str.match(r'^sensor\.(current|voltage|power|energy)(_[0-9]+)?$')
        df = df[condition]
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
    
    def compute_hourlyavgData(self):  
        base_df = self.getalldata()
        base_df['timestamp'] = pd.to_datetime(base_df['timestamp'])
        base_df['formatted_timestamp'] = base_df['timestamp'].dt.strftime('%Y-%m-%d %H:00:00')
        # Raggruppare per 'device' e ora e calcolare le medie
        result = base_df.groupby(['device_id', 'formatted_timestamp']).mean(numeric_only=True).reset_index()        
        # Creare una lista delle colonne da trasformare in righe
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        # Inizializzare un DataFrame vuoto per i risultati
        result_df_avg = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        # Iterare sul DataFrame originale
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['formatted_timestamp']
            # Estrai il numero dopo "D" nel "device_id"
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = f'{col}_avghourly'
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df_avg = pd.concat([result_df_avg, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        if not result_df_avg.empty:
                topic='/homeassistant/sensor/smartSocket/data.analysis/hourly_avg'
                for i in range(len(result_df_avg)):
                    msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_avg['entity_id'].iloc[i], result_df_avg['state'].iloc[i], result_df_avg['timestamp'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                self.client.MQTT.stop() 
                return result_df_avg
        else:
                return None
    
    def compute_hourlytotData(self):  
        base_df = self.getalldata()
        base_df['timestamp'] = pd.to_datetime(base_df['timestamp'])
        base_df['formatted_timestamp'] = base_df['timestamp'].dt.strftime('%Y-%m-%d %H:00:00')
        result = base_df.groupby(['device_id', 'formatted_timestamp']).sum(numeric_only=True).reset_index()
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df_tot = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['formatted_timestamp']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = f'{col}_tothourly'
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df_tot = pd.concat([result_df_tot, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        if not result_df_tot.empty:
                topic='/homeassistant/sensor/smartSocket/data.analysis/hourly_tot'
                for i in range(len(result_df_tot)):
                    msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_tot['entity_id'].iloc[i], result_df_tot['state'].iloc[i], result_df_tot['timestamp'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                self.client.MQTT.stop()
                return result_df_tot
        else:
                return None
    
    def get_hourlydata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.%_tothourly%' "
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
        if rows!=[]:
            hourly_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            hourly_df['attribute'] = hourly_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
            hourly_df['device_id'] = hourly_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
            hourly_df['device_id'] = hourly_df['device_id'].apply(lambda x: f"D{x}")
            hourly_df['timestamp'] = pd.to_datetime(hourly_df['timestamp'])
            hourly_df['state'] = hourly_df['state'].astype(float)
            new_columns=['device_id','attribute','state','timestamp']
            hourly_df = hourly_df.reindex(columns=new_columns)
            hourly_df=hourly_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
            result_df = hourly_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
            return result_df     
        else:
            return None
    
    def compute_dailyavgData(self):
        hourly_df = self.get_hourlydata()
        if hourly_df is not None:
            hourly_df['timestamp'] = pd.to_datetime(hourly_df['timestamp'])
            hourly_df['day'] = hourly_df['timestamp'].dt.strftime('%Y-%m-%d 00:00:00')
            result = hourly_df.groupby(['device_id', 'day']).mean(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_avg= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['day']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_tothourly', '_avgdaily')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_avg = pd.concat([result_df_avg, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/daily_avg'
            for i in range(len(result_df_avg)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_avg['entity_id'].iloc[i], result_df_avg['state'].iloc[i], result_df_avg['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_avg
        else:
            print("No hourly data available to compute daily statistics.")
            return None
    
    def compute_dailytotData(self):
        hourly_df = self.get_hourlydata()
        if hourly_df is not None:
            hourly_df['timestamp'] = pd.to_datetime(hourly_df['timestamp'])
            hourly_df['day'] = hourly_df['timestamp'].dt.strftime('%Y-%m-%d 00:00:00')
            result = hourly_df.groupby(['device_id', 'day']).sum(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_tot= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['day']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_tothourly', '_totdaily')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_tot = pd.concat([result_df_tot, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/daily_tot'
            for i in range(len(result_df_tot)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_tot['entity_id'].iloc[i], result_df_tot['state'].iloc[i], result_df_tot['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_tot
        else:
            print("No hourly data available to compute daily statistics.")
            return None
    
    def get_dailydata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_totdaily%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
        if rows!=[]:
            daily_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            daily_df['attribute'] = daily_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
            daily_df['device_id'] = daily_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
            daily_df['device_id'] = daily_df['device_id'].apply(lambda x: f"D{x}")
            daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
            daily_df['state'] = daily_df['state'].astype(float)
            new_columns=['device_id','attribute','state','timestamp']
            daily_df = daily_df.reindex(columns=new_columns)
            daily_df=daily_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
            result_df = daily_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
            return result_df
        else:
            return None

    def compute_monthlyavgData(self):
        daily_df = self.get_dailydata()
        if daily_df is not None:
            daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
            daily_df['month'] = daily_df['timestamp'].dt.strftime('%Y-%m-01 00:00:00')
            result = daily_df.groupby(['device_id', 'month']).mean(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_avg= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['month']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_totdaily', '_avgmonthly')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_avg = pd.concat([result_df_avg, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/monthly_avg'
            for i in range(len(result_df_avg)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_avg['entity_id'].iloc[i], result_df_avg['state'].iloc[i], result_df_avg['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_avg
        else:
            print("No daily data available to compute monthly statistics.")
            return None
        
    def compute_monthlytotData(self):
        daily_df = self.get_dailydata()
        if daily_df is not None:
            daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
            daily_df['month'] = daily_df['timestamp'].dt.strftime('%Y-%m-01 00:00:00')
            result = daily_df.groupby(['device_id', 'month']).sum(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_tot= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['month']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_totdaily', '_totmonthly')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_tot = pd.concat([result_df_tot, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/monthly_tot'
            for i in range(len(result_df_tot)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_tot['entity_id'].iloc[i], result_df_tot['state'].iloc[i], result_df_tot['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_tot
        else:
            print("No daily data available to compute monthly statistics.")
            return None   
    


    def get_monthlydata(self):
        query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_totmonthly%'"
        self.curs1.execute(query)
        rows = self.curs1.fetchall()
        if rows!=[]:
            monthly_df = pd.DataFrame(rows, columns=['entity','state', 'timestamp'])
            monthly_df['attribute'] = monthly_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
            monthly_df['device_id'] = monthly_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
            monthly_df['device_id'] = monthly_df['device_id'].apply(lambda x: f"D{x}")
            monthly_df['timestamp'] = pd.to_datetime(monthly_df['timestamp'])
            monthly_df['state'] = monthly_df['state'].astype(float)
            new_columns=['device_id','attribute','state','timestamp']
            monthly_df = monthly_df.reindex(columns=new_columns)
            monthly_df=monthly_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
            result_df = monthly_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
            return result_df
        else:
            return None
    
    def compute_yearlyavgData(self):
        monthly_df=self.get_monthlydata()
        if monthly_df is not None:
            monthly_df['timestamp'] = pd.to_datetime(monthly_df['timestamp'])
            monthly_df['year'] = monthly_df['timestamp'].dt.strftime('%Y-01-01 00:00:00')
            result = monthly_df.groupby(['device_id', 'year']).mean(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_avg= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['year']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_totmonthly', '_avgyearly')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_avg = pd.concat([result_df_avg, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/yearly_avg'
            for i in range(len(result_df_avg)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_avg['entity_id'].iloc[i], result_df_avg['state'].iloc[i], result_df_avg['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_avg
        else:
            print("No monthly data available to compute yearly statistics.")
            return None   
    
    def compute_yearlytotData(self):
        monthly_df=self.get_monthlydata()
        if monthly_df is not None:
            monthly_df['timestamp'] = pd.to_datetime(monthly_df['timestamp'])
            monthly_df['year'] = monthly_df['timestamp'].dt.strftime('%Y-01-01 00:00:00')
            result = monthly_df.groupby(['device_id', 'year']).sum(numeric_only=True).reset_index()        
            columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
            result_df_tot= pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
            for _, row in result.iterrows():
                device_id = row['device_id']
                timestamp = row['year']
                i = int(device_id[1:])
                for col in columns_to_melt:
                    entity_id = col.replace('_totmonthly', '_totyearly')
                    if i > 1:
                        entity_id += f'_{i}'
                    state = row[col]
                    result_df_tot = pd.concat([result_df_tot, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
            topic='/homeassistant/sensor/smartSocket/data.analysis/yearly_tot'
            for i in range(len(result_df_tot)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df_tot['entity_id'].iloc[i], result_df_tot['state'].iloc[i], result_df_tot['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df_tot
        else:
            print("No monthly data available to compute yearly statistics.")
            return None  
    
    def compute_hourlyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.%_tothourly%'"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                FROM HouseDev_conn\
                WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()

        combined_results = []
        # Iterate through the rows from the first database
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
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_hourly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        if not result_df.empty:
            topic='/homeassistant/sensor/smartSocket/data.analysis/hourly_house'
            for i in range(len(result_df)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df
        else:
            return None

    def findmaxinaday(self,houseID):
        df=self.compute_hourlyDataHouse(houseID)
        if df is not None:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['day'] = df['timestamp'].dt.date
            max_state_df = df.groupby(['day', 'entity_id'])[['state']].max().reset_index()
            result_df = df.merge(max_state_df, on=['day', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
            result_df['entity_id'] = result_df['entity_id'] + '_max'
            result_df = result_df.drop(columns=['day'])
            result_df['state'] = result_df['state'].astype(int)
            if not result_df.empty:
                topic='/homeassistant/sensor/smartSocket/data.analysis/hourly_house_max'
                for i in range(len(result_df)):
                    msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                self.client.MQTT.stop()
                return result_df
            else:
                return None
        
    

    def compute_dailyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.%_totdaily%'"
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
                # Handle the case where entity_id doesn't match the expected format
                # Check if the deviceID is in the list of deviceIDs for house H1
            for row2 in rows2:
                if row2[1] == deviceID:
                    combined_results.append((entity_id, state,timestamp))  
        
        df = pd.DataFrame(combined_results, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totdaily')
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_daily_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        if not result_df.empty:
            topic='/homeassistant/sensor/smartSocket/data.analysis/daily_house'
            for i in range(len(result_df)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df
        else:
            return None
    
    def findmaxinamonth(self,houseID):
        df=self.compute_dailyDataHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.to_period('M')
        max_state_df = df.groupby(['month', 'entity_id'])[['state']].max().reset_index()
        result_df = df.merge(max_state_df, on=['month', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
        result_df['entity_id'] = result_df['entity_id'] + '_max'
        result_df = result_df.drop(columns=['month'])
        result_df['state'] = result_df['state'].astype(int)
        if not result_df.empty:
                topic='/homeassistant/sensor/smartSocket/data.analysis/daily_house_max'
                for i in range(len(result_df)):
                    msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                self.client.MQTT.stop()
                return result_df
        else:
                return None
    
    def compute_monthlyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.%_totmonthly%'"
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
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_monthly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})      
        if not result_df.empty:
            topic='/homeassistant/sensor/smartSocket/data.analysis/monthly_house'
            for i in range(len(result_df)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df
        else:
            return None
    
    def findmaxinayear(self,houseID):
        df=self.compute_monthlyDataHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['year'] = df['timestamp'].dt.to_period('Y')
        max_state_df = df.groupby(['year', 'entity_id'])[['state']].max().reset_index()
        result_df = df.merge(max_state_df, on=['year', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
        result_df['entity_id'] = result_df['entity_id'] + '_max'
        result_df = result_df.drop(columns=['year'])
        result_df['state'] = result_df['state'].astype(int)  
        if not result_df.empty:
                topic='/homeassistant/sensor/smartSocket/data.analysis/monthly_house_max'
                for i in range(len(result_df)):
                    msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                    self.client.MQTT.Publish(topic, msg)
                self.client.MQTT.stop()
                return result_df
        else:
                return None  
        
    
    def compute_yearlyDataHouse(self,houseID):
        query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                FROM states2\
                WHERE entity_id LIKE 'sensor.%_totyearly%'"
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
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_yearly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})       
        if not result_df.empty:
            topic='/homeassistant/sensor/smartSocket/data.analysis/yearly_house'
            for i in range(len(result_df)):
                msg='{"entity_id": "%s", "state": %f,"timestamp": "%s"}' % (result_df['entity_id'].iloc[i], result_df['state'].iloc[i], result_df['timestamp'].iloc[i])
                self.client.MQTT.Publish(topic, msg)
            self.client.MQTT.stop()
            return result_df
        else:
            return None
    

    def process_data(self):
        self.compute_hourlyavgData()
        self.compute_hourlytotData()
        self.compute_dailyavgData()
        self.compute_dailytotData()
        self.compute_monthlyavgData()
        self.compute_monthlytotData()
        self.compute_yearlyavgData()
        self.compute_yearlytotData()
        query="SELECT houseID\
                FROM Houses"
        self.curs2.execute(query)
        rows = self.curs2.fetchall()
        houses_list= [item[0] for item in rows]
        for houseID in houses_list:
            self.findmaxinaday(houseID)
            self.findmaxinamonth(houseID)
            self.findmaxinayear(houseID)
            self.compute_yearlyDataHouse(houseID)
        
        
    




                    
