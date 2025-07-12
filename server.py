import socket
import json
import time
import pigpio

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 5050       # Must match the port in the client script

# GPIO Pin Configuration
SERVO_PIN = 19
ESC_PIN = 18

# Pulse Width Ranges (in microseconds)
# These values work for most hobby servos and ESCs, but you may need to tune them.
SERVO_MIN_PULSE = 600   # Minimum pulse for servo (full left)
SERVO_MAX_PULSE = 2400  # Maximum pulse for servo (full right)

ESC_MIN_PULSE = 1000    # Minimum pulse for ESC (full reverse or brake)
ESC_MAX_PULSE = 2000    # Maximum pulse for ESC (full forward)
ESC_NEUTRAL_PULSE = 1500 # Neutral pulse for ESC

# --- Initialization ---
print("Initializing RC Car Server...")

# 1. Connect to pigpio daemon
try:
    pi = pigpio.pi()
    if not pi.connected:
        print("❌ Could not connect to pigpio daemon. Is it running?")
        print("   Start it with: sudo systemctl start pigpiod")
        exit()
except Exception as e:
    print(f"❌ Error initializing pigpio: {e}")
    exit()

print("✅ pigpio connected.")

# 2. Set pin modes
pi.set_mode(SERVO_PIN, pigpio.OUTPUT)
pi.set_mode(ESC_PIN, pigpio.OUTPUT)

# 3. Arm the ESC
# Most ESCs require a neutral signal for a few seconds to arm.
print("Arming ESC... Sending neutral signal.")
pi.set_servo_pulsewidth(ESC_PIN, ESC_NEUTRAL_PULSE)
time.sleep(2)
print("✅ ESC armed.")

# 4. Setup Server Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"✅ Server is listening on {HOST}:{PORT}")


# --- Helper Functions ---
def map_value(value, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another."""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def set_safe_state():
    """Sets motor and servo to a neutral/safe state."""
    print("\nSetting safe state (Motor Neutral, Steering Center)...")
    if pi.connected:
        pi.set_servo_pulsewidth(ESC_PIN, ESC_NEUTRAL_PULSE)
        pi.set_servo_pulsewidth(SERVO_PIN, (SERVO_MIN_PULSE + SERVO_MAX_PULSE) / 2)

# --- Main Loop ---
try:
    while True:
        # Wait for a client to connect
        client_socket, addr = server_socket.accept()
        print(f"✅ Accepted connection from: {addr}")
        
        try:
            while True:
                # Receive data from the client
                data = client_socket.recv(1024)
                if not data:
                    # Client disconnected
                    print(f"❌ Client {addr} disconnected.")
                    break

                # Decode and parse the JSON data
                try:
                    controls = json.loads(data.decode('utf-8'))

                    # Extract control values
                    steering_input = controls.get("steering", 45) # Default to center (45)
                    motor_input = controls.get("motor", 1500)   # Default to neutral (1500)
                    gear_input = controls.get("gear", "N")      # Get gear state, default to Neutral

                    # --- Control Logic ---

                    # 1. Steering
                    # Map the client's 0-90 steering value to the servo's pulse width range
                    servo_pulse = map_value(steering_input, 0, 90, SERVO_MIN_PULSE, SERVO_MAX_PULSE)
                      # 2. Motor
                    # If gear is Neutral, force motor to neutral pulse. Otherwise, use client value.
                    if gear_input == 'N':
                        esc_pulse = ESC_NEUTRAL_PULSE
                    else:
                        # The client already calculated the PWM value, so we just use it.
                        # We clamp the value to be safe.
                        esc_pulse = max(ESC_MIN_PULSE, min(ESC_MAX_PULSE, motor_input))

                    # Send the commands to the hardware
                    pi.set_servo_pulsewidth(SERVO_PIN, servo_pulse)
                    pi.set_servo_pulsewidth(ESC_PIN, esc_pulse)

                    # Optional: Print received and mapped values for debugging
                    # print(f"\rSteer In: {steering_input}, Pulse: {int(servo_pulse)} | Motor In: {motor_input}, Pulse:>
                except (json.JSONDecodeError, KeyError):
                    print(f"\n⚠️ Received invalid data from {addr}.")
                    continue

        except (BrokenPipeError, ConnectionResetError):
            print(f"❌ Client {addr} lost connection unexpectedly.")

        finally:
            # When a client disconnects, go to a safe state
            set_safe_state()
            client_socket.close()

except KeyboardInterrupt:
    print("\n🔌 Shutting down server...")

finally:
    # Final cleanup
    set_safe_state()
    if pi.connected:
        pi.stop()
    server_socket.close()
    print("✅ Server shut down cleanly.")