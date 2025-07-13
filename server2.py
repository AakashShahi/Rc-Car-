import socket
import json
import time
import pigpio

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5050

SERVO_PIN = 19
ESC_PIN = 18

SERVO_MIN_PULSE = 600
SERVO_MAX_PULSE = 2400

ESC_MIN_PULSE = 1000
ESC_MAX_PULSE = 2000
ESC_NEUTRAL_PULSE = 1500

print("Initializing RC Car Server...")

try:
    pi = pigpio.pi()
    if not pi.connected:
        print("❌ Could not connect to pigpio daemon. Run: sudo systemctl start pigpiod")
        exit()
except Exception as e:
    print(f"❌ pigpio init error: {e}")
    exit()

print("✅ pigpio connected.")
pi.set_mode(SERVO_PIN, pigpio.OUTPUT)
pi.set_mode(ESC_PIN, pigpio.OUTPUT)

print("Arming ESC...")
pi.set_servo_pulsewidth(ESC_PIN, ESC_NEUTRAL_PULSE)
time.sleep(2)
print("✅ ESC armed.")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"✅ Server listening on {HOST}:{PORT}")

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def set_safe_state():
    print("\n🔒 Safe state (Neutral, Centered Steering)...")
    if pi.connected:
        pi.set_servo_pulsewidth(ESC_PIN, ESC_NEUTRAL_PULSE)
        pi.set_servo_pulsewidth(SERVO_PIN, (SERVO_MIN_PULSE + SERVO_MAX_PULSE) / 2)

try:
    while True:
        print("🔄 Waiting for client...")
        try:
            client_socket, addr = server_socket.accept()
            print(f"✅ Connected: {addr}")
            buffer = ""

            while True:
                data = client_socket.recv(1024)
                if not data:
                    print(f"❌ Client {addr} disconnected.")
                    break

                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        controls = json.loads(line)

                        steering = controls.get("steering", 45)
                        motor = controls.get("motor", 1500)
                        gear = controls.get("gear", "N")

                        servo_pwm = map_value(steering, 0, 90, SERVO_MIN_PULSE, SERVO_MAX_PULSE)
                        esc_pwm = ESC_NEUTRAL_PULSE if gear == 'N' else max(ESC_MIN_PULSE, min(ESC_MAX_PULSE, motor))

                        pi.set_servo_pulsewidth(SERVO_PIN, servo_pwm)
                        pi.set_servo_pulsewidth(ESC_PIN, esc_pwm)

                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"⚠️ Invalid JSON: {e}")
                        continue

        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"⚠️ Server error: {e}")
        finally:
            set_safe_state()
            try:
                client_socket.close()
            except:
                pass

except KeyboardInterrupt:
    print("\n🔌 Server shutting down...")

finally:
    set_safe_state()
    if pi.connected:
        pi.stop()
    server_socket.close()
    print("✅ Shutdown complete.")