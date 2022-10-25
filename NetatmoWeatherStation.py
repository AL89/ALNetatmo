from os.path import exists
from datetime import datetime
import json
#import lnetatmo
import pandas as pd
from lnetatmo import _GETMEASURE_REQ, ClientAuth, WeatherStationData, postRequest


# Credientials are stored in .netatmo.credentials file or predefined here
netatmo_credentials = {
    # "CLIENT_ID" :  "634d73bb6ecff2650d0d3d5c",         #   Your client ID from Netatmo app registration at http://dev.netatmo.com/dev/listapps
    # "CLIENT_SECRET" : "clxicx1tJLoP5w4lZT6wjevU9p",      #   Your client app secret   '     '
    # "USERNAME" : "andreas@loevgaard.dk",           #   Your netatmo account username
    # "PASSWORD" : "Al070789"            #   Your netatmo account password
}
file_credentials = '.netatmo.credentials'
if exists(file_credentials): # if credentials exists in this file, do the following:
    with open(file_credentials, "r") as f:
        netatmo_credentials.update({k.upper():v for k,v in json.loads(f.read()).items()})

authData = ClientAuth(
    clientId=netatmo_credentials['CLIENT_ID'],
    clientSecret=netatmo_credentials['CLIENT_SECRET'],
    username=netatmo_credentials['USERNAME'],
    password=netatmo_credentials['PASSWORD']
)

DEFAULT_DB = 'default.db'

class WST(WeatherStationData):
    def __init__(self, authData=authData, home=None, station=None,db=DEFAULT_DB):
        super().__init__(authData, home, station)
        self.__setModulesDF()
        self.__DATABASE = db

    def __setModulesDF(self):
        stations = list(self.stations.keys())
        InOut = []
        stType = []
        stName = []
        IDs = []
        dateSetupNums = []
        moduleNames = []
        dataTypes = []
        battery = []
        for s in stations:
            data = self.stations[s]
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
                    
        ModulesDict = {'Type':stType,
                        'Station':stName,
                        'ID':IDs,
                        'Module':moduleNames,
                        'Data types':dataTypes,
                        'Date setup':dateSetupNums,
                        'Battery (%)':battery,
                        'In/Out':InOut}
        self.__modules = pd.DataFrame(ModulesDict)

    @property
    def Modules(self):
        return self.__modules

    def MeasureDF(self, device_id, scale, mtype, module_id=None, date_begin=None, date_end=None, limit=None, optimize=False, real_time=False):
        data = self.getMeasure(device_id, scale, mtype, module_id=None, date_begin=None, date_end=None, limit=None, optimize=False, real_time=False)
        # postParams = { "access_token" : self.getAuthToken }
        # postParams['device_id']  = device_id
        # if module_id:
        #     postParams['module_id'] = module_id
        # postParams['scale']      = scale
        # postParams['type']       = mtype
        # if date_begin:
        #     postParams['date_begin'] = date_begin
        # if date_end:
        #     postParams['date_end'] = date_end
        # if limit:
        #     postParams['limit'] = limit
        # postParams['optimize'] = "true" if optimize else "false"
        # postParams['real_time'] = "true" if real_time else "false"

        # data = postRequest(_GETMEASURE_REQ, postParams)
        try:
            dataDF = pd.DataFrame(data=data['body']).T
            dataDF['Date'] = [pd.to_datetime(x,unit='s') for x in list(dataDF.index)]
            dataDF.set_index('Date',inplace=True)
            dataDF.columns = [mtype]
        except TypeError:
            dataDF = pd.DataFrame()

        return dataDF

    def __repr__(self):
        return repr(self.__modules)