import paho.mqtt.client as mqtt
import paho.mqtt.publish as paho_publish
import json
import time
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import boto3

load_dotenv() 

#Firebase configuration
print("Connecting to Google Cloud Firebase")
cred = credentials.Certificate("firebase_key.json") #ignore this file!!!!
firebase_admin.initialize_app(cred)
db = firestore.client()

#AWS configuration
print("Connecting to AWS SNS")
AWS_REGION = "us-east-2" #match to AWS console region
SNS_TOPIC_ARN = "arn:aws:sns:us-east-2:296651897670:FallAlerts"
sns_client = boto3.client( #pull from .env, secret!!!!
    "sns",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION
)

#MQTT configuration
MQTT_BROKER = "localhost" #MQTT Broker IP Address (keep consistent with alarm.py)
MQTT_TOPIC = "fall/alerts"

def on_connect(client, userdata, flags, rc):
    print("Fog Node connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    confidence = payload.get('confidence', 0)
    print(f"\nFall Detected with {confidence*100:.0f}% confidence.")
    
    #Trigger secondary edge device 
    try:
        paho_publish.single("alarm/trigger", "Fall Detected! Please check on the patient.", hostname="127.0.0.1")
        print("Alert sent to local alarm.")
    except Exception as e:
        print(f"Failed to alert local alarm: {e}")

    #Firebase logging
    try:
        db.collection('fall_events').add({
            'device_id': payload.get('device_id', 'unknown_cam'),
            'confidence': confidence,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'critical_fall'
        })
        print("Event logged to Firebase Firestore")
    except Exception as e:
        print(f"Firebase Error: {e}")

    #AWS SNS notification
    try:
        message = f"ATTENTION: Fall detected by {payload.get('device_id')} with {confidence*100:.0f}% confidence. Please check on patient immediately."
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message
        )
        print("SNS notification sent to caregivers.")
    except Exception as e:
        print(f"AWS SNS Error: {e}")


#MQTT client configuration
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()