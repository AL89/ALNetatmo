from pydantic import BaseModel, SecretStr
import os
from typing import Optional, Literal
from datetime import datetime, timedelta

BASE_URL = "https://api.netatmo.com/"

class NetatmoAuth(BaseModel, validate_assignment=True):
    email: str
    password: SecretStr
    client_id: str
    client_secret: SecretStr

    # Auth details
    _auth_code: Optional[SecretStr] = None
    _token: Optional[SecretStr] = None
    _expiration_time: Optional[datetime] = None
    _refresh_token: Optional[SecretStr] = None

    _scope: str = "read_station"
    _redirect_uri: str = "http://localhost"

    @property
    def auth_code(self) -> Optional[SecretStr]:
        if self._auth_code is None:
            code_txt_path = "src/auth_code.txt"
            if os.path.isfile(code_txt_path):
                with open(code_txt_path, "r", encoding="utf-8") as f:
                    auth_code = f.read().strip()
            else:
                """OBS! Need to provide an OAuth2 code.
                Type the following into the browser to retrieve the code:

                https://api.netatmo.com/oauth2/authorize
                    ?client_id=YOUR_CLIENT_ID
                    &redirect_uri=YOUR_REDIRECT_URI
                    &response_type=code
                    &scope=read_station
                """
                from .netatmo_auth_handler import NetatmoOAuthServer

                netatmo_server = NetatmoOAuthServer()
                auth_code = netatmo_server.start_server(client_id=self.client_id,redirect_uri=self._redirect_uri,scope=self._scope)
                self._save_auth_code(auth_code=auth_code)
            
            self.auth_code = auth_code

        return self._auth_code
    
    @auth_code.setter
    def auth_code(self,value:str):
        self._auth_code = SecretStr(value)

    def _save_auth_code(self,auth_code:str,txt_path:str="src/auth_code.txt"):
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(auth_code)

    @property
    def token(self) -> Optional[SecretStr]:
        if self._token is None:
            self.authorize(grant_type='authorization_code')
        
        if datetime.now() > self._expiration_time:
            self.authorize(grant_type='refresh_token')
        return self._token
    
    def authorize(self,grant_type:Literal["authorization_code","refresh_token"]="authorization_code"):
        """ Authorization method to get token.

        Args:
            grant_type (Literal['authorization_code','refresh_token'], optional): Whether to get a new token or refresh the existing. Defaults to "authorization_code".
        """
        from .netatmo_api import api_post

        payload = {
            "grant_type":grant_type,
            "client_id":self.client_id,
            "client_secret":self.client_secret.get_secret_value(),
        }

        if grant_type == 'authorization_code':
            payload["code"] = self.auth_code.get_secret_value()
            payload["redirect_uri"] = self._redirect_uri
            payload["scope"] = self._scope
        else: # refresh_token
            payload["refresh_token"] = self._refresh_token.get_secret_value()
        
        
        data = api_post(auth=self,endpoint="oauth2/token", payload=payload,get_token=True)
        # response = requests.post(url,data=payload)
        # response.raise_for_status()
        # print(response.status_code)
        # print(response.text)
        # print(response.reason)
        # data = response.json()
        
        # if not data:
        #     ValueError('Something went wrong!')

        self._token = SecretStr(data['access_token'])
        self._expiration_time = datetime.now() + timedelta(seconds=data['expires_in'])
        self._refresh_token = SecretStr(data['refresh_token'])
        
        # return data

