import socket
import json
import pygame
import time

# Server settings
SERVER_IP = '192.168.137.142'
PORT = 5050

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((300, 100))  # Required for key input
pygame.display.set_caption("Keyboard RC Controller")

# Socket setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))
print("Connected to Raspberry Pi server")

# Control state
steering = 45  # 0 = full left, 90 = full right
gas = 1200
brake = 0
clutch = 0
gear = 'N'

def send_data():
    motor_pwm = 1350 + int(650 * gas) - int(300 * brake)
    data = {
        "steering": steering,
        "motor": motor_pwm,
        "gear": gear,
        "gas": round(gas, 2),
        "brake": round(brake, 2),
        "clutch": clutch
    }
    client_socket.sendall(json.dumps(data).encode('utf-8'))
    print(data)

try:
    while True:
        pygame.event.pump()

        keys = pygame.key.get_pressed()

        # Gas and brake
        gas = 1.0 if keys[pygame.K_UP] else 0.0
        brake = 1.0 if keys[pygame.K_DOWN] else 0.0

        # Steering
        if keys[pygame.K_LEFT]:
            steering = max(0, steering - 2)
        elif keys[pygame.K_RIGHT]:
            steering = min(90, steering + 2)

        # Gear input
        if keys[pygame.K_0]: gear = 'N'
        if keys[pygame.K_1]: gear = '1'
        if keys[pygame.K_2]: gear = '2'
        if keys[pygame.K_3]: gear = '3'
        if keys[pygame.K_4]: gear = '4'
        if keys[pygame.K_5]: gear = '5'

        # Clutch toggle (press 'c')
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                clutch = 0 if clutch == 1 else 1  # toggle clutch

        send_data()
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Client shutting down...")

finally:
    client_socket.close()
    pygame.quit()