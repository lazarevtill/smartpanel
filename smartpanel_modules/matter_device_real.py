"""
REAL Matter Device Implementation using CircuitMatter
Exposes Smart Panel as a Matter device with 6 buttons that work with:
- Samsung SmartThings
- Apple Home
- Google Home
- Amazon Alexa
"""

import logging
import threading
import time
import socket

logger = logging.getLogger('SmartPanel.MatterDevice')

try:
    import circuitmatter as cm
    from circuitmatter import data_model
    HAS_CIRCUITMATTER = True
    logger.info("✓ CircuitMatter loaded - REAL Matter device available")
except ImportError as e:
    HAS_CIRCUITMATTER = False
    logger.error(f"CircuitMatter not available: {e}")


class MatterButtonDevice:
    """
    Real Matter device with 6 buttons using CircuitMatter
    Each button appears as a switch in your smart home app
    """
    
    def __init__(self, config, button_pins):
        self.config = config
        self.enabled = config.get('matter_enabled', True) and HAS_CIRCUITMATTER
        self.vendor_id = config.get('matter_vendor_id', 0xFFF1)
        self.product_id = config.get('matter_product_id', 0x8000)
        self.discriminator = config.get('matter_discriminator', 3840)
        self.setup_pin = config.get('matter_setup_pin', 20202021)
        
        # Button states
        self.button_pins = button_pins
        self.button_states = [False] * len(button_pins)
        self.button_press_callbacks = []
        
        # Matter device
        self.matter_device = None
        self.server_thread = None
        self.running = False
        self.paired = False
        
        # QR code cache
        self._qr_cache = None
        self._manual_cache = None
        
        logger.info(f"Matter device initialized: {len(button_pins)} buttons")
        logger.info(f"  Vendor ID: 0x{self.vendor_id:04X}")
        logger.info(f"  Product ID: 0x{self.product_id:04X}")
        logger.info(f"  Discriminator: {self.discriminator}")
        logger.info(f"  Setup PIN: {self.setup_pin}")
        
        if not HAS_CIRCUITMATTER:
            logger.error("CircuitMatter not installed - Matter device disabled")
            self.enabled = False
            return
        
        if self.enabled:
            # Start Matter device in background
            threading.Thread(target=self._start_matter_device, daemon=True).start()
    
    def _start_matter_device(self):
        """Start the CircuitMatter device server"""
        try:
            time.sleep(1)  # Let main app initialize
            
            logger.info("Starting REAL Matter device server...")
            
            # Create Matter device
            self.matter_device = cm.MatterDevice()
            
            # Set device information
            self.matter_device.vendor_id = self.vendor_id
            self.matter_device.product_id = self.product_id
            self.matter_device.discriminator = self.discriminator
            self.matter_device.setup_pin_code = self.setup_pin
            
            # Add 6 button endpoints (as on/off lights for compatibility)
            for i, pin in enumerate(self.button_pins):
                endpoint = cm.OnOffLight(name=f"Button {i+1}")
                self.matter_device.add_endpoint(endpoint)
                logger.info(f"  Added endpoint: Button {i+1} (GPIO {pin})")
            
            # Start the Matter server
            self.running = True
            logger.info("✓ Matter device server started successfully!")
            logger.info("  Device is now discoverable by smart home apps")
            
            # Run the server
            self.matter_device.serve_forever()
            
        except Exception as e:
            logger.error(f"Error starting Matter device: {e}", exc_info=True)
            self.running = False
    
    def handle_button_press(self, pin):
        """Handle physical button press - update Matter state"""
        try:
            if pin in self.button_pins:
                idx = self.button_pins.index(pin)
                # Toggle state
                self.button_states[idx] = not self.button_states[idx]
                
                logger.info(f"Button {idx+1} pressed: {self.button_states[idx]}")
                
                # Update Matter endpoint if device is running
                if self.running and self.matter_device:
                    try:
                        endpoint = self.matter_device.endpoints[idx + 1]  # +1 because endpoint 0 is root
                        endpoint.on = self.button_states[idx]
                        logger.debug(f"Updated Matter endpoint {idx+1}")
                    except Exception as e:
                        logger.error(f"Error updating Matter endpoint: {e}")
                
                return self.button_states[idx]
        except Exception as e:
            logger.error(f"Error handling button press: {e}")
        return None
    
    def get_pairing_qr_payload(self):
        """Get Matter QR code payload"""
        if self._qr_cache:
            return self._qr_cache
        
        # Generate real Matter QR code
        # Format: MT:<base38-encoded-data>
        version = 0
        vendor_id = self.vendor_id
        product_id = self.product_id
        custom_flow = 0
        discovery_caps = 0x05  # BLE + SoftAP
        discriminator = self.discriminator
        passcode = self.setup_pin
        
        # Pack into bit field
        payload_int = 0
        payload_int |= (version & 0x7)
        payload_int |= (vendor_id & 0xFFFF) << 3
        payload_int |= (product_id & 0xFFFF) << 19
        payload_int |= (custom_flow & 0x3) << 35
        payload_int |= (discovery_caps & 0xFF) << 37
        payload_int |= (discriminator & 0xFFF) << 45
        payload_int |= (passcode & 0x7FFFFFF) << 57
        
        # Convert to Base-38
        base38_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-."
        base38_str = ""
        
        while payload_int > 0:
            base38_str = base38_chars[payload_int % 38] + base38_str
            payload_int //= 38
        
        while len(base38_str) < 22:
            base38_str = "0" + base38_str
        
        qr_payload = f"MT:{base38_str}"
        self._qr_cache = qr_payload
        
        logger.info(f"Generated Matter QR code: {qr_payload}")
        return qr_payload
    
    def get_manual_pairing_code(self):
        """Get manual pairing code"""
        if self._manual_cache:
            return self._manual_cache
        
        disc_str = f"{self.discriminator:04d}"
        pass_str = f"{self.setup_pin:08d}"
        code_without_check = disc_str + pass_str
        
        # Verhoeff check digit
        check_digit = self._calculate_verhoeff(code_without_check)
        full_code = code_without_check + str(check_digit)
        formatted = f"{full_code[0:4]}-{full_code[4:8]}-{full_code[8:13]}"
        
        self._manual_cache = formatted
        return formatted
    
    def _calculate_verhoeff(self, num_str):
        """Calculate Verhoeff check digit"""
        d = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        p = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        c = 0
        for i, digit in enumerate(reversed(num_str)):
            c = d[c][p[(i + 1) % 8][int(digit)]]
        return inv[c]
    
    def get_status(self):
        """Get device status"""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'paired': self.paired,
            'pairing_mode': not self.paired,
            'has_sdk': HAS_CIRCUITMATTER,
            'simulation_mode': not HAS_CIRCUITMATTER,
            'button_count': len(self.button_pins),
            'vendor_id': f"0x{self.vendor_id:04X}",
            'product_id': f"0x{self.product_id:04X}",
            'discriminator': self.discriminator,
            'setup_pin': self.setup_pin
        }
    
    def get_all_button_states(self):
        """Get all button states"""
        return [
            {
                'id': i + 1,
                'label': f"Button {i + 1}",
                'pin': pin,
                'state': self.button_states[i],
                'press_count': 0,
                'last_press': 0
            }
            for i, pin in enumerate(self.button_pins)
        ]
    
    def stop(self):
        """Stop the Matter device"""
        if self.running:
            logger.info("Stopping Matter device...")
            self.running = False
            if self.matter_device:
                try:
                    self.matter_device.stop()
                except:
                    pass
            logger.info("Matter device stopped")


# Alias for compatibility
MatterServer = MatterButtonDevice

