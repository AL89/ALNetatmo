from .netatmo_auth import NetatmoAuth
from .netatmo_api import api_post
from pydantic import BaseModel
from typing import List, Optional, Self, Dict, Any
from datetime import datetime, timezone

class NetatmoTS(BaseModel):
    device_id: str
    data_type: str
    time: List[datetime] = []
    values: List[float] = []

class NetatmoStation(BaseModel):
    device_id: str
    station_name: str
    latitude: Optional[float] = None 
    longitude: Optional[float] = None
    last_update: datetime = datetime.now()

    ts: List[NetatmoTS] = []

    @staticmethod
    def api_public_stations(auth:NetatmoAuth,lat_ne, lon_ne, lat_sw, lon_sw, required_data=["Rain"]):
        payload = {
            "lat_ne": lat_ne,
            "lon_ne": lon_ne,
            "lat_sw": lat_sw,
            "lon_sw": lon_sw,
            "required_data": required_data,
            "filter": "all"
        }

        data = api_post(auth,"getpublicdata", payload)
        # stations = NetatmoStation.from_api_dict(data=data.get("body", []))
        stations_dict: List[Dict[str,Any]] = data.get("body", [])
        stations = []
        for s in stations_dict:
            location = s.get("place", {}).get("location", [None, None])
            station = NetatmoStation(
                device_id=s['id'],
                station_name=s.get('station_name'),
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