from .netatmo_auth import NetatmoAuth
from .netatmo_api import api_post
from pydantic import BaseModel
from typing import List, Optional, Self, Dict, Any, Literal, Union
import pandas as pd
from datetime import datetime, timezone, timedelta

class NetatmoTS(BaseModel):
    station_id: str
    module_id: str
    data_type: str
    data_unit: Optional[str] = None
    scale:str = '1hour'
    time: List[datetime] = []
    values: List[float] = []
    last_update: datetime = datetime.now()

class NetatmoModule(BaseModel):
    station_id: str
    module_id: str
    module_name: Optional[str] = None
    module_type: Literal['NAMain','NAModule1','NAModule2','NAModule3','NAModule4'] = 'NAMain'
    data_types: List[str] = []
    ts: List[NetatmoTS] = []
    battery_percent: Optional[int] = None
    date_setup: datetime = datetime.now()

    def get_ts_by_datatype(self,data_type:str) -> Optional[NetatmoTS]:
        return next((ts for ts in self.ts if ts.data_type == data_type),None)

class NetatmoStation(BaseModel):
    station_id: str
    home_id: Optional[str] = None
    home_name: Optional[str] = None
    modules: List[NetatmoModule] = []
    latitude: Optional[float] = None 
    longitude: Optional[float] = None
    date_setup: datetime = datetime.now()

    def df_show_modules(self) -> pd.DataFrame:
        if not self.modules:
            return pd.DataFrame()

    def get_module_by_id(self,module_id:str):
        return next((m for m in self.modules if m.module_id == module_id),None)

    def get_module_by_datatype(self,data_type:str) -> Optional[NetatmoModule]:
        return next((m for m in self.modules if data_type in m.data_types),None)
    
    def get_module_by_type(self,module_type:Literal['NAMain','NAModule1','NAModule2','NAModule3','NAModule4'] = 'NAMain') -> Optional[NetatmoModule]:
        return next((m for m in self.modules if m.module_type == module_type),None)

    def api_get_measure(
            self,
            auth:NetatmoAuth,
            data_type:str,
            scale:str='1hour',
            time_start:Union[int,datetime,None]=None,
            time_end:Union[int,datetime,None]=None,
            time_delta: int = 24*3600       # 1 day
        ):
        module = self.get_module_by_datatype(data_type=data_type)
        if module is None:
            raise ValueError(f"No module found for retrieving data '{data_type}' from Netatmo API.")

        module_ts = module.get_ts_by_datatype(data_type=data_type)
        if module_ts is None:
            module_ts = NetatmoTS(station_id=self.station_id,module_id=module.module_id,data_type=data_type,last_update=module.date_setup)

        # If both time start and end is None, set default end time to now and the start time to a day before.
        # if time_start is None and time_end is None:
        #     time_end = datetime.now()
        #     time_start = time_end - timedelta(seconds=time_delta)
        
        # Try to set the start time by module time series last update
        if time_start is None:
            time_start = module_ts.last_update
        
        # And set the time end to 1 day ahead
        if time_end is None:
            time_end = time_start + timedelta(seconds=time_delta)

        # Convert datetime to UNIX timestamps
        if isinstance(time_start, datetime):
            time_start = int(time_start.timestamp())
        if isinstance(time_end, datetime):
            time_end = int(time_end.timestamp())
        
        payload = {
            "device_id": self.station_id,
            "module_id": module.module_id,
            "scale": scale,
            "type": data_type,
            "date_begin": time_start,
            "date_end": time_end
        }
        
        data = api_post(auth, "getmeasure", payload)
        return data

    def api_station_data(self,auth:NetatmoAuth) -> Dict[str,Any]:
        payload = {
            "device_id":self.station_id
        }

        data = api_post(auth=auth,endpoint="api/getstationsdata",payload=payload)
        station_data = next((st for st in data['body']['devices'] if st['_id']==self.station_id),{})
        if not station_data:
            raise ValueError('Unable to retrieve station data from Netatmo API.')

        location = station_data.get('place',{}).get('location',[])

        # Update station
        self.home_id = station_data.get('home_id',None)
        self.home_name = station_data.get('home_name',None)
        if location:
            self.latitude = location[0]
            self.longitude = location[1]
        self.date_setup = datetime.fromtimestamp(station_data['date_setup'])

        # Create or edit modules
        modules = []

        ## Get main module if any
        main_module = self.get_module_by_id(station_data.get('_id'))
        if main_module is None:
            # Create a new main module
        
            main_module_dict = {
                'station_id':self.station_id,
                'module_id':station_data['_id'],
                'module_name':station_data['module_name'],
                'module_type':station_data['type'],
                'data_types':station_data['data_type'],
                'date_setup':datetime.fromtimestamp(station_data['date_setup']) # , tz=timezone.utc
            }
            modules.append(main_module_dict)

        for m in station_data['modules']:
            existing_module = self.get_module_by_id(module_id=m['_id'])
            if existing_module is None:
                module = {
                    'station_id':self.station_id,
                    'module_id':m['_id'],
                    'module_name':m['module_name'],
                    'module_type':m['type'],
                    'data_types':m['data_type'],
                    'battery_percent':m['battery_percent'],
                    'date_setup':datetime.fromtimestamp(station_data['last_setup']) # , tz=timezone.utc
                }
                modules.append(module)
            else:
                existing_module.battery_percent = m['battery_percent']
                existing_module.date_setup = datetime.fromtimestamp(station_data['last_setup'])

        if modules:
            self.modules.extend([NetatmoModule.model_validate(m) for m in modules])

    @staticmethod
    def api_public_stations(auth:NetatmoAuth,lat_ne, lon_ne, lat_sw, lon_sw, required_data=["Rain"]):
        payload = {
            "lat_ne": lat_ne,
            "lon_ne": lon_ne,
            "lat_sw": lat_sw,
            "lon_sw": lon_sw,
            "required_data": required_data,
            "filter": False
        }

        data = api_post(auth,"api/getpublicdata", payload)
        # stations = NetatmoStation.from_api_dict(data=data.get("body", []))
        stations_dict: List[Dict[str,Any]] = data.get("body", [])
        stations = []
        for s in stations_dict:
            location = s.get("place", {}).get("location", [None, None])
            station = NetatmoStation(
                device_id=s['_id'],
                modules=s.get('modules',[]),
                latitude=location[0],
                longitude=location[1],
                last_update=datetime.now(timezone.utc)
            )
            stations.append(station)
        return stations

    # @staticmethod
    # def from_api_dict(data:List[Dict[str,Any]]) -> List["NetatmoStation"]:

    #     stations = []
    #     for s in data:
    #         location = s.get("place", {}).get("location", [None, None])
    #         station = NetatmoStation(
    #             device_id=s['id'],
    #             station_name=s.get('station_name'),
    #             latitude=location[0],
    #             longitude=location[1],
    #             last_update=datetime.now(timezone.utc)
    #         )
    #         stations.append(station)
    #     return stations