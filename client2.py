import socket
import json
import pygame
import time

SERVER_IP = '192.168.16.101'  # Your Pi's IP
PORT = 5050

BUTTON_GEAR_UP = 10
BUTTON_GEAR_DOWN = 9
AXIS_STEERING = 0
AXIS_GAS = 1
AXIS_BRAKE = 2
GEAR_SEQUENCE = ['R', 'N', '1', '2', '3', '4', '5']
GEAR_SPEED_MULTIPLIER = {
    '1': 1.2,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5
}

GAS_DEADZONE = 0.05
BRAKE_DEADZONE = 0.05
GAS_THRESHOLD_RUN = 0.6
PWM_NEUTRAL = 1500

def get_gear_range(gear: str) -> tuple[int, int]:
    factor = GEAR_SPEED_MULTIPLIER.get(gear, 1)
    gear_min = 1575 + (factor - 1) * 25
    return gear_min, gear_min + 25

def connect_to_server():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((SERVER_IP, PORT))
            print(f"✅ Connected to RC Car server at {SERVER_IP}:{PORT}")
            return s
        except Exception as e:
            print(f"🔁 Reconnecting in 2s: {e}")
            time.sleep(2)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No joystick found.")
    pygame.quit()
    raise SystemExit

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"✅ Joystick '{joystick.get_name()}' initialized.")

client_socket = connect_to_server()
current_gear_index = 1
gear_up_last_state = False
gear_down_last_state = False

try:
    while True:
        pygame.event.pump()

        steer_axis = joystick.get_axis(AXIS_STEERING)
        gas_raw = joystick.get_axis(AXIS_GAS)
        brake_raw = joystick.get_axis(AXIS_BRAKE)

        gas = max(0, min(1, -(gas_raw - 1) / 2))
        brake = max(0, min(1, -(brake_raw - 1) / 2))

        if gas < GAS_DEADZONE: gas = 0
        if brake < BRAKE_DEADZONE: brake = 0

        gear_up = joystick.get_button(BUTTON_GEAR_UP)
        gear_down = joystick.get_button(BUTTON_GEAR_DOWN)

        if gear_up and not gear_up_last_state and current_gear_index < len(GEAR_SEQUENCE) - 1:
            current_gear_index += 1
        if gear_down and not gear_down_last_state and current_gear_index > 0:
            current_gear_index -= 1

        gear_up_last_state = gear_up
        gear_down_last_state = gear_down

        gear = GEAR_SEQUENCE[current_gear_index]
        steering = int((-steer_axis + 1) * 45)
        motor = PWM_NEUTRAL

        if gear == 'R':
            if gas > GAS_DEADZONE:
                motor = PWM_NEUTRAL - int(40 * gas)
        elif gear == 'N':
            motor = PWM_NEUTRAL
        elif gear in GEAR_SPEED_MULTIPLIER:
            if gas > GAS_THRESHOLD_RUN:
                gear_min, gear_max = get_gear_range(gear)
                scaled = min(1, max(0, (gas - 0.5) * 2))
                forward = int(gear_min + (gear_max - gear_min) * scaled)
                motor = forward
            else:
                motor = PWM_NEUTRAL

            motor -= int(50 * brake)
            motor = max(PWM_NEUTRAL, min(2000, motor))

        controls = {
            "steering": steering,
            "motor": motor,
            "gear": gear,
            "gas": round(gas, 2),
            "brake": round(brake, 2)
        }

        try:
            client_socket.sendall((json.dumps(controls) + '\n').encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            print("\n❌ Server lost. Reconnecting...")
            client_socket.close()
            client_socket = connect_to_server()
            continue

        print(f"\rSending: {controls}", end="")
        time.sleep(0.01)  # 100 Hz update rate

except KeyboardInterrupt:
    print("\n🛑 Client stopped.")

finally:
    client_socket.close()
    pygame.quit()
    print("✅ Closed cleanly.")
