import requests
import json

try:
    url = "http://localhost:8001/api/query"
    data = {"question": "hola"}
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
