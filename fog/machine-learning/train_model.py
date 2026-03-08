import os
import numpy as np
import tensorflow as tf # Need the main tf library for conversion
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split


# "montreal" or "ur"
CURRENT_DATASET = "montreal"

DATA_PATH = os.path.join("processed_data", CURRENT_DATASET)
MODEL_NAME = f"model_{CURRENT_DATASET}.h5"
TFLITE_NAME = f"model_{CURRENT_DATASET}.tflite"

print(f"Training on: {CURRENT_DATASET}")
print(f"Reading data from: {DATA_PATH}")

actions = ["fall", "adl"]
label_map = {label:num for num, label in enumerate(actions)}

sequences, labels = [], []

# Load Data
for action in actions:
    action_path = os.path.join(DATA_PATH, action)
    if not os.path.exists(action_path):
        print(f"Warning: {action_path} does not exist!")
        continue
        
    for file_name in os.listdir(action_path):
        if file_name.endswith('.npy'):
            window = np.load(os.path.join(action_path, file_name))
            sequences.append(window)
            labels.append(label_map[action])

if len(sequences) == 0:
    print("ERROR: No data found, maybe run process_data.py first?")
    exit()

X = np.array(sequences)
y = to_categorical(labels).astype(int)

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

# Build Model
model = Sequential()
model.add(Input(shape=(30, 132)))
model.add(LSTM(64, return_sequences=True, activation='relu'))
model.add(LSTM(128, return_sequences=False, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(len(actions), activation='softmax'))

model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])

# Train
model.fit(X_train, y_train, epochs=150)

# Save Standard Model
model.save(MODEL_NAME)
print(f"\n SUCCESS: Standard model saved as '{MODEL_NAME}'")

# Convert to TFLite
print("Converting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.target_spec.supported_ops = [
  tf.lite.OpsSet.TFLITE_BUILTINS, 
  tf.lite.OpsSet.SELECT_TF_OPS 
]
converter.optimizations = [tf.lite.Optimize.DEFAULT] 
tflite_model = converter.convert()

# Save TFLite Model
with open(TFLITE_NAME, "wb") as f:
    f.write(tflite_model)
    
print(f"SUCCESS: TFLite model saved as '{TFLITE_NAME}'")
