import os
import cv2
import numpy as np
import mediapipe as mp


# "montreal" or "ur"
CURRENT_DATASET = "montreal"

# Path Setup
SOURCE_PATH = os.path.join("raw_videos", CURRENT_DATASET)
OUTPUT_PATH = os.path.join("processed_data", CURRENT_DATASET)

print(f"Processing Dataset: {CURRENT_DATASET}")
print(f"Reading from: {SOURCE_PATH}")
print(f"Saving to:   {OUTPUT_PATH}")

# Classes
ACTIONS = ["fall", "adl"]
SEQUENCE_LENGTH = 30

# Setup MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

for action in ACTIONS:
    action_output_path = os.path.join(OUTPUT_PATH, action)
    os.makedirs(action_output_path, exist_ok=True)
    
    action_source_path = os.path.join(SOURCE_PATH, action)
    
    if not os.path.exists(action_source_path):
        print(f"Source folder not found: {action_source_path}")
        continue

    # Used to find videos within subfolders 
    video_file_paths = []
    print(f"Searching inside '{action}' folders...")
    
    for root, dirs, files in os.walk(action_source_path):
        for file in files:
            if file.lower().endswith(('.avi', '.mp4', '.mov', '.mkv', '.webm')):
                full_path = os.path.join(root, file)
                video_file_paths.append(full_path)

    if len(video_file_paths) == 0:
        print(f"No videos found in {action}. Recheck your folders!")
        continue

    print(f"Found {len(video_file_paths)} videos for '{action}'! Processing...")

    global_sequence_count = 0  
    
    for video_index, video_path in enumerate(video_file_paths):
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            
            if results.pose_landmarks:
                keypoints = []
                for res in results.pose_landmarks.landmark:
                    keypoints.append(np.array([res.x, res.y, res.z, res.visibility]))
                frames.append(np.array(keypoints).flatten())

        cap.release()
        

        if len(frames) >= SEQUENCE_LENGTH:
            num_sequences = len(frames) // SEQUENCE_LENGTH
            
            for i in range(num_sequences):
                window = frames[i*SEQUENCE_LENGTH : (i+1)*SEQUENCE_LENGTH]
                
                save_name = f"{action}_{video_index}_{i}.npy"
                save_path = os.path.join(action_output_path, save_name)
                
                np.save(save_path, np.array(window))
                global_sequence_count += 1
                
        if (video_index + 1) % 10 == 0:
             print(f"Processed {video_index + 1}/{len(video_file_paths)} videos...")

    print(f"Finished {action}: {global_sequence_count} sequences saved.")
