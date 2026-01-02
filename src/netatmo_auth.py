from pydantic import BaseModel, SecretStr
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

    @property
    def token(self) -> Optional[SecretStr]:
        if self._token is None:
            self.authorize(grant_type='authorization_code')
        
        if datetime.now() > self._expiration_time:
            self.authorize(grant_type='refresh_token')
        return self._token
    
    def authorize(self,redirect_uri:str="http://localhost",grant_type:Literal["authorization_code","refresh_token"]="authorization_code"):
        """ Authorization method to get token.

        OBS! Need to provide an OAuth2 code.
        Type the following into the browser to retrieve the code:

        https://api.netatmo.com/oauth2/authorize
            ?client_id=YOUR_CLIENT_ID
            &redirect_uri=YOUR_REDIRECT_URI
            &response_type=code
            &scope=read_station

        Args:
            auth_code (str): Authorization code
        """
        import requests

        url = BASE_URL + "oauth2/token"
        scope = 'read_station'
        
        if self._auth_code is None:
            from .netatmo_auth_handler import NetatmoOAuthServer

            netatmo_server = NetatmoOAuthServer()
            auth_code = netatmo_server.start_server(client_id=self.client_id,redirect_uri=redirect_uri,scope=scope)
            self._auth_code = SecretStr(auth_code)
        
        payload = {
            "grant_type":grant_type,
            "client_id":self.client_id,
            "client_secret":self.client_secret.get_secret_value(),
        }

        if grant_type == 'authorization_code':
            payload["code"] = self._auth_code.get_secret_value()
            payload["redirect_uri"] = redirect_uri
            payload["scope"] = scope
        else: # refresh_token
            payload["refresh_token"] = self._refresh_token.get_secret_value()
        
        response = requests.post(url,data=payload)
        response.raise_for_status()
        # print(response.status_code)
        # print(response.text)
        # print(response.reason)
        data = response.json()
        
        # if not data:
        #     ValueError('Something went wrong!')

        self._token = SecretStr(data['access_token'])
        self._expiration_time = datetime.now() + timedelta(seconds=data['expires_in'])
        self._refresh_token = SecretStr(data['refresh_token'])
        
        # return data

