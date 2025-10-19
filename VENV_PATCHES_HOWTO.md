# How to Reapply CircuitMatter Patches After Venv Rebuild

If you need to recreate your virtual environment, you'll need to reapply the CircuitMatter patches. Here's how:

## When Do You Need This?

- After running `rm -rf venv` and `./setup.sh`
- After upgrading Python version
- After moving the project to a new machine
- After CircuitMatter library updates

## Quick Patch Application

### Step 1: Locate the Files

```bash
cd /home/lazarev/smartpanel/venv/lib/python3.13/site-packages/circuitmatter
```

### Step 2: Patch `__init__.py`

Open the file:
```bash
nano __init__.py
```

Find line ~542 (look for `elif protocol_opcode == InteractionModelOpcode.STATUS_RESPONSE:`).

**Add this BEFORE that line**:
```python
            elif protocol_opcode == InteractionModelOpcode.TIMED_REQUEST:
                # Handle timed request - send status response
                print("Received TIMED_REQUEST - acknowledging")
                # Send a status response (success)
                status_response = interaction_model.StatusResponseMessage()
                status_response.Status = interaction_model.StatusCode.SUCCESS
                exchange.send(status_response)
                # Don't close the exchange - keep it open for the next invoke command
```

Save and exit (Ctrl+X, Y, Enter).

### Step 3: Patch `node_operational_credentials.py`

Open the file:
```bash
nano clusters/device_management/node_operational_credentials.py
```

Find the `NodeOperationalCredentialsCluster` class (around line 130).

**Add this after the class attributes** (before any methods):
```python
    def __init__(self):
        super().__init__()
        # Store DAC key and cert for consistent use
        self._dac_cert = None
        self._dac_key = None
        self._dac_key_obj = None
    
    def _ensure_dac(self):
        """Ensure DAC certificate and key are generated and cached"""
        if self._dac_cert is None:
            from ... import certificates
            from ...utility import random
            import ecdsa
            
            # Generate DAC once and cache it
            self._dac_cert, self._dac_key = certificates.generate_dac(
                vendor_id=0xFFF1,
                product_id=0x8000,
                product_name="SmartPanel",
                random_source=random
            )
            # Load the private key for signing
            self._dac_key_obj = ecdsa.keys.SigningKey.from_der(self._dac_key)
            print(f"Generated and cached DAC certificate ({len(self._dac_cert)} bytes)")
        return self._dac_cert, self._dac_key_obj
```

**Then add the full `invoke` method**. The complete implementation is in `circuitmatter_patches.md` (search for "Patch 2.2").

Save and exit.

## Automated Patch Script (Future Enhancement)

You could create a script to automate this:

```bash
#!/bin/bash
# apply_patches.sh

VENV_DIR="venv/lib/python3.13/site-packages/circuitmatter"

echo "Applying CircuitMatter patches..."

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: CircuitMatter not found. Run ./setup.sh first."
    exit 1
fi

# Apply patches using sed or patch command
# (This would require creating proper .patch files)

echo "Patches applied successfully!"
```

## Verification

After applying patches, test that they work:

```bash
cd /home/lazarev/smartpanel
./run.sh
```

Watch for these log messages:
- `Received TIMED_REQUEST - acknowledging`
- `Handling AttestationRequest`
- `✓ AttestationResponse sent`
- `Handling CertificateChainRequest`
- `✓ CertificateChainResponse sent`

## Alternative: Use Docker

To avoid reapplying patches, consider using Docker:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    libopenblas-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff6 \
    avahi-daemon \
    avahi-utils \
    python3-lgpio

RUN pip install -r requirements.txt

# Apply patches
COPY patches/circuitmatter_init.patch /tmp/
COPY patches/noc_cluster.patch /tmp/
RUN cd /usr/local/lib/python3.13/site-packages/circuitmatter && \
    patch -p1 < /tmp/circuitmatter_init.patch && \
    patch -p1 < /tmp/noc_cluster.patch

CMD ["python3", "dashboard_new.py"]
```

## Complete Patch Reference

For the complete, detailed patches, see:
- `circuitmatter_patches.md` - Full documentation
- `CERTIFICATE_IMPLEMENTATION.md` - Technical details

## Quick Test

After patching, run this to verify:

```bash
python3 -c "
from circuitmatter import CircuitMatter
from circuitmatter.clusters.device_management.node_operational_credentials import NodeOperationalCredentialsCluster
noc = NodeOperationalCredentialsCluster()
print('✓ Patches applied successfully!' if hasattr(noc, '_ensure_dac') else '✗ Patches missing!')
"
```

Expected output: `✓ Patches applied successfully!`

---

*Last Updated: 2025-10-20*
*CircuitMatter Version: 0.4.0+*

