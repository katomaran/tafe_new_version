
# import serial
# import logging
# import time
# import threading

# def initialize_serial_port(port, baudrate, timeout=3):
#     """Initialize serial port."""
#     try:
#         ser = serial.Serial(port, baudrate, timeout=timeout)
#         logging.info(f"🔔 Serial port opened on {port} at {baudrate} baudrate.")
#         return ser
#     except Exception as e:
#         logging.warning(f"⚠️ Could not open serial port: {e}")
#         return None

# def read_serial_command(ser):
#     """Read a line from serial port and return as string."""
#     try:
#         if ser and ser.in_waiting:
#             ascii_data = ser.readline().decode('utf-8', errors='ignore').strip()
#             logging.info(f"📩 Received string: '{ascii_data}'")
#             return ascii_data
#     except Exception as e:
#         logging.error(f"❌ Error reading serial data: {e}")
#     return None

# def write_led_control(ser, led_control):
#     """Write LED control array to serial port."""
#     try:
#         if ser:
#             ser.write(bytes(led_control))
#             logging.info(f"🔁 LED signal sent: {led_control}")
#     except Exception as e:
#         logging.error(f"❌ Error sending LED array: {e}")

# def close_serial_port(ser):
#     """Close serial port safely."""
#     try:
#         if ser:
#             ser.close()
#             logging.info("🔌 Serial connection closed.")
#     except Exception:
#         pass

# def start_serial_listener(ser, callback, state_flag):
#     """
#     Start a thread to listen for serial commands and call the callback with received data.
#     - ser: serial port object
#     - callback: function to call with received command
#     - state_flag: a dict with a 'detection_active' key to control thread exit
#     """
#     def listener():
#         logging.info("📱 Serial command listener started (usb_controller)")
#         while state_flag.get("detection_active", True):
#             ascii_data = read_serial_command(ser)
#             print("````````````````````````````````````````````````````````````````````````````````````````````")
#             if ascii_data:
#                 print(f"data recived from----------------{ascii_data}--------------------------------------------------")
#                 callback(ascii_data)
#                 # update_target_classes_one(ascii_data)
#                 # update_target_classes(ascii_data)

#             time.sleep(0.1)
#         close_serial_port(ser)
#         logging.info("📱 Serial connection closed (usb_controller)")

#     thread = threading.Thread(target=listener, daemon=True)
#     thread.start()
#     return thread





import serial
import logging
import time
import threading

def initialize_serial_port(port, baudrate, timeout=3):
    """Initialize serial port."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        logging.info(f"🔔 Serial port opened on {port} at {baudrate} baudrate.")
        return ser
    except Exception as e:
        logging.warning(f"⚠️ Could not open serial port: {e}")
        return None

def read_serial_command(ser):
    """Read a line from serial port and return as string."""
    try:
        if ser and ser.in_waiting:
            ascii_data = ser.readline().decode('utf-8', errors='ignore').strip()
            logging.info(f"📩 Received string: '{ascii_data}'")
            return ascii_data
    except Exception as e:
        logging.error(f"❌ Error reading serial data: {e}")
    return None

def write_led_control(ser, led_control):
    """Write LED control array to serial port in format '0,1,0'."""
    try:
        if ser:
            # Convert array to comma-separated string format
            data_string = ",".join(map(str, led_control)) + "\n"
            ser.write(data_string.encode('utf-8'))
            logging.info(f"🔁 Data signal sent: {data_string.strip()}")
    except Exception as e:
        logging.error(f"❌ Error sending data: {e}")

def close_serial_port(ser):
    """Close serial port safely."""
    try:
        if ser:
            ser.close()
            logging.info("🔌 Serial connection closed.")
    except Exception:
        pass

def start_serial_listener(ser, callback, state_flag):
    """
    Start a thread to listen for serial commands and call the callback with received data.
    - ser: serial port object
    - callback: function to call with received command
    - state_flag: a dict with a 'detection_active' key to control thread exit
    """
    def listener():
        logging.info("📱 Serial command listener started (usb_controller)")
        while state_flag.get("detection_active", True):
            ascii_data = read_serial_command(ser)
            print("````````````````````````````````````````````````````````````````````````````````````````````")
            if ascii_data:
                print(f"data recived from----------------{ascii_data}--------------------------------------------------")
                callback(ascii_data)
                # update_target_classes_one(ascii_data)
                # update_target_classes(ascii_data)

            time.sleep(0.1)
        close_serial_port(ser)
        logging.info("📱 Serial connection closed (usb_controller)")

    thread = threading.Thread(target=listener, daemon=True)
    thread.start()
    return thread