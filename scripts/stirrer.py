import serial
import time
import sys
import os
import django

# Django setup
sys.path.append("C:/Users/Siddarth Shankar/Desktop/Web_Application")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "controlhub.settings")
django.setup()

from dashboard.models import Session, ScriptLog

# --- Get session ID ---
if len(sys.argv) < 2:
    print("Missing session ID.")
    sys.exit(1)

session_id = sys.argv[1]

try:
    session = Session.objects.get(id=session_id)
except Session.DoesNotExist:
    print(f"No session with ID {session_id}")
    sys.exit(1)

ser = None
output = ""
error = ""

try:
    # --- Connect to Serial ---
    ser = serial.Serial('COM10', 115200, timeout=1)
    time.sleep(0.1)  # Allow brief buffer time

    # --- Handshake Wait ---
    handshake_received = False
    start_time = time.time()
    while time.time() - start_time < 5:
        line = ser.readline().decode(errors="ignore").strip()
        print("Received:", line)
        if "READY" in line:
            handshake_received = True
            break

    if not handshake_received:
        error = "❌ Handshake from ESP32 not received."
        raise Exception(error)

    print("🟢 Handshake complete. Starting motor control...")

    last_sent_rpm = None

    # --- Main loop ---
    while True:
        session.refresh_from_db()
        current_rpm = session.rpm

        # Optional: stop motor if session is marked ended
        if hasattr(session, "status") and session.status == "ended":
            print("🛑 Session ended by user.")
            break

        # Only send RPM if it's changed
        if current_rpm != last_sent_rpm:
            print(f"🔁 Sending new RPM: {current_rpm}")
            ser.write(f"{current_rpm}\n".encode())
            last_sent_rpm = current_rpm

            output = f"✅ Sent RPM: {current_rpm}"
            error = ""
            ScriptLog.objects.create(
                script_name="stirrer",
                output=output,
                error=error,
                session=session
            )

        time.sleep(1)

except KeyboardInterrupt:
    print("\n⛔ Interrupted by user.")
    output = "Interrupted by user"
    error = ""
except Exception as e:
    error = str(e)
    print("❌ Error:", error)
finally:
    if ser and ser.is_open:
        ser.close()
        print("🔌 Serial port closed.")

    # Log if any error occurred
    if output or error:
        ScriptLog.objects.create(
            script_name="stirrer",
            output=output,
            error=error,
            session=session
        )
