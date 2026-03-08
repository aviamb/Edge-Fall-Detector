# Edge-based Fall Detection System

Falls among the elderly are a leading cause of fatal injury, 
with prolonged response times significantly increasing mortality rates. 
Current monitoring solutions rely either on wearable devices, 
which suffer from low user compliance, or cloud-based vision systems, 
which introduce severe privacy risks, high network bandwidth consumption, 
and potentially fatal latency delays. This project proposes a decentralized 
Edge-Fog-Cloud IoT architecture for real-time fall detection. By using
an NVIDIA Jetson Orin Nano for local Machine Learning inference via MediaPipe 
skeletal tracking, the system achieves a 93.7% recall rate in detecting falls. 
Moving processing to the Edge reduces network bandwidth consumption by over 
99.9% compared to video streaming and ensures raw video never leaves the room. 
A local Fog node manages escalation, dropping alert latency to a 55ms average, 
while a Cloud layer asynchronously handles remote AWS notifications and 
long-term Firebase analytics. The results demonstrate a highly scalable, 
privacy-preserving framework for next-generation healthcare IoT.

