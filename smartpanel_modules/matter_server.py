"""
Matter Server for Smart Panel
Exposes Smart Panel as a Matter device with 6 configurable buttons
Each button can be controlled via Matter protocol (Apple Home, Google Home, etc.)
"""

import logging
import threading
import time

logger = logging.getLogger('SmartPanel.MatterServer')

# Check for Matter/CHIP library availability
try:
    # This would be python-matter-server or chip library
    # For now, we'll create a framework that can be integrated later
    HAS_MATTER_SERVER = False
    logger.warning("Matter server library not available - running in simulation mode")
except ImportError:
    HAS_MATTER_SERVER = False


class MatterButton:
    """Represents a Matter-exposed button/switch"""
    def __init__(self, button_id, pin, label):
        self.button_id = button_id
        self.pin = pin
        self.label = label
        self.state = False  # Off/On state
        self.press_count = 0
        self.last_press_time = 0
        logger.debug(f"Created Matter button: {label} (GPIO {pin})")
    
    def press(self):
        """Register a button press (toggle state)"""
        self.state = not self.state
        self.press_count += 1
        self.last_press_time = time.time()
        logger.info(f"Button {self.label} pressed: state={self.state}, count={self.press_count}")
        return self.state
    
    def get_state(self):
        """Get current button state"""
        return self.state
    
    def set_state(self, state):
        """Set button state (from Matter controller)"""
        old_state = self.state
        self.state = bool(state)
        if old_state != self.state:
            logger.info(f"Button {self.label} state changed via Matter: {old_state} -> {self.state}")
        return self.state


class MatterServer:
    """
    Matter server that exposes Smart Panel as a Matter device
    
    The Smart Panel appears as a Matter device with 6 buttons/switches
    that can be controlled from any Matter controller (Apple Home, Google Home, etc.)
    """
    
    def __init__(self, config, button_pins):
        self.config = config
        self.enabled = config.get('matter_enabled', True)
        self.vendor_id = config.get('matter_vendor_id', 0xFFF1)
        self.product_id = config.get('matter_product_id', 0x8000)
        self.discriminator = config.get('matter_discriminator', 3840)
        self.setup_pin = config.get('matter_setup_pin', 20202021)
        
        # Create Matter buttons for each physical button
        self.buttons = []
        for i, pin in enumerate(button_pins):
            button = MatterButton(
                button_id=i + 1,
                pin=pin,
                label=f"Button {i + 1}"
            )
            self.buttons.append(button)
        
        self.running = False
        self.server_thread = None
        self.paired = False
        self.pairing_mode = False
        
        logger.info(f"Matter server initialized: {len(self.buttons)} buttons")
        logger.info(f"  Vendor ID: 0x{self.vendor_id:04X}")
        logger.info(f"  Product ID: 0x{self.product_id:04X}")
        logger.info(f"  Setup PIN: {self.setup_pin}")
        logger.info(f"  Discriminator: {self.discriminator}")
        
        if self.enabled:
            self.start()
    
    def start(self):
        """Start the Matter server"""
        if not self.enabled:
            logger.warning("Matter server is disabled in configuration")
            return False
        
        if self.running:
            logger.warning("Matter server already running")
            return True
        
        logger.info("Starting Matter server...")
        self.running = True
        self.pairing_mode = not self.paired
        
        if HAS_MATTER_SERVER:
            # Start actual Matter server
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            logger.info("✓ Matter server started successfully")
        else:
            logger.info("✓ Matter server running in SIMULATION mode")
            logger.info("  Install python-matter-server for real Matter functionality")
            logger.info("  pip install python-matter-server")
        
        return True
    
    def stop(self):
        """Stop the Matter server"""
        if not self.running:
            return
        
        logger.info("Stopping Matter server...")
        self.running = False
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        logger.info("Matter server stopped")
    
    def _run_server(self):
        """Run the Matter server (in separate thread)"""
        try:
            # This is where the actual Matter server would run
            # Real implementation would use python-matter-server or CHIP SDK
            logger.info("Matter server thread started")
            
            while self.running:
                # Keep server alive
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Matter server error: {e}", exc_info=True)
            self.running = False
    
    def get_button(self, button_id):
        """Get a button by ID (1-6)"""
        if 1 <= button_id <= len(self.buttons):
            return self.buttons[button_id - 1]
        return None
    
    def get_button_by_pin(self, pin):
        """Get a button by GPIO pin"""
        for button in self.buttons:
            if button.pin == pin:
                return button
        return None
    
    def handle_button_press(self, pin):
        """
        Handle a physical button press
        Returns the new state (True/False)
        """
        button = self.get_button_by_pin(pin)
        if button:
            new_state = button.press()
            # Notify Matter network of state change
            self._notify_state_change(button)
            return new_state
        return None
    
    def _notify_state_change(self, button):
        """Notify Matter network of button state change"""
        if HAS_MATTER_SERVER and self.paired:
            # Send state update to Matter network
            logger.debug(f"→ Matter network: {button.label} = {button.state}")
        else:
            logger.debug(f"[SIM] Matter state: {button.label} = {button.state}")
    
    def get_pairing_qr_payload(self):
        """
        Generate Matter pairing QR code payload
        Format: MT:<base38-encoded-data>
        
        The QR code contains:
        - Version
        - Vendor ID
        - Product ID
        - Commissioning flow
        - Discriminator
        - Setup PIN code
        """
        # Simplified payload for demonstration
        # Real implementation would use proper Matter QR code generation
        # from chip.setup_payload import SetupPayload
        
        payload = f"MT:Y.K9042C00KA0648G00"  # Example payload
        logger.debug(f"Generated pairing QR payload: {payload}")
        return payload
    
    def get_manual_pairing_code(self):
        """
        Get manual pairing code (for entering without QR scan)
        Format: XXXX-XXXX-XXXX (11 digits with check digit)
        """
        # Simplified version - real implementation would calculate check digits
        code = f"{self.setup_pin:011d}"
        formatted = f"{code[0:4]}-{code[4:8]}-{code[8:11]}"
        return formatted
    
    def is_paired(self):
        """Check if device is paired with a Matter controller"""
        return self.paired
    
    def is_pairing_mode(self):
        """Check if device is in pairing mode"""
        return self.pairing_mode
    
    def enable_pairing_mode(self):
        """Enable pairing mode (for adding to new controller)"""
        self.pairing_mode = True
        logger.info("Pairing mode enabled - device is discoverable")
    
    def disable_pairing_mode(self):
        """Disable pairing mode"""
        self.pairing_mode = False
        logger.info("Pairing mode disabled")
    
    def get_status(self):
        """Get Matter server status"""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'paired': self.paired,
            'pairing_mode': self.pairing_mode,
            'simulation_mode': not HAS_MATTER_SERVER,
            'button_count': len(self.buttons),
            'vendor_id': f"0x{self.vendor_id:04X}",
            'product_id': f"0x{self.product_id:04X}",
            'discriminator': self.discriminator,
            'setup_pin': self.setup_pin
        }
    
    def get_all_button_states(self):
        """Get states of all buttons"""
        return [
            {
                'id': btn.button_id,
                'label': btn.label,
                'pin': btn.pin,
                'state': btn.state,
                'press_count': btn.press_count,
                'last_press': btn.last_press_time
            }
            for btn in self.buttons
        ]
    
    def get_device_info(self):
        """Get Matter device information"""
        return {
            'device_name': 'Smart Panel',
            'device_type': 'Multi-Button Controller',
            'vendor_name': 'Smart Panel Project',
            'vendor_id': f"0x{self.vendor_id:04X}",
            'product_name': 'Smart Panel 6-Button',
            'product_id': f"0x{self.product_id:04X}",
            'serial_number': f"SP-{self.discriminator:04d}",
            'firmware_version': '1.0.0'
        }

