import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from collections import deque
import time
import paho.mqtt.client as mqtt
import json

#model choice
MODEL_PATH = '/home/rnguy137/CS131_Final/models/fall_model.tflite'
#MODEL_PATH = '/home/rnguy137/CS131_Final/models/model_ur.tflite'

MQTT_BROKER = "10.0.0.23"  #Mac/Fog IP !!!!
MQTT_TOPIC = "fall/alerts"
CONFIDENCE_THRESHOLD = 0.85 #variable
SEQUENCE_LENGTH = 30

PROCESS_RESOLUTION = (640, 480) #scale down resolution for memory
PREDICT_EVERY_N_FRAMES = 5

#TFLite setup
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("TFLite Model Loaded.")

#MQTT setup
client = mqtt.Client()
try:
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    print("Connected to Fog Node.")
except Exception as e:
    print(f"MQTT connection failed: {e}")

#MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) #adjust these?
mp_drawing = mp.solutions.drawing_utils

def extract_keypoints(results):
    if not results.pose_landmarks:
        return np.zeros(33 * 4) #landmark shape
        
    res = []
    landmarks = results.pose_landmarks.landmark
    center_x, center_y, center_z = 0, 0, 0

    for lm in landmarks:
        res.extend([lm.x - center_x, lm.y - center_y, lm.z - center_z, lm.visibility])
        
    return np.array(res).flatten()

#Camera setup / logic
cap = cv2.VideoCapture(0)
sequence = deque(maxlen=SEQUENCE_LENGTH)

cooldown = 0
frame_counter = 0
fall_prob = 0.0
status = "Normal"
color = (0, 255, 0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame_counter += 1
    frame = cv2.resize(frame, PROCESS_RESOLUTION)

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    keypoints = extract_keypoints(results)
    sequence.append(keypoints)

    #Only run prediction every 5 frames, sequence len 30 (save fps)
    if len(sequence) == SEQUENCE_LENGTH and frame_counter % PREDICT_EVERY_N_FRAMES == 0:
        input_data = np.expand_dims(sequence, axis=0).astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        res = interpreter.get_tensor(output_details[0]['index'])[0]
        fall_prob = res[0]

        if fall_prob > CONFIDENCE_THRESHOLD:
            if cooldown == 0:
                status = "critical_fall"
                color = (0, 0, 255)
                payload = {
                    "device_id": "orin_nano_cam_1", 
                    "status": status,
                    "confidence": float(fall_prob),
                    "timestamp": time.time()
                }
                client.publish(MQTT_TOPIC, json.dumps(payload))
                cooldown = 60 #wait 60 frames / 2 sec between alerts
        else:
            status = "Normal"
            color = (0, 255, 0)
            
    if cooldown > 0:
        cooldown -= 1

    #Edge screen UI (testing only)
    #cv2.rectangle(frame, (0,0), (PROCESS_RESOLUTION[0], 40), (0, 0, 0), -1)
    #cv2.putText(frame, f"Status: {status} ({fall_prob:.2f})", (10,30), 
    #            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

    #cv2.imshow('Fall Detection (ML)', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
