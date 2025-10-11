"""
pyproxy.utils.crypto.py

Certificate generation utilities for SSL inspection in pyproxy.
"""

import os
from OpenSSL import crypto


def generate_certificate(domain, certs_folder, ca_cert, ca_key):
    """
    Generates a self-signed SSL certificate for the given domain.

    Args:
        domain (str): The domain name for which the certificate is generated.

    Returns:
        tuple: Paths to the generated certificate and private key files.
    """
    cert_path = f"{certs_folder}{domain}.pem"
    key_path = f"{certs_folder}{domain}.key"

    if not os.path.exists(cert_path):
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        with open(ca_cert, "r", encoding="utf-8") as f:
            ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        with open(ca_key, "r", encoding="utf-8") as f:
            ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())

        cert = crypto.X509()
        cert.set_serial_number(int.from_bytes(os.urandom(16), "big"))
        cert.get_subject().CN = domain
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(ca_cert.get_subject())
        cert.set_pubkey(key)
        san = f"DNS:{domain}"
        cert.add_extensions([crypto.X509Extension(b"subjectAltName", False, san.encode())])

        cert.sign(ca_key, "sha256")

        with open(cert_path, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(key_path, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    return cert_path, key_path
