import requests
import json

# API URL
api_url = "http://localhost/workflow/5638KBJRU9Xs0ntk"

# API Key
api_key = "app-Nli22sBKsN0gDdXcBP9aVpnE"

# Request headers
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}

# Request payload
data = {
    "query": "你好",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "abc-123"
}

# Send the POST request
response = requests.post(api_url, headers=headers, data=json.dumps(data))

# Check the response
if response.status_code == 200:
    print("Request successful")
else:
    print(f"Request failed with status code: {response.status_code}")
    print("Error:", response.text)
