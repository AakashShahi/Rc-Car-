import pygame
import time

pygame.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"✅ Connected to: {joystick.get_name()}")
print(f"Detected {joystick.get_numbuttons()} buttons.")
print("\nPress any button on your wheel or shifter to see its number. Press Ctrl+C to exit.")

last_pressed = -1
try:
    while True:
        pygame.event.pump()
        for i in range(joystick.get_numbuttons()):
            if joystick.get_button(i):
                if i != last_pressed:
                    print(f"Button {i} PRESSED")
                    last_pressed = i
            elif i == last_pressed and not joystick.get_button(i):
                 last_pressed = -1 # Reset when button is released
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nDone.")
finally:
    pygame.quit()