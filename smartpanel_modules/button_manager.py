"""
Button Manager for Smart Panel
Handles configurable button assignments and Matter device control
"""

import logging
from .config import BUTTON_PINS, BUTTON_LABELS, BUTTON_FUNCTIONS, load_config, save_config

logger = logging.getLogger('SmartPanel.ButtonManager')


class ButtonManager:
    """Manages button assignments and actions"""
    
    def __init__(self, config=None):
        self.config = config or load_config()
        self.button_assignments = self.config.get('button_assignments', {})
        self.button_matter_devices = self.config.get('button_matter_devices', {})
        logger.info(f"Button manager initialized with {len(BUTTON_PINS)} buttons")
        self._log_assignments()
    
    def _log_assignments(self):
        """Log current button assignments"""
        for pin in BUTTON_PINS:
            function = self.button_assignments.get(str(pin), 'none')
            device = self.button_matter_devices.get(str(pin))
            if device:
                logger.info(f"  {BUTTON_LABELS[pin]}: {function} -> Matter Device {device}")
            else:
                logger.info(f"  {BUTTON_LABELS[pin]}: {function}")
    
    def get_button_function(self, pin):
        """Get the assigned function for a button"""
        return self.button_assignments.get(str(pin), 'none')
    
    def get_button_matter_device(self, pin):
        """Get the Matter device assigned to a button"""
        return self.button_matter_devices.get(str(pin))
    
    def set_button_function(self, pin, function):
        """Assign a function to a button"""
        if function not in BUTTON_FUNCTIONS:
            logger.error(f"Invalid function: {function}")
            return False
        
        self.button_assignments[str(pin)] = function
        self.config['button_assignments'] = self.button_assignments
        save_config(self.config)
        logger.info(f"Button {BUTTON_LABELS[pin]} assigned to: {function}")
        return True
    
    def set_button_matter_device(self, pin, device_id):
        """Assign a Matter device to a button"""
        self.button_matter_devices[str(pin)] = device_id
        self.config['button_matter_devices'] = self.button_matter_devices
        save_config(self.config)
        
        if device_id:
            logger.info(f"Button {BUTTON_LABELS[pin]} assigned to Matter device: {device_id}")
        else:
            logger.info(f"Button {BUTTON_LABELS[pin]} Matter device cleared")
        return True
    
    def handle_button_press(self, pin, context):
        """
        Handle a button press based on its assignment
        
        Args:
            pin: GPIO pin number
            context: Dictionary with 'panel', 'matter_server', etc.
        
        Returns:
            Action result or None
        """
        function = self.get_button_function(pin)
        logger.debug(f"Button {BUTTON_LABELS.get(pin, pin)} pressed: {function}")
        
        # Notify Matter server of button press
        matter_server = context.get('matter_server')
        if matter_server:
            new_state = matter_server.handle_button_press(pin)
            logger.debug(f"Matter button state: {new_state}")
        
        # Handle system functions
        if function == 'back':
            return 'back'
        elif function == 'select':
            return 'select'
        elif function == 'menu':
            return 'menu'
        elif function == 'matter_qr':
            return 'matter_qr'
        elif function == 'offset_cycle':
            return 'offset_cycle'
        elif function == 'none':
            # Button press updates Matter state only
            return 'matter_button_pressed'
        
        return None
    
    def get_available_functions(self):
        """Get list of available button functions"""
        return list(BUTTON_FUNCTIONS.keys())
    
    def get_function_name(self, function_key):
        """Get human-readable name for a function"""
        return BUTTON_FUNCTIONS.get(function_key, 'Unknown')
    
    def get_button_label(self, pin):
        """Get label for a button"""
        return BUTTON_LABELS.get(pin, f"GPIO{pin}")
    
    def get_all_assignments(self):
        """Get all button assignments for display"""
        assignments = []
        for pin in BUTTON_PINS:
            function = self.get_button_function(pin)
            device = self.get_button_matter_device(pin)
            assignments.append({
                'pin': pin,
                'label': self.get_button_label(pin),
                'function': function,
                'function_name': self.get_function_name(function),
                'matter_device': device
            })
        return assignments

