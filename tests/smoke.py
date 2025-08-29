import requests
BASE = "http://127.0.0.1:5000"
print("/health ->", requests.get(f"{BASE}/health").json())
