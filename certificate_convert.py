from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption
)
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from pathlib import Path

# 🔧 Input
pfx_path = ""
pfx_password = ""

# 📤 Output file names
client_cert_file = "client-cert.pem"
client_key_file = "client-key.pem"
ca_cert_file = "ca-cert.pem"

# 📦 Load PFX contents
pfx_data = Path(pfx_path).read_bytes()
private_key, client_cert, additional_certs = load_key_and_certificates(
    pfx_data, pfx_password.encode(), None
)

# 📝 Write client certificate
with open(client_cert_file, "wb") as f:
    f.write(client_cert.public_bytes(Encoding.PEM))

# 🔐 Write private key
with open(client_key_file, "wb") as f:
    f.write(private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ))

# 🛡️ Write CA certificates (if any)
if additional_certs:
    with open(ca_cert_file, "wb") as f:
        for cert in additional_certs:
            f.write(cert.public_bytes(Encoding.PEM))
