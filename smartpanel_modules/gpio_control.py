"""
GPIO Control for Smart Panel
Pin management and state control
"""

import RPi.GPIO as GPIO
from .config import PIN_DC, PIN_RST, PIN_BL, ENC_A, ENC_B, ENC_PUSH, BUTTON_PINS

# GPIO state tracking
gpio_states = {}


def init_gpio_control():
    """Initialize GPIO pins for control"""
    controllable_pins = [2, 3, 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 26, 27]
    for pin in controllable_pins:
        if pin not in [PIN_DC, PIN_RST, PIN_BL, ENC_A, ENC_B, ENC_PUSH] + BUTTON_PINS:
            try:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                gpio_states[pin] = False
            except Exception as e:
                print(f"Warning: Could not initialize GPIO{pin}: {e}")


def toggle_gpio_pin(pin):
    """Toggle GPIO pin state"""
    if pin in gpio_states:
        new_state = not gpio_states[pin]
        try:
            GPIO.output(pin, GPIO.HIGH if new_state else GPIO.LOW)
            gpio_states[pin] = new_state
            return new_state
        except Exception as e:
            print(f"Error toggling GPIO{pin}: {e}")
            return gpio_states[pin]
    return False


def get_gpio_state(pin):
    """Get current GPIO pin state"""
    return gpio_states.get(pin, False)


def set_gpio_pin(pin, state):
    """Set GPIO pin to specific state"""
    if pin in gpio_states:
        try:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            gpio_states[pin] = state
            return True
        except Exception as e:
            print(f"Error setting GPIO{pin}: {e}")
            return False
    return False


def get_all_gpio_states():
    """Get all GPIO pin states"""
    return gpio_states.copy()

