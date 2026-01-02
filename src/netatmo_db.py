# from pydantic import BaseModel
from typing import List, Any, Dict
import duckdb
from .netatmo_auth import NetatmoAuth
from .netatmo_weather import NetatmoStation

class NetatmoDB:
    def __init__(self,db_path:str="netatmo_weather.db",access_token:str=None):
        self.db_path = db_path
        self.conn = duckdb.connect(self.db_path)

        self._create_tables()

    def _create_tables(self):
        # Stations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                station_name TEXT,
                latitude DOUBLE,
                longitude DOUBLE,
                last_update TIMESTAMP                  
            )
        """)

        # Measurements table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                station_id TEXT,
                time TIMESTAMP,
                temperature DOUBLE,
                rain DOUBLE,
                humidity DOUBLE,
                PRIMARY KEY(station_id, time)
            )
        """)

    # ========================
    # Helper function for API calls
    # ========================
    # def _api_post(self, auth: NetatmoAuth, endpoint:str, payload:str) -> Dict[str,Any]:
    #     import requests

    #     url = f"https://api.netatmo.com/api/{endpoint}"
    #     headers = {"Authorization": f"Bearer {auth.token.get_secret_value()}"}
    #     response = requests.post(url, headers=headers, json=payload)
    #     response.raise_for_status()
    #     return response.json()
    
    def add_stations(self,stations:List[NetatmoStation]):
        for s in stations:
            self.conn.execute("""
                INSERT OR REPLACE INTO stations (station_id, station_name, latitude, longitude, last_update)
                VALUES (?, ?, ?, ?, ?)
            """, [
                s.device_id,
                s.station_name,
                s.latitude,s.longitude,
                s.last_update
            ])
        return stations
    
    # def fetch_public_stations(self, lat_ne, lon_ne, lat_sw, lon_sw, required_data=["Rain"]) -> List[NetatmoStation]:
    #     from datetime import datetime, timezone

    #     payload = {
    #         "lat_ne": lat_ne,
    #         "lon_ne": lon_ne,
    #         "lat_sw": lat_sw,
    #         "lon_sw": lon_sw,
    #         "required_data": required_data,
    #         "filter": "all"
    #     }

    #     data = self._api_post("getpublicdata", payload)
    #     stations = NetatmoStation.from_api_dict(data=data.get("body", []))

    #     # Gem i DB
    #     for s in stations:
    #         self.conn.execute("""
    #             INSERT OR REPLACE INTO stations (station_id, station_name, latitude, longitude, last_update)
    #             VALUES (?, ?, ?, ?, ?)
    #         """, [
    #             s.device_id,
    #             s.station_name,
    #             s.latitude,s.longitude,
    #             s.last_update
    #         ])
    #     return stations
