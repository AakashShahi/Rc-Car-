import socket
import json
import pygame
import time

# --- Server Configuration ---
SERVER_IP = '192.168.137.142'  # Raspberry Pi IP
PORT = 5050

# --- Controller Configuration ---
BUTTON_GEAR_UP = 10
BUTTON_GEAR_DOWN = 9
AXIS_STEERING = 0
AXIS_GAS = 1
AXIS_BRAKE = 2

GEAR_SEQUENCE = ['R', 'N', '1', '2', '3', '4', '5']
GEAR_SPEED_MULTIPLIER = {
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5
}

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No joystick connected.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"✅ Joystick '{joystick.get_name()}' initialized.")

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, PORT))
    print(f"✅ Connected to RC Car server at {SERVER_IP}:{PORT}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    pygame.quit()
    exit()

current_gear_index = 1
gear_up_pressed_last = False
gear_down_pressed_last = False

try:
    while True:
        pygame.event.pump()

        steer_axis = joystick.get_axis(AXIS_STEERING)
        gas_raw = joystick.get_axis(AXIS_GAS)
        brake_raw = joystick.get_axis(AXIS_BRAKE)

        gas = max(0, min(1, -(gas_raw - 1) / 2))
        brake = max(0, min(1, -(brake_raw - 1) / 2))

        if gas < 0.05: gas = 0
        if brake < 0.05: brake = 0

        # Gear shifting
        gear_up = joystick.get_button(BUTTON_GEAR_UP)
        gear_down = joystick.get_button(BUTTON_GEAR_DOWN)

        if gear_up and not gear_up_pressed_last and current_gear_index < len(GEAR_SEQUENCE) - 1:
            current_gear_index += 1
        if gear_down and not gear_down_pressed_last and current_gear_index > 0:
            current_gear_index -= 1

        gear_up_pressed_last = gear_up
        gear_down_pressed_last = gear_down

        gear = GEAR_SEQUENCE[current_gear_index]

        # Steering: [-1, 1] → [0, 90]
        steering = int((steer_axis + 1) * 45)

        # Motor PWM
        if gear == 'R':
            if gas > 0.05:
                motor = 1500 - int(50 * gas)
            else:
                 motor = 1500 
        elif gear == 'N':
            motor = 1500
        else:
            factor = GEAR_SPEED_MULTIPLIER[gear]
            forward = 1500 + int(50 * factor * gas)
            backward = int(50 * brake)
            motor = forward - backward
            motor = max(1500, min(2000, motor))

        # Send data
        controls = {
            "steering": steering,
            "motor": motor,
            "gear": gear,
            "gas": round(gas, 2),
            "brake": round(brake, 2)
        }

        try:
            client_socket.sendall((json.dumps(controls) + '\n').encode('utf-8'))
        except BrokenPipeError:
            print("❌ Server disconnected.")
            break

        print(f"\rSending: {controls}", end="")
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n🛑 Shutting down client...")

finally:
    client_socket.close()
    pygame.quit()
    print("✅ Closed cleanly.")
