from pydantic import BaseModel, model_validator, ConfigDict
from typing import List, Any, Dict, Optional, Self
import duckdb
from .netatmo_auth import NetatmoAuth
from .netatmo_weather import NetatmoStation

class NetatmoDB(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    db_path: str = "netatmo_weather.duckdb"

    stations: List[NetatmoStation] = []

    _con: Optional[duckdb.DuckDBPyConnection] = None
    
    @model_validator(mode='after')
    def on_mount(self) -> Self:
        self._create_tables()

        self.close_db()
        return self

    def conn_db(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            self._con = duckdb.connect(self.db_path)
        return self._con
    
    def close_db(self):
        if self._con is not None:
            self._con.close()
            self._con = None

    def _create_tables(self):
        # Stations table
        con = self.conn_db()
        con.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                home_id TEXT,
                home_name TEXT,
                latitude DOUBLE,
                longitude DOUBLE,
                date_setup TIMESTAMP,
            )
        """)

        # Modules table
        con.execute("""
            CREATE TABLE IF NOT EXISTS modules (
                station_id TEXT,
                module_id TEXT,
                module_name TEXT,
                module_type TEXT,
                data_types LIST (TEXT),
                battery_percent INT,
                date_setup TIMESTAMP,
                PRIMARY KEY(station_id, module_id)
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS timeseries_data (
                station_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                data_type TEXT,
                data_unit TEXT DEFAULT NULL,
                scale TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (station_id,module_id,data_type,scale)
            );
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS timeseries_values (
                module_id TEXT,
                time TIMESTAMP,
                value DOUBLE,
                PRIMARY KEY (ts_id,module_id,time)
            );
        """)

        # Foreign key constraints
        con.execute("""
            ALTER TABLE modules
            ADD CONSTRAINT fk_modules_station
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        """)
        
        con.execute("""
            ALTER TABLE timeseries_data
            ADD CONSTRAINT fk_timeseries_station
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        """)

        con.execute("""
            ALTER TABLE timeseries_data
            ADD CONSTRAINT fk_timeseries_module
            FOREIGN KEY (module_id) REFERENCES modules(module_id)
        """)

        con.execute("""
            ALTER TABLE timeseries_values
            ADD CONSTRAINT fk_timeseries_values
            FOREIGN KEY (module_id) REFERENCES timeseries_data(module_id)
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
        con = self.conn_db()
        for s in stations:

            # Insert station
            con.execute("""
                INSERT OR REPLACE INTO stations (station_id, home_id, home_name, latitude, longitude, date_setup)
                VALUES (?, ?, ?, ?, ?,?)
            """, [
                s.station_id,
                s.home_id,s.home_name,
                s.latitude,s.longitude,
                s.date_setup
            ])
            
            # Insert station modules
            for m in s.modules:
                con.execute("""
                    INSERT OR REPLACE INTO modules (station_id,module_id,module_name,module_type,data_types,battery_percent,date_setup)
                    VALUES (?,?,?,?,?,?,?)
                """,[
                    m.station_id,
                    m.module_id, m.module_name, m.module_type,
                    m.data_types, m.battery_percent, m.date_setup
                ])

                # Insert module timeseries
                for ts in m.ts:

                    # Insert into metadata table
                    con.execute("""
                        INSERT OR REPLACE INTO timeseries_data (station_id, module_id, data_type, data_unit, scale, last_update)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,[
                        ts.station_id,
                        ts.module_id,
                        ts.data_type,ts.data_unit,
                        ts.scale,
                        ts.last_update
                    ])

                    # Insert values into timeseries values table
                    


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
