# utils.py
import requests
from django.conf import settings

def send_line_message(user_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    print('🔁 LINE API response:', response.status_code, response.text)
    return response.json()
