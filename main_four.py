# GOKUL CHANGES

# import cv2
# import numpy as np
# import time
# import logging
# import threading
# import os
# from ultralytics import YOLO
# from queue import Queue

# from usb_controller import (
#     initialize_serial_port,
#     write_led_control,
#     start_serial_listener
# )

# MODEL_PATH = "last_30_7.pt"

# # Camera sources
# CAMERA_SOURCES = {
#     "CAM1": "/dev/video0",
#     "CAM2": "/dev/video2", 
#     "CAM3": "/dev/video4",
#     "CAM4": "/dev/video6"
# }

# # Unified camera configuration for consistency and performance
# CAMERA_CONFIGS = {
#     cam: {"fps": 24, "width": 640, "height": 360, "retry_count": 3}
#     for cam in CAMERA_SOURCES
# }

# # Configurations
# CONFIG = {
#     "CONFIDENCE": 0.4,
#     "PROCESS_INTERVAL": 0.1,  # Faster processing for real-time
#     "DISPLAY_INTERVAL": 0.033,  # ~30 FPS display
#     "VIDEO_OUTPUT": "inference_output_quad.mp4",
#     "OUTPUT_FPS": 24,
#     "BUZZER_PORT": "/dev/ttyUSB0",
#     "BUZZER_BAUDRATE": 115200,
#     "MAX_FRAME_RETRIES": 3,
#     "CAMERA_TIMEOUT": 1.0,
# }

# # Detection states
# STATE = {
#     cam: {"TARGET_CLASSES": ["yellow", "black", "stick"],
#           "current_detection_mode": "RED",
#           "detection_active": True}
#     for cam in CAMERA_SOURCES
# }

# # Blinking states
# BLINK_STATE = {
#     cam: {"columns": [False, False, False],
#           "last_toggle": time.time(),
#           "detected_colors": ["", "", ""]}
#     for cam in CAMERA_SOURCES
# }

# # Thread-safe queues
# CAMERA_QUEUES = {
#     cam: Queue(maxsize=1)  # Smaller queue size to reduce latency
#     for cam in CAMERA_SOURCES
# }

# # Thread control
# THREAD_CONTROL = {
#     "running": True,
#     "lock": threading.Lock()
# }

# # Camera status
# CAMERA_STATUS = {
#     cam: {"initialized": False, "last_frame_time": 0, "error_count": 0, "success_count": 0}
#     for cam in CAMERA_SOURCES
# }

# # Colors
# BOX_COLORS = {
#     "red": (0, 0, 255),
#     "yellow": (0, 255, 255),
#     "black": (0, 0, 0),
#     "stick": (128, 128, 128),
# }
# CLASS_NAME_OVERRIDE = {"brown": "yellow"}

# def select_target_class():
#     """Allow user to select target class via terminal input."""
#     while True:
#         print("\n" + "=" * 50)
#         print("🎯 TARGET CLASS SELECTION")
#         print("  r - RED")
#         print("  b - BLACK")
#         print("  y - YELLOW")
#         print("  q - QUIT/RESTART")
#         choice = input("Enter choice (r/b/y/q): ").lower().strip()
#         if choice in ['r', 'b', 'y']: return choice.upper()
#         elif choice == 'q': return "RESTART"
#         print("❌ Invalid choice! Use r, b, y, or q.")

# def setup_logging():
#     """Setup logging configuration."""
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s | %(levelname)s | %(message)s",
#         handlers=[logging.FileHandler("grape_detection.log"), logging.StreamHandler()]
#     )

# def log_event(msg):
#     """Thread-safe logging."""
#     with THREAD_CONTROL["lock"]:
#         logging.info(msg)

# def update_target_classes(camera, excluded_color):
#     """Update target classes for a specific camera."""
#     all_colors = {"RED": "red", "BLACK": "black", "YELLOW": "yellow", "STICK": "stick"}
#     if excluded_color in all_colors:
#         active_classes = [c for k, c in all_colors.items() if k != excluded_color]
#         with THREAD_CONTROL["lock"]:
#             STATE[camera]["TARGET_CLASSES"] = active_classes
#             STATE[camera]["current_detection_mode"] = excluded_color
#         log_event(f"🎯 [{camera}] Excluding {excluded_color}, targeting: {', '.join(active_classes).upper()}")

# def handle_serial_command(ascii_data):
#     """Handle serial commands for all cameras."""
#     clean_data = ascii_data.strip().upper()
#     color = None
#     if "RED" in clean_data: color = "RED"
#     elif "BLACK" in clean_data: color = "BLACK"
#     elif "YELLOW" in clean_data: color = "YELLOW"
#     if color:
#         for cam in STATE:
#             update_target_classes(cam, color)

# def initialize_yolo_model(path=MODEL_PATH):
#     """Initialize YOLO model with optimized settings."""
#     model = YOLO(path)
#     model.overrides['imgsz'] = 320  # Smaller image size for faster inference
#     log_event(f"✅ YOLOv8 model loaded ({len(model.names)} classes)")
#     return model

# def initialize_video_capture(source, cam_id):
#     """Initialize video capture with optimized settings."""
#     log_event(f"🔧 Initializing {cam_id} ({source})...")
#     try:
#         cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
#         if not cap.isOpened():
#             log_event(f"❌ Could not open camera {source}")
#             return None, 0, 0, 0
        
#         cam_config = CAMERA_CONFIGS[cam_id]
#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_config["width"])
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_config["height"])
#         cap.set(cv2.CAP_PROP_FPS, cam_config["fps"])
#         cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#         cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

#         ret, _ = cap.read()
#         if not ret:
#             log_event(f"❌ {cam_id}: Could not read test frame")
#             cap.release()
#             return None, 0, 0, 0

#         w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fps = int(cap.get(cv2.CAP_PROP_FPS)) or cam_config["fps"]
        
#         log_event(f"✅ {cam_id} initialized: {w}x{h} @ {fps}fps")
#         with THREAD_CONTROL["lock"]:
#             CAMERA_STATUS[cam_id]["initialized"] = True
#         return cap, w, h, fps

#     except Exception as e:
#         log_event(f"❌ Error initializing {cam_id}: {e}")
#         return None, 0, 0, 0

# def read_frame_with_retry(cap, cam_id):
#     """Read frame with retry mechanism."""
#     max_retries = CAMERA_CONFIGS[cam_id]["retry_count"]
#     for attempt in range(max_retries):
#         ret, frame = cap.read()
#         if ret and frame is not None and frame.size > 0:
#             with THREAD_CONTROL["lock"]:
#                 CAMERA_STATUS[cam_id]["success_count"] += 1
#                 CAMERA_STATUS[cam_id]["last_frame_time"] = time.time()
#             return True, frame
#         time.sleep(0.01)
    
#     with THREAD_CONTROL["lock"]:
#         CAMERA_STATUS[cam_id]["error_count"] += 1
#     return False, None

# def process_frame(frame, model, width, cam_id):
#     """Process a single frame with YOLO detection."""
#     results = model(frame, imgsz=320, conf=CONFIG["CONFIDENCE"])  # Faster inference
#     zone_width = width // 3
#     led_control = [0, 0, 0]
#     detected_colors = ["", "", ""]
    
#     with THREAD_CONTROL["lock"]:
#         targets = [c.lower().strip() for c in STATE[cam_id]["TARGET_CLASSES"]]

#     for r in results:
#         for box in r.boxes:
#             cid = int(box.cls[0])
#             cname = CLASS_NAME_OVERRIDE.get(model.names[cid], model.names[cid]).lower().strip()
#             conf = float(box.conf[0])
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
            
#             if cname in targets and conf > CONFIG["CONFIDENCE"]:
#                 cx = (x1 + x2) // 2
#                 line_idx = min(cx // zone_width, 2)
#                 led_control[line_idx] = 1
#                 detected_colors[line_idx] = cname
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLORS.get(cname, (255, 255, 255)), 1)
#                 cv2.putText(frame, f"{cname} ({conf:.2f})", (x1, y1 - 10),
#                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

#     return frame, led_control, any(led_control), detected_colors

# def draw_zone_lines(frame, width, height, cam_id, led_control, detected_colors):
#     """Draw zone lines and indicators."""
#     zone_width = width // 3
#     cv2.line(frame, (zone_width, 0), (zone_width, height), (255, 255, 0), 1)
#     cv2.line(frame, (2 * zone_width, 0), (2 * zone_width, height), (255, 255, 0), 1)

#     current_time = time.time()
#     with THREAD_CONTROL["lock"]:
#         for i, led_state in enumerate(led_control):
#             if led_state:
#                 BLINK_STATE[cam_id]["detected_colors"][i] = detected_colors[i]
#                 if current_time - BLINK_STATE[cam_id]["last_toggle"] > 0.3:
#                     BLINK_STATE[cam_id]["columns"][i] = not BLINK_STATE[cam_id]["columns"][i]
#                     BLINK_STATE[cam_id]["last_toggle"] = current_time
#             else:
#                 BLINK_STATE[cam_id]["columns"][i] = False
#                 BLINK_STATE[cam_id]["detected_colors"][i] = ""

#         for i, is_blinking in enumerate(BLINK_STATE[cam_id]["columns"]):
#             if is_blinking:
#                 x1 = i * zone_width
#                 x2 = (i + 1) * zone_width
#                 color = BOX_COLORS.get(BLINK_STATE[cam_id]["detected_colors"][i], (0, 0, 255))
#                 overlay = frame.copy()
#                 cv2.rectangle(overlay, (x1, 0), (x2, height), color, -1)
#                 cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

#     with THREAD_CONTROL["lock"]:
#         mode = STATE[cam_id]["current_detection_mode"]
#         status = CAMERA_STATUS[cam_id]
    
#     status_text = f"{cam_id} Mode: {mode}"
#     cv2.putText(frame, status_text, (5, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

# def camera_thread(cam_id, source, model, serial_port):
#     """Threaded camera processing."""
#     log_event(f"🚀 Starting thread for {cam_id} ({source})")
#     cap, width, height, fps = initialize_video_capture(source, cam_id)
#     if not cap:
#         return

#     try:
#         while THREAD_CONTROL["running"]:
#             ret, frame = read_frame_with_retry(cap, cam_id)
#             if not ret:
#                 time.sleep(0.05)
#                 continue

#             annotated, led_control, found, detected_colors = process_frame(frame, model, width, cam_id)
#             draw_zone_lines(annotated, width, height, cam_id, led_control, detected_colors)
            
#             if serial_port and found:
#                 with THREAD_CONTROL["lock"]:
#                     write_led_control(serial_port, led_control)
            
#             try:
#                 CAMERA_QUEUES[cam_id].put_nowait({
#                     'frame': annotated,
#                     'timestamp': time.time()
#                 })
#             except:
#                 pass

#             time.sleep(0.005)  # Minimal delay to prevent CPU overload

#     except Exception as e:
#         log_event(f"❌ Error in {cam_id} thread: {e}")
#     finally:
#         cap.release()
#         log_event(f"🔚 {cam_id} thread stopped")

# def display_thread():
#     """Display thread for all camera feeds."""
#     log_event("🖥️ Starting display thread")
#     latest_frames = {}
    
#     try:
#         while THREAD_CONTROL["running"]:
#             for cam_id in CAMERA_SOURCES:
#                 try:
#                     frame_data = CAMERA_QUEUES[cam_id].get_nowait()
#                     latest_frames[cam_id] = frame_data
#                 except:
#                     pass
            
#             for cam_id, frame_data in latest_frames.items():
#                 if 'frame' in frame_data:
#                     cv2.imshow(f"Detection {cam_id}", frame_data['frame'])
            
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 THREAD_CONTROL["running"] = False
#                 break
            
#             time.sleep(CONFIG["DISPLAY_INTERVAL"])
            
#     except Exception as e:
#         log_event(f"❌ Error in display thread: {e}")
#     finally:
#         cv2.destroyAllWindows()
#         log_event("🔚 Display thread stopped")

# def main():
#     """Main function with optimized threaded camera processing."""
#     while True:
#         setup_logging()
#         THREAD_CONTROL["running"] = True
#         for cam_id in CAMERA_STATUS:
#             CAMERA_STATUS[cam_id].update({
#                 "initialized": False,
#                 "last_frame_time": 0,
#                 "error_count": 0,
#                 "success_count": 0
#             })

#         target_class = select_target_class()
#         if target_class == "RESTART":
#             continue

#         for cam in STATE:
#             update_target_classes(cam, target_class)

#         model = initialize_yolo_model()
#         serial_port = None
#         try:
#             serial_port = initialize_serial_port(CONFIG["BUZZER_PORT"], CONFIG["BUZZER_BAUDRATE"])
#             if serial_port:
#                 start_serial_listener(serial_port, handle_serial_command, {"detection_active": True})
#         except Exception as e:
#             log_event(f"⚠️ Serial port error: {e}")

#         for queue in CAMERA_QUEUES.values():
#             while not queue.empty():
#                 queue.get()

#         camera_threads = []
#         for cam_id, source in CAMERA_SOURCES.items():
#             thread = threading.Thread(
#                 target=camera_thread,
#                 args=(cam_id, source, model, serial_port),
#                 daemon=True
#             )
#             thread.start()
#             camera_threads.append(thread)

#         display_thread_obj = threading.Thread(target=display_thread, daemon=True)
#         display_thread_obj.start()

#         try:
#             while THREAD_CONTROL["running"]:
#                 time.sleep(0.1)
#         except KeyboardInterrupt:
#             THREAD_CONTROL["running"] = False

#         for thread in camera_threads:
#             thread.join(timeout=1.0)
#         display_thread_obj.join(timeout=1.0)

#         if serial_port:
#             serial_port.close()
#         log_event("🔚 All threads stopped, restarting...")

# if __name__ == "__main__":
#     main()



# THANA CHANGES


import cv2
import numpy as np
import time
import logging
import threading
import os
from ultralytics import YOLO
from datetime import datetime
from queue import Queue
import copy

from usb_controller import (
    initialize_serial_port,
    write_led_control,
    start_serial_listener
)

MODEL_PATH = "/home/kumar/Katomaran/Projects/colour/lastzip20_8/30_7/last_30_7.pt"

# Cameras (🔹 4 camera sources - using working devices)
CAMERA_SOURCES = {
    "CAM1": "/dev/video0",
    "CAM2": "/dev/video0", 
    "CAM3": "/dev/video0",
    "CAM4": "/dev/video0"
}

# Camera-specific configurations for better stability
CAMERA_CONFIGS = {
    "CAM1": {"fps": 30, "width": 640, "height": 480, "retry_count": 3},
    "CAM2": {"fps": 30, "width": 640, "height": 480, "retry_count": 3},
    "CAM3": {"fps": 15, "width": 640, "height": 480, "retry_count": 5},  # Lower FPS for stability
    "CAM4": {"fps": 15, "width": 640, "height": 480, "retry_count": 5}   # Lower FPS for stability
}

# Configurations
CONFIG = {
    "CONFIDENCE": 0.4,
    "PROCESS_INTERVAL": 1,
    "DISPLAY_INTERVAL": 1,
    "VIDEO_OUTPUT": "inference_output_quad.mp4",
    "OUTPUT_FPS": 5,
    "BUZZER_PORT": "/dev/ttyUSB0",
    "BUZZER_BAUDRATE": 115200,
    "MAX_FRAME_RETRIES": 5,  # Maximum retries for frame reading
    "CAMERA_TIMEOUT": 2.0,   # Camera timeout in seconds
}

# Independent detection states for each camera
STATE = {
    cam: {"TARGET_CLASSES": ["yellow", "black", "stick"],
          "current_detection_mode": "RED",
          "detection_active": True}
    for cam in CAMERA_SOURCES
}

# Blinking states for all cameras
BLINK_STATE = {
    cam: {"columns": [False, False, False],
          "last_toggle": time.time(),
          "detected_colors": ["", "", ""]}
    for cam in CAMERA_SOURCES
}

# Thread-safe queues for each camera
CAMERA_QUEUES = {
    cam: Queue(maxsize=2)  # Limit queue size to prevent memory issues
    for cam in CAMERA_SOURCES
}

# Thread control flags
THREAD_CONTROL = {
    "running": True,
    "lock": threading.Lock()  # Thread-safe lock for shared resources
}

# Camera status tracking
CAMERA_STATUS = {
    cam: {"initialized": False, "last_frame_time": 0, "error_count": 0, "success_count": 0}
    for cam in CAMERA_SOURCES
}

# Colors
BOX_COLORS = {
    "red": (0, 0, 255),
    "yellow": (0, 255, 255),
    "black": (0, 0, 0),
    "stick": (128, 128, 128),
}
CLASS_NAME_OVERRIDE = {"brown": "yellow"}


def select_target_class():
    """Allow user to select target class via terminal input."""
    while True:
        print("\n" + "=" * 50)
        print("🎯 TARGET CLASS SELECTION")
        print("=" * 50)
        print("Choose target class to detect:")
        print("  r - RED")
        print("  b - BLACK")
        print("  y - YELLOW")
        print("  q - QUIT/RESTART")
        print("=" * 50)

        choice = input("Enter your choice and Press Enter (r/b/y/q): ").lower().strip()

        if choice == 'r': return "RED"
        elif choice == 'b': return "BLACK"
        elif choice == 'y': return "YELLOW"
        elif choice == 'q':
            print("🔄 Restarting program...")
            return "RESTART"
        else:
            print("❌ Invalid choice! Please enter r, b, y, or q.")


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler("grape_detection.log"), logging.StreamHandler()]
    )


def log_event(msg): 
    """Thread-safe logging."""
    with THREAD_CONTROL["lock"]:
        logging.info(msg)


def update_target_classes(camera, excluded_color):
    """Update target classes for a specific camera."""
    all_colors = {"RED": "red", "BLACK": "black", "YELLOW": "yellow", "STICK": "stick"}
    if excluded_color in all_colors:
        active_classes = [c for k, c in all_colors.items() if k != excluded_color]
        with THREAD_CONTROL["lock"]:
            STATE[camera]["TARGET_CLASSES"] = active_classes
            STATE[camera]["current_detection_mode"] = excluded_color
        log_event(f"🎯 [{camera}] Detection will EXCLUDE {excluded_color}, targeting: {', '.join(active_classes).upper()}")


def handle_serial_command(ascii_data):
    """Handle serial commands and apply to all cameras."""
    clean_data = ascii_data.strip().upper()
    log_event(f"📱 Raw command received: '{ascii_data}' -> normalized: '{clean_data}'")
    color = None
    if "RED" in clean_data: color = "RED"
    elif "BLACK" in clean_data: color = "BLACK"
    elif "YELLOW" in clean_data: color = "YELLOW"
    if color:
        for cam in STATE:
            update_target_classes(cam, color)


def initialize_yolo_model(path=MODEL_PATH):
    """Initialize YOLO model."""
    model = YOLO(path)
    log_event(f"✅ YOLOv8 model loaded ({len(model.names)} classes)")
    return model


def initialize_video_capture(source, cam_id):
    """Initialize video capture for a camera source with improved error handling."""
    log_event(f"🔧 Initializing {cam_id} ({source}) with custom settings...")
    
    try:
        cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        if not cap.isOpened():
            log_event(f"❌ Could not open camera {source}")
            return None, 0, 0, 0
        
        # Get camera-specific configuration
        cam_config = CAMERA_CONFIGS.get(cam_id, {"fps": 30, "width": 640, "height": 480, "retry_count": 3})
        
        # Set camera properties for better stability
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_config["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_config["height"])
        cap.set(cv2.CAP_PROP_FPS, cam_config["fps"])
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
        
        # Additional settings for problematic cameras
        if cam_id in ["CAM3", "CAM4"]:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
        
        # Read a test frame to verify camera is working
        ret, test_frame = cap.read()
        if not ret:
            log_event(f"❌ {cam_id}: Could not read test frame")
            cap.release()
            return None, 0, 0, 0
        
        # Get actual camera properties
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or cam_config["fps"]
        
        log_event(f"✅ {cam_id} ({source}) initialized: {w}x{h} @ {fps}fps")
        
        # Update camera status
        with THREAD_CONTROL["lock"]:
            CAMERA_STATUS[cam_id]["initialized"] = True
        
        return cap, w, h, fps
        
    except Exception as e:
        log_event(f"❌ Error initializing {cam_id}: {e}")
        return None, 0, 0, 0


def read_frame_with_retry(cap, cam_id, max_retries=None):
    """Read frame with retry mechanism for better reliability."""
    if max_retries is None:
        max_retries = CAMERA_CONFIGS.get(cam_id, {}).get("retry_count", 3)
    
    for attempt in range(max_retries):
        try:
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                # Update success count
                with THREAD_CONTROL["lock"]:
                    CAMERA_STATUS[cam_id]["success_count"] += 1
                    CAMERA_STATUS[cam_id]["last_frame_time"] = time.time()
                return True, frame
            
            # Small delay before retry
            time.sleep(0.01)
            
        except Exception as e:
            log_event(f"⚠️ {cam_id} frame read error (attempt {attempt + 1}): {e}")
            time.sleep(0.05)  # Longer delay on error
    
    # Update error count
    with THREAD_CONTROL["lock"]:
        CAMERA_STATUS[cam_id]["error_count"] += 1
    
    return False, None


def process_frame(frame, model, width, cam_id):
    """Process a single frame with YOLO detection."""
    annotated = frame.copy()
    results = model(annotated, imgsz=600)

    zone_width = width // 3
    led_control, found = [0, 0, 0], False
    detected_colors = ["", "", ""]
    
    # Get target classes safely
    with THREAD_CONTROL["lock"]:
        targets = [c.lower().strip() for c in STATE[cam_id]["TARGET_CLASSES"]]

    for r in results:
        for box in r.boxes:
            cid = int(box.cls[0])
            cname = CLASS_NAME_OVERRIDE.get(model.names[cid], model.names[cid]).lower().strip()
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), BOX_COLORS.get(cname, (255, 255, 255)), 2)
            cv2.putText(annotated, f"{cname} ({conf:.2f})", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Check if detection matches target classes
            if cname in targets and conf > CONFIG["CONFIDENCE"]:
                cx = (x1 + x2) // 2
                line_idx = min(cx // zone_width, 2)
                led_control[line_idx], found = 1, True
                detected_colors[line_idx] = cname
                log_event(f"✅ [{cam_id}] MATCH: {cname.upper()} in line {line_idx + 1}")

    return annotated, led_control, found, detected_colors


def draw_zone_lines(frame, width, height, cam_id, led_control, detected_colors):
    """Draw zone lines and blinking indicators on frame."""
    zone_width = width // 3
    
    # Draw zone separator lines
    cv2.line(frame, (zone_width, 0), (zone_width, height), (255, 255, 0), 2)
    cv2.line(frame, (2 * zone_width, 0), (2 * zone_width, height), (255, 255, 0), 2)

    current_time = time.time()
    blink_interval = 0.5

    # Update blinking state safely
    with THREAD_CONTROL["lock"]:
        for i, led_state in enumerate(led_control):
            if led_state == 1:
                BLINK_STATE[cam_id]["detected_colors"][i] = detected_colors[i]
                if current_time - BLINK_STATE[cam_id]["last_toggle"] > blink_interval:
                    BLINK_STATE[cam_id]["columns"][i] = not BLINK_STATE[cam_id]["columns"][i]
                    BLINK_STATE[cam_id]["last_toggle"] = current_time
            else:
                BLINK_STATE[cam_id]["columns"][i] = False
                BLINK_STATE[cam_id]["detected_colors"][i] = ""

        # Draw blinking columns
        for i, is_blinking in enumerate(BLINK_STATE[cam_id]["columns"]):
            if is_blinking:
                if i == 0: x1, x2 = 0, zone_width
                elif i == 1: x1, x2 = zone_width, 2 * zone_width
                else: x1, x2 = 2 * zone_width, width

                detected_color = BLINK_STATE[cam_id]["detected_colors"][i]
                color = BOX_COLORS.get(detected_color, (0, 0, 255))
                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, 0), (x2, height), color, -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    # Display camera mode and status
    with THREAD_CONTROL["lock"]:
        mode = STATE[cam_id]['current_detection_mode']
        status = CAMERA_STATUS[cam_id]
    
    # Add status information to frame
    status_text = f"{cam_id} Mode: {mode}"
    cv2.putText(frame, status_text, (10, height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Add error/success count
    error_rate = status["error_count"] / max(status["success_count"] + status["error_count"], 1) * 100
    status_text2 = f"Errors: {status['error_count']} ({error_rate:.1f}%)"
    cv2.putText(frame, status_text2, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)


def camera_thread(cam_id, source, model, serial_port):
    """
    🔄 THREADED CAMERA PROCESSING FUNCTION
    
    This function runs in a separate thread for each camera and handles:
    - Continuous frame capture with retry mechanism
    - YOLO object detection
    - Frame processing and annotation
    - Queue management for thread-safe communication
    """
    log_event(f"🚀 Starting thread for {cam_id} ({source})")
    
    # Initialize camera with improved settings
    cap, width, height, fps = initialize_video_capture(source, cam_id)
    if not cap:
        log_event(f"❌ Failed to initialize {cam_id}")
        return

    frame_count = 0
    last_process_time = time.time()
    consecutive_failures = 0
    max_consecutive_failures = 10
    
    try:
        while THREAD_CONTROL["running"]:
            # Read frame with retry mechanism
            ret, frame = read_frame_with_retry(cap, cam_id)
            
            if not ret:
                consecutive_failures += 1
                if consecutive_failures > max_consecutive_failures:
                    log_event(f"⚠️ {cam_id}: Too many consecutive failures, pausing...")
                    time.sleep(1.0)  # Longer pause
                    consecutive_failures = 0
                else:
                    time.sleep(0.1)
                continue
            
            consecutive_failures = 0  # Reset on success
            frame_count += 1
            current_time = time.time()
            
            # Process frame at specified interval
            if current_time - last_process_time >= CONFIG["PROCESS_INTERVAL"]:
                # Process frame with YOLO
                annotated, led_control, found, detected_colors = process_frame(
                    frame, model, width, cam_id
                )
                
                # Draw zone lines and indicators
                draw_zone_lines(annotated, width, height, cam_id, led_control, detected_colors)
                
                # Send LED control to serial port (thread-safe)
                if serial_port and found:
                    with THREAD_CONTROL["lock"]:
                        write_led_control(serial_port, led_control)
                
                # Put processed frame in queue for display
                try:
                    CAMERA_QUEUES[cam_id].put_nowait({
                        'frame': annotated,
                        'led_control': led_control,
                        'found': found,
                        'detected_colors': detected_colors,
                        'timestamp': current_time
                    })
                except:
                    # Queue is full, skip this frame
                    pass
                
                last_process_time = current_time
                
                # Log processing stats
                if frame_count % 30 == 0:  # Log every 30 frames
                    with THREAD_CONTROL["lock"]:
                        status = CAMERA_STATUS[cam_id]
                    log_event(f"📊 [{cam_id}] Processed {frame_count} frames, Errors: {status['error_count']}")
            
            # Adaptive delay based on camera performance
            if cam_id in ["CAM3", "CAM4"]:
                time.sleep(0.02)  # Longer delay for problematic cameras
            else:
                time.sleep(0.01)
            
    except Exception as e:
        log_event(f"❌ Error in {cam_id} thread: {e}")
    finally:
        cap.release()
        log_event(f"🔚 {cam_id} thread stopped")


def display_thread():
    """
    🖥️ DISPLAY THREAD FUNCTION
    
    This function handles displaying all camera feeds in separate windows.
    It reads from the camera queues and displays frames when available.
    """
    log_event("🖥️ Starting display thread")
    
    # Store latest frames from each camera
    latest_frames = {}
    
    try:
        while THREAD_CONTROL["running"]:
            # Check each camera queue for new frames
            for cam_id in CAMERA_SOURCES:
                try:
                    # Get frame from queue (non-blocking)
                    frame_data = CAMERA_QUEUES[cam_id].get_nowait()
                    latest_frames[cam_id] = frame_data
                except:
                    # No new frame available, use previous one if exists
                    pass
            
            # Display all available frames
            for cam_id, frame_data in latest_frames.items():
                if 'frame' in frame_data:
                    cv2.imshow(f"Detection {cam_id}", frame_data['frame'])
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                log_event("🔄 'q' pressed - stopping all threads")
                THREAD_CONTROL["running"] = False
                break
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.03)  # ~30 FPS display rate
            
    except Exception as e:
        log_event(f"❌ Error in display thread: {e}")
    finally:
        cv2.destroyAllWindows()
        log_event("🔚 Display thread stopped")


def main():
    """Main function with threaded camera processing."""
    while True:  # Main restart loop
        setup_logging()
        os.makedirs("missed_frames", exist_ok=True)

        # Reset thread control and camera status
        THREAD_CONTROL["running"] = True
        for cam_id in CAMERA_STATUS:
            CAMERA_STATUS[cam_id].update({
                "initialized": False,
                "last_frame_time": 0,
                "error_count": 0,
                "success_count": 0
            })

        # Get target class selection from user
        target_class = select_target_class()
        if target_class == "RESTART":
            print("🔄 Restarting program...")
            continue

        # Update target classes for all cameras
        for cam in STATE:
            update_target_classes(cam, target_class)

        # Initialize YOLO model and serial port
        model = initialize_yolo_model()
        
        # Try to initialize serial port (optional)
        serial_port = None
        try:
            serial_port = initialize_serial_port(CONFIG["BUZZER_PORT"], CONFIG["BUZZER_BAUDRATE"])
            if serial_port:
                start_serial_listener(serial_port, handle_serial_command, {"detection_active": True})
                log_event("🔔 Serial port initialized successfully")
            else:
                log_event("⚠️ Serial port not available - continuing without LED control")
        except Exception as e:
            log_event(f"⚠️ Serial port error: {e} - continuing without LED control")

        # Clear all camera queues
        for queue in CAMERA_QUEUES.values():
            while not queue.empty():
                queue.get()

        log_event(f"🚀 Starting 4-camera threaded detection for {target_class}")

        # Create and start camera threads
        camera_threads = []
        working_cameras = 0
        
        for cam_id, source in CAMERA_SOURCES.items():
            thread = threading.Thread(
                target=camera_thread,
                args=(cam_id, source, model, serial_port),
                daemon=True
            )
            thread.start()
            camera_threads.append(thread)
            log_event(f"📷 Started thread for {cam_id}")
            working_cameras += 1
        
        if working_cameras == 0:
            log_event("❌ No cameras could be initialized. Please check camera connections.")
            print("❌ No cameras working. Press Enter to restart...")
            input()
            continue

        # Start display thread
        display_thread_obj = threading.Thread(target=display_thread, daemon=True)
        display_thread_obj.start()
        log_event("🖥️ Started display thread")

        # Wait for threads to complete
        try:
            while THREAD_CONTROL["running"]:
                time.sleep(0.1)
        except KeyboardInterrupt:
            log_event("⚠️ Keyboard interrupt received")
            THREAD_CONTROL["running"] = False

        # Wait for all threads to finish
        log_event("⏳ Waiting for threads to finish...")
        for thread in camera_threads:
            thread.join(timeout=2.0)
        
        display_thread_obj.join(timeout=2.0)

        # Cleanup
        if serial_port:
            serial_port.close()
        
        log_event("🔚 All threads stopped, restarting program...")
        print("🔄 Restarting program...")


if __name__ == "__main__":
    main()