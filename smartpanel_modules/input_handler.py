"""
Input Handler for Smart Panel
Enhanced input handling with long press, short press, emergency reset, and debouncing
"""

import time
import logging
from gpiozero import RotaryEncoder, Button as GPIOButton
from gpiozero.pins.lgpio import LGPIOFactory
from .config import EMERGENCY_RESET_BUTTONS, EMERGENCY_RESET_DURATION

logger = logging.getLogger('SmartPanel.Input')

# Use lgpio factory with pull-up resistors
factory = LGPIOFactory()


class InputHandler:
    """Enhanced input handler with gesture detection and emergency reset"""
    
    def __init__(self, enc_a, enc_b, enc_push, button_pins):
        logger.info("Initializing input handler")
        
        # Initialize encoder
        self.encoder = RotaryEncoder(enc_a, enc_b, max_steps=0, wrap=False, bounce_time=0.002, pin_factory=factory)
        
        # Encoder button with pull-up (active low - pressed = GND)
        # KY-040 rotary encoder SW pin connects to GND when pressed
        # pull_up=True means internal pull-up resistor, button connects to GND when pressed
        self.enc_button = GPIOButton(enc_push, pull_up=True, bounce_time=0.05, pin_factory=factory)
        
        # Initialize buttons with pull-down resistors (active high - pressed = HIGH/3.3V)
        # pull_up=False: button.is_pressed = True when button pressed (connected to 3.3V)
        # This is the correct configuration for buttons wired to 3.3V
        self.buttons = [GPIOButton(p, pull_up=False, bounce_time=0.05, pin_factory=factory) for p in button_pins]
        self.button_pins = button_pins
        self.button_states = {p: False for p in button_pins}
        
        # Setup button callbacks
        for b in self.buttons:
            b.when_pressed = lambda button=b: self._button_pressed(button.pin.number)
        
        # Encoder button press tracking
        self.enc_press_start = None
        self.enc_last_state = False
        
        # Long press threshold (seconds)
        self.long_press_threshold = 0.5
        
        # Gesture detection
        self.last_enc_time = time.time()
        self.enc_velocity = 0
        
        # Emergency reset tracking
        self.emergency_reset_start = None
        self.emergency_reset_buttons = set(EMERGENCY_RESET_BUTTONS)
        self.emergency_reset_duration = EMERGENCY_RESET_DURATION
        
        logger.info(f"Input handler initialized with {len(button_pins)} buttons")
        logger.info(f"Emergency reset: Hold B1+B6 for {EMERGENCY_RESET_DURATION}s")
        
        # Debug: Check initial button states
        time.sleep(0.1)  # Small delay for buttons to stabilize
        logger.debug(f"Encoder button GPIO{self.enc_button.pin.number}: is_pressed={self.enc_button.is_pressed}")
        for b in self.buttons:
            logger.debug(f"Button GPIO{b.pin.number}: is_pressed={b.is_pressed}")
    
    def _button_pressed(self, pin):
        """Handle button press event"""
        self.button_states[pin] = True
    
    def get_encoder_delta(self):
        """Get encoder rotation delta"""
        delta = self.encoder.steps
        self.encoder.steps = 0
        
        # Track velocity for gesture detection
        if delta != 0:
            current_time = time.time()
            time_delta = current_time - self.last_enc_time
            if time_delta > 0:
                self.enc_velocity = abs(delta) / time_delta
            self.last_enc_time = current_time
        
        return delta
    
    def get_encoder_button_state(self):
        """
        Get encoder button state with long/short press detection
        Returns: ('none', 'short_press', 'long_press', 'pressed')
        """
        is_pressed = self.enc_button.is_pressed
        current_time = time.time()
        
        # Button just pressed
        if is_pressed and not self.enc_last_state:
            self.enc_press_start = current_time
            self.enc_last_state = True
            return 'pressed'
        
        # Button released
        elif not is_pressed and self.enc_last_state:
            self.enc_last_state = False
            if self.enc_press_start:
                press_duration = current_time - self.enc_press_start
                self.enc_press_start = None
                
                if press_duration >= self.long_press_threshold:
                    return 'long_press'
                else:
                    return 'short_press'
        
        # Button held down
        elif is_pressed and self.enc_last_state:
            if self.enc_press_start:
                press_duration = current_time - self.enc_press_start
                if press_duration >= self.long_press_threshold:
                    # Return long_press once, then reset
                    self.enc_press_start = None
                    return 'long_press'
        
        return 'none'
    
    def check_emergency_reset(self):
        """
        Check if emergency reset combination is held
        Returns: (is_active, progress_percent)
        """
        # Check if all emergency reset buttons are currently pressed
        all_pressed = all(
            any(b.pin.number == pin and b.is_pressed for b in self.buttons)
            for pin in self.emergency_reset_buttons
        )
        
        current_time = time.time()
        
        if all_pressed:
            if self.emergency_reset_start is None:
                self.emergency_reset_start = current_time
                logger.warning("Emergency reset sequence started!")
            
            elapsed = current_time - self.emergency_reset_start
            progress = min(100, int((elapsed / self.emergency_reset_duration) * 100))
            
            if elapsed >= self.emergency_reset_duration:
                logger.critical("EMERGENCY RESET TRIGGERED!")
                return ('triggered', 100)
            
            return ('active', progress)
        else:
            if self.emergency_reset_start is not None:
                logger.info("Emergency reset sequence cancelled")
            self.emergency_reset_start = None
            return ('none', 0)
    
    def get_button_states(self):
        """Get and clear button states"""
        states = self.button_states.copy()
        for p in self.button_pins:
            self.button_states[p] = False
        return states
    
    def is_fast_scroll(self):
        """Check if user is scrolling fast"""
        return self.enc_velocity > 5.0
    
    def reset(self):
        """Reset input state"""
        self.encoder.steps = 0
        for p in self.button_pins:
            self.button_states[p] = False
        self.enc_press_start = None
        self.enc_last_state = False

