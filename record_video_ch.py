import cv2
import time
# add some import
import threading
import serial
import csv
import datetime
import os
from cms50d import CMS50D


import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
print("Available ports:")
for p in ports:
    print(p)

# check serial port 
try:
    ser = serial.Serial("COM9", baudrate=9600, timeout=1)
    print("Serial port opened successfully")
    ser.close()
except Exception as e:
    print(f"Failed to open serial port: {e}")

# create a file
OUTPUT_DIR = "recording_file"
VIDEO_FILENAME = os.path.join(OUTPUT_DIR, "output.avi")
CSV_FILENAME = os.path.join(OUTPUT_DIR, "pulse_log.csv")
SERIAL_PORT = 'COM9' 

baudrate = 9600
target_fps = 20.0
frame_interval = 1.0 / target_fps  # 0.05seconds
duration = 60  # recording time
frame_width = 640
frame_height = 480

os.makedirs(OUTPUT_DIR, exist_ok=True)

hr_records = []
frame_count = 0  # Added: define frame_count for use in finally block

# Initialize PPG device
try:
    monitor = CMS50D(port=SERIAL_PORT)
    monitor.connect()
    monitor.start_live_acquisition()
    print("PPG acquisition started.")
except Exception as e:
    print(f"Failed to initialize CMS50D: {e}")
    monitor = None

# Initialize video capture and writer
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(VIDEO_FILENAME, fourcc, target_fps, (frame_width, frame_height))

print("Recording at 20 FPS...")

# Modified: use try-except-finally to ensure proper cleanup on Ctrl+C
try:
    start_time = time.time()

    while time.time() - start_time < duration:
        loop_start = time.time()

        ret, frame = cap.read()
        if not ret:
            print("Frame capture failed.")
            break

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        cv2.putText(frame, timestamp[:-3], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        out.write(frame)

        if monitor:
            data = monitor.get_latest_data()
            pulse_rate = data['pulse_rate'] if data else 0
        else:
            pulse_rate = 0

        hr_records.append([timestamp, pulse_rate])
        frame_count += 1

        cv2.imshow('Recording', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Recording stopped by user.")
            break

        elapsed = time.time() - loop_start
        time_to_wait = frame_interval - elapsed
        if time_to_wait > 0:
            time.sleep(time_to_wait)

except KeyboardInterrupt: # handle Ctrl+C cleanly
    print("\nRecording interrupted by user (Ctrl+C)")

finally:
    # release all resources and save CSV
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    with open(CSV_FILENAME, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Pulse Rate (bpm)"])
        writer.writerows(hr_records)
        print("Saved HR data to:", os.path.abspath(CSV_FILENAME))

    print(f"Done. Captured {frame_count} frames.")