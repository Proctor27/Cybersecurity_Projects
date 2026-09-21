"""
AngelaMos | 2026
encoding.py

XOR cipher and Base64 encoding pipeline for obfuscating C2 traffic

Provides the low-level encoding primitives used on both the server and
implant sides. encode applies a repeating XOR with the shared key then
Base64-encodes the result; decode reverses the operation. This is
traffic obfuscation, not encryption.

Key exports:
  xor_bytes - byte-level XOR with repeating key
  encode - plaintext string to XOR+Base64 string
  decode - XOR+Base64 string back to plaintext

Connects to:
  protocol.py - calls encode and decode
  tests/test_encoding.py - tests all three functions
"""
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
 


"""
def xor_bytes(data: bytes, key: bytes) -> bytes:
    
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encode(payload: str, key: str) -> str:
    
    raw = payload.encode("utf-8")
    xored = xor_bytes(raw, key.encode("utf-8"))
    return base64.b64encode(xored).decode("ascii")


def decode(encoded: str, key: str) -> str:
    
    xored = base64.b64decode(encoded)
    raw = xor_bytes(xored, key.encode("utf-8"))
    return raw.decode("utf-8")
"""

def _derive_key(secret_key: str) -> bytes:
    """Derive a 32-byte AES key from a string secret using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"c2-beacon-aes",
    )
    return hkdf.derive(secret_key.encode("utf-8"))


def encode(data: str, key_str: str) -> str:
    """Encrypts plaintext string to Base64-encoded AES-256-GCM ciphertext."""
    key = _derive_key(key_str)
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)
    plaintext = data.encode("utf-8")

    # AESGCM.encrypt returns ciphertext + 16-byte auth tag
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # Prepend 12-byte nonce to ciphertext and Base64 encode
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decode(encoded_data: str, key_str: str) -> str:
    """Decrypts Base64-encoded AES-256-GCM ciphertext back to plaintext string."""
    key = _derive_key(key_str)
    aesgcm = AESGCM(key)

    payload = base64.b64decode(encoded_data.encode("utf-8"))
    if len(payload) < 28:  # 12 bytes nonce + 16 bytes auth tag minimum
        raise ValueError("Payload too short to contain valid nonce and authentication tag")

    nonce = payload[:12]
    ciphertext = payload[12:]

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")