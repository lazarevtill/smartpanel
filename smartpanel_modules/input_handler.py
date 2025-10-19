"""
Input Handler for Smart Panel
Enhanced input handling with long press, short press, and debouncing
"""

import time
from gpiozero import RotaryEncoder, Button as GPIOButton


class InputHandler:
    """Enhanced input handler with gesture detection"""
    
    def __init__(self, enc_a, enc_b, enc_push, button_pins):
        # Initialize encoder
        self.encoder = RotaryEncoder(enc_a, enc_b, max_steps=0, wrap=False, bounce_time=0.002)
        self.enc_button = GPIOButton(enc_push)
        
        # Initialize buttons
        self.buttons = [GPIOButton(p) for p in button_pins]
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

