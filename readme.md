"""# 🍇 Dual-Camera YOLO Detection System  

This project implements a **dual-camera real-time detection system** using [Ultralytics YOLOv8](https://docs.ultralytics.com) with **independent camera states**, **serial communication for LED/buzzer control**, and **interactive target selection**.  

The system detects grapes (yellow/black) and sticks, separates detections by camera zones (left, center, right), and provides **visual blinking feedback** per column along with **serial output** for external device control.  

---

## 🚀 Features  

- **Dual-Camera Support** (`/dev/video0`, `/dev/video2`)  
- **Zone-Based Detection** (left, center, right columns)  
- **YOLOv8 Integration** (`last_30_7.pt` model)  
- **Interactive Target Class Selection** via terminal (RED / YELLOW / BLACK)  
- **Blinking Column Highlights** for detected objects  
- **Serial Communication** with external hardware (LED/Buzzer)  
- **Command Handling** from serial input (e.g., switch detection mode remotely)  
- **Restart on-demand** (`q` key or terminal command)  
- **Logging** (`grape_detection.log`)  

---

## 🛠️ Requirements  

- Python 3.10.18  
- Libraries:
  pip install -r requirements.txt
- YOLOv8 trained model file:
  Place your trained weights at:
    /home/katomaran/applications/grapes/30_7/last_30_7.pt
- Two connected cameras:
  - /dev/video0
  - /dev/video2  
- Serial device for buzzer/LED (example: /dev/ttyUSB0)  

---

## 📂 Project Structure  

📁 grapes/30_7
 ├── main.py                 # Main detection script
 ├── usb_controller.py       # Serial port communication
 ├── last_30_7.pt            # YOLOv8 trained model
 ├── grape_detection.log     # Generated logs
 └── missed_frames/          # (Auto-created) Store missed frames if needed

---

## ⚙️ Configuration  

Modify CONFIG in main.py:  

CONFIG = {
    "CONFIDENCE": 0.4,              # YOLO confidence threshold
    "PROCESS_INTERVAL": 1,          # Processing interval in seconds
    "DISPLAY_INTERVAL": 1,          # Display update interval
    "VIDEO_OUTPUT": "inference_output_dual.mp4",  
    "OUTPUT_FPS": 25,
    "BUZZER_PORT": "/dev/ttyUSB0",  # Serial port for buzzer/LED
    "BUZZER_BAUDRATE": 115200,
}

---

## 🎯 Target Selection  

When the program starts, choose detection mode from terminal:  

==================================================
🎯 TARGET CLASS SELECTION
==================================================
Choose target class to detect:
  r - RED
  b - BLACK
  y - YELLOW
  q - QUIT/RESTART
==================================================
Enter your choice and Press Enter (r/b/y/q):

- r → Detect everything except RED  
- b → Detect everything except BLACK  
- y → Detect everything except YELLOW  
- q → Restart the program  

You can also send commands (RED, BLACK, YELLOW) via serial to switch dynamically.  

---

## ▶️ Running  

python main.py

- Press q during runtime → restart program  
- Logs available in: grape_detection.log  

---

## 🖼️ Visual Feedback  

- Left, center, right columns drawn on camera feed  
- Detected zones blink with detected color overlay  
- Object bounding boxes + class labels shown on live video  

---

## 🔌 Serial Communication  

- Outgoing: LED control array [left, center, right]  
- Incoming: Commands to switch detection target (RED / BLACK / YELLOW)  

See usb_controller.py for implementation details.  

---

## 📝 Logs  

Logs are automatically stored in:  

grape_detection.log

Example entry:  

2025-08-19 14:44:42 | INFO | 📱 Raw command received: 'RED' -> normalized: 'RED'
2025-08-19 14:44:42 | INFO | 🎯 [CAM1] Detection will EXCLUDE RED, targeting: BLACK, YELLOW, STICK

---

## 📌 Notes  

- Ensure both cameras (/dev/video0, /dev/video2) are working.  
- Adjust model path (MODEL_PATH) if your weights are stored elsewhere.  
- Serial port must match your hardware setup.  
- Restart loop ensures program never hangs permanently.  
"""