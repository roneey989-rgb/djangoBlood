import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS")

    if firebase_json:
        #  For Render (use environment variable)
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
    else:
        #  For Local (use JSON file)
        cred = credentials.Certificate("djangoblood-cb5b2-8cd1c328e3b1.json")

    firebase_admin.initialize_app(cred)


def send_push_notification(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {}
    )

    try:
        response = messaging.send(message)
        print("FCM sent:", response)
    except Exception as e:
        print("FCM error:", e)