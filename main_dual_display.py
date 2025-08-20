import cv2
import numpy as np
import time
import logging
import threading
import os
from ultralytics import YOLO
from datetime import datetime

from usb_controller import (
    initialize_serial_port,
    write_led_control,
    start_serial_listener
)

MODEL_PATH = "/home/katomaran/applications/grapes/30_7/last_30_7.pt"

# Cameras
CAMERA_SOURCES = {
    "CAM1": "/dev/video0",   # first camera
    "CAM2": "/dev/video2"    # second camera
}

# Configurations (shared thresholds, but cameras have independent states)
CONFIG = {
    "CONFIDENCE": 0.4,
    "PROCESS_INTERVAL": 1,
    "DISPLAY_INTERVAL": 1,
    "VIDEO_OUTPUT": "inference_output_dual.mp4",
    "OUTPUT_FPS": 25,
    "BUZZER_PORT": "/dev/ttyUSB0",
    "BUZZER_BAUDRATE": 115200,
}

# Independent detection states for each camera
STATE = {
    "CAM1": {"TARGET_CLASSES": ["yellow", "black", "stick"], "current_detection_mode": "RED", "detection_active": True},
    "CAM2": {"TARGET_CLASSES": ["yellow", "black", "stick"], "current_detection_mode": "RED", "detection_active": True},
}

# Blinking state for columns (0, 1, 2 for left, center, right columns)
BLINK_STATE = {
    "CAM1": {"columns": [False, False, False], "last_toggle": time.time(), "detected_colors": ["", "", ""]},
    "CAM2": {"columns": [False, False, False], "last_toggle": time.time(), "detected_colors": ["", "", ""]}
}

# Colors
BOX_COLORS = {
    "red": (0, 0, 255),
    "yellow": (0, 255, 255),
    "black": (0, 0, 0),
    "stick": (128, 128, 128),
}

CLASS_NAME_OVERRIDE = {"brown": "yellow"}

# Target class selection
def select_target_class():
    """Allow user to select target class via terminal input."""
    while True:
        print("\n" + "="*50)
        print("🎯 TARGET CLASS SELECTION")
        print("="*50)
        print("Choose target class to detect:")
        print("  r - RED")
        print("  b - BLACK") 
        print("  y - YELLOW")
        print("  q - QUIT/RESTART")
        print("="*50)
        
        choice = input("Enter your choice and Press Enter (r/b/y/q): ").lower().strip()
        
        if choice == 'r':
            return "RED"
        elif choice == 'b':
            return "BLACK"
        elif choice == 'y':
            return "YELLOW"
        elif choice == 'q':
            print("🔄 Restarting program...")
            return "RESTART"
        else:
            print("❌ Invalid choice! Please enter r, b, y, or q.")

# Logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler("grape_detection.log"), logging.StreamHandler()]
    )

def log_event(msg): logging.info(msg)

# Update target classes
def update_target_classes(camera, excluded_color):
    all_colors = {"RED": "red", "BLACK": "black", "YELLOW": "yellow", "STICK": "stick"}
    if excluded_color in all_colors:
        active_classes = [c for k, c in all_colors.items() if k != excluded_color]
        STATE[camera]["TARGET_CLASSES"] = active_classes
        STATE[camera]["current_detection_mode"] = excluded_color
        log_event(f"🎯 [{camera}] Detection will EXCLUDE {excluded_color}, targeting: {', '.join(active_classes).upper()}")

# Handle serial commands → apply to both cameras
def handle_serial_command(ascii_data):
    clean_data = ascii_data.strip().upper()
    log_event(f"📱 Raw command received: '{ascii_data}' -> normalized: '{clean_data}'")
    color = None
    if "RED" in clean_data: color = "RED"
    elif "BLACK" in clean_data: color = "BLACK"
    elif "YELLOW" in clean_data: color = "YELLOW"
    if color:
        for cam in STATE:
            update_target_classes(cam, color)

# Initialize model
def initialize_yolo_model(path=MODEL_PATH):
    model = YOLO(path)
    log_event(f"✅ YOLOv8 model loaded ({len(model.names)} classes)")
    return model

# Initialize capture
def initialize_video_capture(source):
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
    if not cap.isOpened():
        logging.critical(f"❌ Could not open camera {source}")
        return None, 0, 0, 0
    w, h, fps = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FPS)) or 30
    log_event(f"📷 Camera {source} opened: {w}x{h} {fps}fps")
    return cap, w, h, fps

# Process frame
def process_frame(frame, model, width, cam_id):
    annotated = frame.copy()
    results = model(annotated, imgsz=600)

    zone_width = width // 3
    led_control, found = [0,0,0], False
    detected_colors = ["", "", ""]  # Track colors for each zone
    targets = [c.lower().strip() for c in STATE[cam_id]["TARGET_CLASSES"]]

    for r in results:
        for box in r.boxes:
            cid = int(box.cls[0])
            cname = CLASS_NAME_OVERRIDE.get(model.names[cid], model.names[cid]).lower().strip()
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), BOX_COLORS.get(cname, (255,255,255)), 2)
            cv2.putText(annotated, f"{cname} ({conf:.2f})", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

            if cname in targets and conf > CONFIG["CONFIDENCE"]:
                cx, line_idx = (x1+x2)//2, min(((x1+x2)//2)//zone_width, 2)
                led_control[line_idx], found = 1, True
                detected_colors[line_idx] = cname  # Store the detected color
                log_event(f"✅ [{cam_id}] MATCH: {cname.upper()} in line {line_idx+1}")
    
    return annotated, led_control, found, detected_colors

# Draw guides and blinking columns
def draw_zone_lines(frame, width, height, cam_id, led_control, detected_colors):
    zone_width = width // 3
    
    # Draw zone separator lines
    cv2.line(frame,(zone_width,0),(zone_width,height),(255,255,0),2)
    cv2.line(frame,(2*zone_width,0),(2*zone_width,height),(255,255,0),2)
    
    # Update blinking state based on detection
    current_time = time.time()
    blink_interval = 0.5  # Blink every 0.5 seconds
    
    for i, led_state in enumerate(led_control):
        if led_state == 1:  # Detection active in this zone
            # Update detected color for this zone
            BLINK_STATE[cam_id]["detected_colors"][i] = detected_colors[i]
            # Toggle blink state
            if current_time - BLINK_STATE[cam_id]["last_toggle"] > blink_interval:
                BLINK_STATE[cam_id]["columns"][i] = not BLINK_STATE[cam_id]["columns"][i]
                BLINK_STATE[cam_id]["last_toggle"] = current_time
        else:
            # No detection, turn off blinking and clear color
            BLINK_STATE[cam_id]["columns"][i] = False
            BLINK_STATE[cam_id]["detected_colors"][i] = ""
    
    # Draw blinking columns with detected colors
    for i, is_blinking in enumerate(BLINK_STATE[cam_id]["columns"]):
        if is_blinking:
            # Calculate column boundaries
            if i == 0:  # Left column
                x1, x2 = 0, zone_width
            elif i == 1:  # Center column
                x1, x2 = zone_width, 2 * zone_width
            else:  # Right column
                x1, x2 = 2 * zone_width, width
            
            # Get the color for this zone
            detected_color = BLINK_STATE[cam_id]["detected_colors"][i]
            if detected_color in BOX_COLORS:
                color = BOX_COLORS[detected_color]
            else:
                color = (0, 0, 255)  # Default red if color not found
            
            # Draw semi-transparent overlay with detected color
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, 0), (x2, height), color, -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
    
    cv2.putText(frame,f"{cam_id} Mode: {STATE[cam_id]['current_detection_mode']}",(10,height-20),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

# Main loop
def main():
    while True:  # Main restart loop
        setup_logging()
        os.makedirs("missed_frames", exist_ok=True)

        # Get target class selection from user
        target_class = select_target_class()
        if target_class == "RESTART":
            print("🔄 Restarting program...")
            continue

        # Update target classes for both cameras based on selection
        for cam in STATE:
            update_target_classes(cam, target_class)

        model = initialize_yolo_model()
        serial_port = initialize_serial_port(CONFIG["BUZZER_PORT"], CONFIG["BUZZER_BAUDRATE"])
        if serial_port: start_serial_listener(serial_port, handle_serial_command, {"detection_active": True})

        caps, widths, heights = {}, {}, {}
        for cam, src in CAMERA_SOURCES.items():
            cap, w, h, fps = initialize_video_capture(src)
            if cap: caps[cam], widths[cam], heights[cam] = cap, w, h

        log_event(f"🚀 Starting dual-camera detection for {target_class}")
        
        # Detection loop
        while True:
            for cam_id, cap in caps.items():
                ret, frame = cap.read()
                if not ret: continue
                annotated, leds, found, detected_colors = process_frame(frame, model, widths[cam_id], cam_id)
                if serial_port: write_led_control(serial_port, leds)
                draw_zone_lines(annotated, widths[cam_id], heights[cam_id], cam_id, leds, detected_colors)
                cv2.imshow(f"Detection {cam_id}", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): 
                print("🔄 Press 'q' detected - restarting program...")
                break

        # Cleanup before restart
        for cap in caps.values(): cap.release()
        cv2.destroyAllWindows()
        if serial_port: serial_port.close()
        
        print("🔄 Restarting program...")

if __name__ == "__main__":
    main()
