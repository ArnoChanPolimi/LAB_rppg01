import time
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cms50d import CMS50D

# add some other import
import os
import csv
import serial

try:
    ser = serial.Serial("COM9", baudrate=9600, timeout=1)
    print("Serial port opened successfully")
    ser.close()
except Exception as e:
    print(f"Failed to open serial port: {e}")


import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
print("Available ports:")
for p in ports:
    print(p)


# create a file
os.makedirs("data", exist_ok=True)
csv_filename = "data/hr_data.csv"
hr_records = [] 

monitor = CMS50D(port="COM9")  # Replace with your actual COM port
monitor.connect()
monitor.start_live_acquisition()

# Matplotlib live plot
plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
xdata, ydata = [], []
# line, = ax.plot_date([], [], fmt='-m', label='Pulse Waveform')
line, = ax.plot([], [], '-m', label='Pulse Waveform')

text_hr = ax.text(0.02, 0.95, '', transform=ax.transAxes, color='red', fontsize=12)
text_spo2 = ax.text(0.02, 0.90, '', transform=ax.transAxes, color='blue', fontsize=12)

ax.set_ylim(0, 128)
ax.set_ylabel("Waveform")
ax.set_xlabel("Time")
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
plt.title("CMS50D Live Data")

try:
    while True:
        data = monitor.get_latest_data()
        if not data:
            continue

        now = data['timestamp']
        pulse_rate = data['pulse_rate']
        hr_records.append([now.strftime("%Y-%m-%d %H:%M:%S.%f"), pulse_rate])
        waveform = data['waveform']
        xdata.append(now)
        ydata.append(waveform)

        cutoff = now - datetime.timedelta(seconds=60)
        hr_records = [[t, hr] for [t, hr] in hr_records if datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f") >= cutoff]

        xdata = [t for t in xdata if t >= cutoff]
        ydata = ydata[-len(xdata):]

        line.set_data(xdata, ydata)
        ax.set_xlim(cutoff, now)
        text_hr.set_text(f"HR: {pulse_rate} bpm")
        text_spo2.set_text(f"SpO2: {data['spO2']}%")

        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    monitor.stop_live_acquisition()
    monitor.disconnect()
    plt.ioff()
    plt.close('all')

    with open(csv_filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Pulse Rate (bpm)"])
        writer.writerows(hr_records)

    print("Saved HR data to:", os.path.abspath(csv_filename))
