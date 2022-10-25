# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 10:00:07 2020

@author: ALD
"""
import lnetatmo
#import patatmo
import pandas as pd
import pickle
#import utm
import time

# def Netatmo1000TS(startTime,tscale):
#     if tscale == '5min':
#         ts = 5*60
#     elif tscale == '30min':
#         ts = 30*60
#     elif tscale == '1hour':
#         ts = 60*60
#     elif tscale == '3hours':
#         ts = 3*60*60
#     elif tscale == '1day':
#         ts = 24*60*60
#     elif tscale == '1week':
#         ts = 7*24*60*60
#     elif tscale == '1month':
#         ts = 30*24*60*60
    
#     endTime = startTime + 1000*ts
    
#     if endTime > time.time():
#         endTime = time.time()
    
#     return endTime

# This function use the NetatmoWST GetData function to collect the latest data based on the 'Data' input
def CollectNWSTData(WST,Data=None,DItems=None,startTime=None,endTime=None,tscale='5min'):  
    if DItems == None:
        dataitems = list(WST.GetStationData()['Data types'])
        in_out = list(WST.GetStationData()['In/Out'])
        DItems = []
        for i, di in enumerate(dataitems):
            env = in_out[i]
            for el in di:
                DItems.append(env + '' + el)

    if Data == None:
        startTime_WST = WST.startTime
        if startTime == None:
            startTime = startTime_WST
    else:
        if startTime == None:
            startTime = (Data.index[-1] - pd.Timestamp('1970-01-01')) // pd.Timedelta('1s')
            
    if endTime == None:
        endTime = time.time()
    
    while startTime < endTime:
        collectData = WST.GetData(datatype=DItems, startTime=startTime,tscale=tscale)
        try:
            Data = Data.append(collectData)
        except AttributeError:
            Data = pd.DataFrame()
            Data = Data.append(collectData)
        except TypeError:
            break
        startTime = (Data.index[-1] - pd.Timestamp('1970-01-01')) // pd.Timedelta('1s')
    
    return Data

class NetatmoWST(object):
    def __init__(self,clientID,clientSECRET,user,password):
        auth = lnetatmo.ClientAuth(clientId=clientID,
                                   clientSecret=clientSECRET,
                                   username=user,
                                   password=password)
        self.WeatherStation = lnetatmo.WeatherStationData(auth)
        
    def GetStationData(self,df=True):
        try:
            if df:    
                return self.Modules
            else:
                return self.ModulesDict
        except:
            stations = list(self.WeatherStation.stations.keys())
            InOut = []
            stType = []
            stName = []
            IDs = []
            dateSetupNums = []
            moduleNames = []
            dataTypes = []
            battery = []
            for s in stations:
                data = self.WeatherStation.stations[s]
                stType.append(data['type'])
                stationName = data['station_name']
                stName.append(stationName)
                self.IdStation = data['_id']
                IDs.append(self.IdStation)
                self.startTime = data['date_setup']
                dateSetupNums.append(self.startTime)
                moduleNames.append(data['module_name'])
                dataTypes.append(data['data_type'])
                battery.append(None)
                InOut.append('Indoor')
                for mod in data['modules']:
                    stType.append(mod['type'])
                    stName.append(stationName)
                    IDs.append(mod['_id'])
                    dateSetupNums.append(self.startTime)
                    moduleNames.append(mod['module_name'])
                    dataTypes.append(mod['data_type'])
                    battery.append(mod['battery_percent'])
                    InOut.append('Outdoor')
                    
            self.ModulesDict = {'Type':stType,
                                'Station':stName,
                            'ID':IDs,
                            'Module':moduleNames,
                            'Data types':dataTypes,
                            'Date setup':dateSetupNums,
                            'Battery (%)':battery,
                            'In/Out':InOut}
            self.Modules = pd.DataFrame(self.ModulesDict)
            if df:
                return self.Modules
            else:
                return self.ModulesDict
    
    def GetData(self,datatype,startTime=None,tscale='5min'):
        stData = self.GetStationData()
        
        if type(datatype) == str:
            datatype = [datatype]
            
        if type(startTime) == str:
            startTime = lnetatmo.toEpoch(startTime)
        elif startTime == None:
            startTime = self.startTime

        for dType in datatype:
            try:
                atmosphere,dType = dType.split(' ')
            except:
                atmosphere = None
            for i, row in stData.iterrows():
                currentData = row['Data types']
                curInOut = row['In/Out']
                if dType in currentData:
                    curID = row['ID']
                    if atmosphere == curInOut or atmosphere == None:
                        break
                    
            self.measure = self.WeatherStation.getMeasure(device_id=self.IdStation,
                                                     scale=tscale,
                                                     mtype=dType,
                                                     module_id=curID,
                                                     date_begin=startTime)
            
            try:
                measureTimes = [int(x) for x in self.measure['body'].keys()]
                measureTimes = pd.to_datetime(measureTimes,unit='s')
                measureVals = [x[0] for x in self.measure['body'].values()]
                data[dType] = measureVals
            except AttributeError:
                pass
            except TypeError:
                pass
            except NameError:
                data = pd.DataFrame({dType:measureVals},index=measureTimes)
        
        try:
            return data
        except:
            return None
            
        
        
        
        #if type(Id) == str:
         #   self.WeatherStation.getMeasure(self.IdStation,dscale,)
        
def CleanRainData(RainData):
    '''
    Removes the 0's from the raindata.

    Parameters
    ----------
    RainData : DataFrame
        Contains raindata over time.

    Returns
    -------
    DataFrame (cleaned)
    '''
    rowsToKeep = []
    for i, val in enumerate(RainData['Rain']):
        if val != 0:
            if i != 0:
                if RainData.iloc[i-1,0] == 0:
                    rowsToKeep.append(i-1)
            rowsToKeep.append(i)
            if i != len(RainData):
                if RainData.iloc[i+1,0] == 0:
                    rowsToKeep.append(i+1)
            
    return RainData.iloc[rowsToKeep]
                
    

if __name__ == '__main__':
    clientId = "5f9847c2900177097644bb31"
    clientSecret= "6dMXzdnjUDzvpc6421vJvc5AoS4J"
    username='andreas@loevgaard.dk'
    password='Al070789'
        # creds = {'client_id':clientId,
        #          'client_secret':clientSecret,
        #          'username':username,
        #          'password':password}

    wst = NetatmoWST(clientId,clientSecret,username,password)
    try: 
        Rain = pickle.load(open("raindata.p","rb"))
        #newRain = CollectNWSTData(wst,Data=Rain,DItems='Rain')
        #cleanedRain = CleanRainData(newRain)
        #cleanedRain = CleanRainData(Rain)
    except:
        # clientId = "5f9847c2900177097644bb31"
        # clientSecret= "6dMXzdnjUDzvpc6421vJvc5AoS4J"
        # username='andreas@loevgaard.dk'
        # password='Al070789'
        # # creds = {'client_id':clientId,
        # #          'client_secret':clientSecret,
        # #          'username':username,
        # #          'password':password}

        # wst = NetatmoWST(clientId,clientSecret,username,password)

        stData = wst.GetStationData()
        Rain = CollectNWSTData(wst,DItems='Rain')
    cleanedRain = CleanRainData(Rain)
        
        #pickle.dump(Rain,open("raindata.p","wb"))
    pickle.dump(cleanedRain,open("raindata.p","wb"))
    
    
    
#Temperature = CollectNWSTData(wst,DItems='Outdoor Temperature')

#MarkvangenData = NetatmoWST(clientId,clientSecret,username,password)