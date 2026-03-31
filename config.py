from requests.auth import HTTPBasicAuth
import requests
import urllib3

BASE_URL = "https://192.168.1.1:443"
USERNAME = "admin"
PASSWORD = "pfsense"
DURATION_BETWEEN_ATTEMPTS = 20

session = requests.Session()
session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
session.headers.update({"Content-Type": "application/json"})
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
