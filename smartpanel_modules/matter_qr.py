"""
Matter QR Code Generation and Display
Generates QR codes for Matter device commissioning
"""

try:
    import qrcode
    from PIL import Image
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    print("Warning: qrcode library not installed. QR code generation disabled.")
    print("Install with: pip3 install qrcode[pil]")


def generate_matter_qr_code(setup_payload):
    """
    Generate a Matter QR code from setup payload
    
    Args:
        setup_payload: Matter setup payload string (e.g., "MT:Y.K9042C00KA0648G00")
    
    Returns:
        PIL Image object or None if qrcode not available
    """
    if not HAS_QRCODE:
        return None
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=2,
        )
        qr.add_data(setup_payload)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None


def get_default_matter_payload():
    """
    Get default Matter setup payload for this Raspberry Pi
    
    In production, this should be generated based on:
    - Vendor ID
    - Product ID
    - Discriminator
    - Setup PIN Code
    """
    # Example payload - replace with actual generated payload
    # Format: MT:Y.K9042C00KA0648G00
    return "MT:Y.K9042C00KA0648G00"


def generate_matter_manual_code(discriminator, setup_pin):
    """
    Generate Matter manual pairing code
    
    Args:
        discriminator: 12-bit discriminator value
        setup_pin: Setup PIN code (8 digits)
    
    Returns:
        Manual pairing code string
    """
    # Simplified manual code generation
    # Real implementation should follow Matter specification
    return f"{discriminator:04d}-{setup_pin:08d}"


def render_qr_to_display(qr_image, target_size=(100, 100)):
    """
    Resize QR code image to fit display
    
    Args:
        qr_image: PIL Image of QR code
        target_size: Tuple of (width, height) for target size
    
    Returns:
        Resized PIL Image
    """
    if qr_image is None:
        return None
    
    try:
        return qr_image.resize(target_size, Image.Resampling.NEAREST)
    except:
        # Fallback for older PIL versions
        return qr_image.resize(target_size, Image.NEAREST)

