import pygame
import time

# --- Controller Configuration ---

# Buttons for Sequential Shifting
BUTTON_GEAR_UP = 10
BUTTON_GEAR_DOWN = 9

# Axis Configuration (for combined pedals)
AXIS_STEERING = 0
AXIS_GAS_AND_BRAKE = 1 # This axis handles both gas and brake
   # Clutch is usually separate
# --- Main Program ---

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No joystick connected. Please connect your G29.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"✅ Connected to: {joystick.get_name()}")
print(f"Detected {joystick.get_numaxes()} axes and {joystick.get_numbuttons()} buttons.")
print("-" * 50)
print("Controls:")
print(f"  - Steer:         Wheel")
print(f"  - Gas/Brake:     Pedals")
print(f"  - Shift Up:      Button {BUTTON_GEAR_UP}")
print(f"  - Shift Down:    Button {BUTTON_GEAR_DOWN}")
print("-" * 50)


# --- Gearbox State ---
# We define the order of gears in a list.
# The index of the list will represent our current gear.
GEAR_SEQUENCE = ['R', 'N', '1', '2', '3', '4', '5']
current_gear_index = 1 # Start in Neutral ('N')

# State variables to detect a single button press (edge detection)
# This prevents one long press from shifting through all gears instantly.
gear_up_pressed_last_frame = False
gear_down_pressed_last_frame = False


try:
    while True:
        # This is the heart of a pygame program, it processes all events.
        pygame.event.pump()

        # --- Read Axis Values ---
        steer = round(joystick.get_axis(AXIS_STEERING), 2)
        
        # Handle Combined Pedals
        gas_brake_axis_val = joystick.get_axis(AXIS_GAS_AND_BRAKE)
        
        # Axis value < 0 is Accelerator, > 0 is Brake
        if gas_brake_axis_val < 0:
            accelerator = round(gas_brake_axis_val * -100)
            brake = 0
        else:
            accelerator = 0
            brake = round(gas_brake_axis_val * 100)

        # --- Sequential Shifter Logic ---
        
        # Check the current state of the shift buttons
        is_gear_up_pressed = joystick.get_button(BUTTON_GEAR_UP)
        is_gear_down_pressed = joystick.get_button(BUTTON_GEAR_DOWN)

        # Shift Up
        # We only shift if the button is pressed NOW and was NOT pressed in the last frame.
        if is_gear_up_pressed and not gear_up_pressed_last_frame:
            # Move to the next gear, but don't go past the highest gear ('5')
            if current_gear_index < len(GEAR_SEQUENCE) - 1:
                current_gear_index += 1
        
        # Shift Down
        # We use the same logic for downshifting.
        if is_gear_down_pressed and not gear_down_pressed_last_frame:
            # Move to the previous gear, but don't go below the lowest gear ('R')
            if current_gear_index > 0:
                current_gear_index -= 1

        # Update the 'last frame' variables for the next loop
        gear_up_pressed_last_frame = is_gear_up_pressed
        gear_down_pressed_last_frame = is_gear_down_pressed
        
        # Get the current gear's name (e.g., 'N', '1', 'R') from the list
        current_gear_name = GEAR_SEQUENCE[current_gear_index]

        # --- Apply Gas based on Gear Logic ---
        # If we are in Neutral, the gas pedal does nothing.
        if current_gear_name == 'N':
            final_accelerator = 0
        else:
            final_accelerator = accelerator

        # --- Display Formatted Output ---
        # The '\r' at the start moves the cursor to the beginning of the line
        # so we can overwrite it for a live-updating display.
        status_line = (
            f"Steer: {steer:<5} | "
            f"Gas: {final_accelerator:>3}% | "
            f"Brake: {brake:>3}% | "
            f"Gear: {current_gear_name}"
        )

        print(f"\r{status_line}    ", end="", flush=True)

        # A short delay to prevent the script from using 100% CPU
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n\n👋 Exiting program.")

finally:
    pygame.quit()