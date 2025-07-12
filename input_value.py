import pygame
import time
import sys

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()

# Check if joystick is connected
if pygame.joystick.get_count() == 0:
    print("No joystick connected.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

num_buttons = joystick.get_numbuttons()
print(f"Joystick Name: {joystick.get_name()}")
print(f"Buttons: {num_buttons}, Axes: {joystick.get_numaxes()}")

# Helper to safely get button state
def safe_get_button(index):
    return joystick.get_button(index) if index < num_buttons else False

# Gear mapping using safe checks
def detect_gear():
    if safe_get_button(12): return "R"
    elif safe_get_button(13): return "1"
    elif safe_get_button(14): return "2"
    elif safe_get_button(15): return "3"
    elif safe_get_button(0):  return "4"
    elif safe_get_button(1):  return "5"
    elif safe_get_button(3):  return "6"
    return "N"

try:
    while True:
        pygame.event.pump()

        # Read axis inputs
        steering = joystick.get_axis(0)  # Range: [-1, 1]
        brake = -(joystick.get_axis(2) - 1) / 2  # Normalize to [0, 1]
        gas = -(joystick.get_axis(3) - 1) / 2
        clutch = -(joystick.get_axis(4) - 1) / 2

        # Read button states
        buttons = [str(safe_get_button(i)) for i in range(num_buttons)]

        # Detect gear
        gear = detect_gear()

        # Format output
        output = (
            f"\rSteering: {steering:.2f} | Gas: {gas:.2f} | Brake: {brake:.2f} | "
            f"Clutch: {clutch:.2f} | Gear: {gear} | Buttons: {' '.join(buttons)}"
        )

        # Print on one line
        sys.stdout.write(output)
        sys.stdout.flush()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    pygame.quit()
