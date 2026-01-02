from .netatmo_auth import NetatmoAuth
from typing import Dict, Any

# ========================
# Helper function for API calls
# ========================
def api_post(auth: NetatmoAuth, endpoint:str, payload:str) -> Dict[str,Any]:
    import requests

    url = f"https://api.netatmo.com/api/{endpoint}"
    headers = {"Authorization": f"Bearer {auth.token.get_secret_value()}"}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()