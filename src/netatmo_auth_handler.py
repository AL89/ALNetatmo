import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ========================
# KONFIGURATION
# ========================
CLIENT_ID = "DIN_CLIENT_ID"
CLIENT_SECRET = "DIT_CLIENT_SECRET"
REDIRECT_URI = "http://localhost"
SCOPE = "read_station"

TOKEN_URL = "https://api.netatmo.com/oauth2/token"

# ========================
# LOKAL HTTP SERVER
# ========================
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            self.server.auth_code = query["code"][0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h2>Netatmo login OK</h2>
                    <p>Du kan lukke dette vindue.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

# ========================
# START SERVER
# ========================

class NetatmoOAuthServer:
    def __init__(self,http_server:str='localhost',port:int=80):
        self.http_server = http_server
        self.port = port

    def start_server(self,client_id:str,redirect_uri:str="http://localhost",scope:str="read_station") -> str:
        httpd = HTTPServer((self.http_server, self.port), OAuthHandler)
        
        auth_params = (
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scope}"
        )
        print("Opens browser to Netatmo login...")
        AUTH_URL = "https://api.netatmo.com/oauth2/authorize"
        webbrowser.open(AUTH_URL + auth_params)

        print("Awaiting authorization code...")
        httpd.handle_request()  # stopper efter første request

        auth_code = httpd.auth_code
        # print(f"\nAuthorization code modtaget:\n{auth_code}")
        return auth_code


