import serial
import time
import os
import django
import sys
from datetime import datetime

# Setup Django
sys.path.append("C:/Users/Siddarth Shankar/Desktop/Web_Application")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "controlhub.settings")
django.setup()

from dashboard.models import TemperatureLog, Session

# Expect session ID to be passed as a command-line argument
if len(sys.argv) < 2:
    print("Missing session ID.")
    sys.exit(1)

session_id = sys.argv[1]

try:
    session = Session.objects.get(id=session_id)
except Session.DoesNotExist:
    print(f"No session with ID {session_id}")
    sys.exit(1)

print(f"Logging temperatures for session: {session.name} (ID: {session.id})")

# Serial config (adjust COM port)
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)

try:
    while True:
        line = ser.readline().decode().strip()
        if "Celcius" in line:
            try:
                temp = float(line.replace(" Celcius", ""))
                TemperatureLog.objects.create(session=session, temperature=temp)
                print(f"[{datetime.now()}] {temp} °C")
            except ValueError:
                print("Bad reading:", line)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopped logging.")
    ser.close()
