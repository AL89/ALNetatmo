from .netatmo_auth import NetatmoAuth
from typing import Dict, Any

# ========================
# Helper function for API calls
# ========================
def api_post(auth: NetatmoAuth, endpoint:str, payload:str,get_token:bool=False) -> Dict[str,Any]:
    import requests

    url = f"https://api.netatmo.com/{endpoint}"
    if get_token:
        response = requests.post(url,data=payload)
    else:
        headers = {"Authorization": f"Bearer {auth.token.get_secret_value()}"}
        response = requests.post(url, headers=headers, json=payload)
    # print(response.status_code)
    # print(response.text)
    # print(response.reason)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return response.json()