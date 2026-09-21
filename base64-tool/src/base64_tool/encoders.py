"""
©AngelaMos | 2026
encoders.py

Encode and decode functions for all five supported formats

Provides individual encode/decode functions for base64, base64url,
base32, hex, and URL percent-encoding, plus a dispatch registry
(ENCODER_REGISTRY) that maps each EncodingFormat to its function pair.
The top-level encode(), decode(), and try_decode() functions route
calls through the registry and handle all common decoding exceptions.

Key exports:
  encode() - Encode bytes to string for a given format
  decode() - Decode string to bytes for a given format
  try_decode() - Like decode() but returns None on failure instead of raising
  ENCODER_REGISTRY - Dict mapping EncodingFormat to (encoder, decoder) function pairs
  EncoderFn, DecoderFn - Type aliases for encoder and decoder callables

Connects to:
  constants.py - imports EncodingFormat
  detector.py - imports try_decode
  cli.py - imports encode, decode, encode_url, decode_url
  test_encoders.py - tests all functions directly
  test_properties.py - property-based roundtrip tests
  test_peeler.py - imports encode to build test inputs
"""

import base64 as b64
import binascii
import codecs
from collections.abc import Callable
from urllib.parse import (
    quote,
    quote_plus,
    unquote,
    unquote_plus,
)
from base64_tool.constants import EncodingFormat


type EncoderFn = Callable[[bytes], str]
type DecoderFn = Callable[[str], bytes]


"""def encode_base64(data: bytes) -> str:
    return b64.b64encode(data).decode("ascii")


def decode_base64(data: str) -> bytes:
    cleaned = "".join(data.split())
    return b64.b64decode(cleaned, validate=True)"""

def encode_base64(data: bytes, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") -> str:
    """Encode bytes to Base64, supporting standard or custom alphabets."""
    if alphabet == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/":
        return b64.b64encode(data).decode("ascii")
    return custom_base64_encode(data, alphabet)


def decode_base64(data: str, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") -> bytes:
    """Decode Base64 string, supporting standard or custom alphabets."""
    cleaned = "".join(data.split())
    if alphabet == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/":
        return b64.b64decode(cleaned, validate=True)
    return custom_base64_decode(cleaned, alphabet)


def encode_base64url(data: bytes) -> str:
    return b64.urlsafe_b64encode(data).decode("ascii")


def decode_base64url(data: str) -> bytes:
    cleaned = "".join(data.split())
    return b64.urlsafe_b64decode(cleaned)


def encode_base32(data: bytes) -> str:
    return b64.b32encode(data).decode("ascii")


def decode_base32(data: str) -> bytes:
    cleaned = "".join(data.split()).upper()
    return b64.b32decode(cleaned)


def encode_hex(data: bytes) -> str:
    return data.hex()


def decode_hex(data: str) -> bytes:
    cleaned = data.strip()
    for sep in (" ", ":", "-", "."):
        cleaned = cleaned.replace(sep, "")
    return bytes.fromhex(cleaned)


def encode_url(data: bytes, *, form: bool = False) -> str:
    text = data.decode("utf-8")
    if form:
        return quote_plus(text)
    return quote(text, safe="")


def decode_url(data: str, *, form: bool = False) -> bytes:
    if form:
        return unquote_plus(data).encode("utf-8")
    return unquote(data).encode("utf-8")

def encode_rot13(data: bytes) -> str:
    """ Encode bytes to a ROT13 string """
    text = data.decode("utf-8", errors="ignore")
    return codecs.encode(text, "rot13")

def decode_rot13(data: str) -> bytes:
    """ Decode a ROT13 string back to bytes."""
    #ROT13 is its own inverse, so encoding it again decodes it
    decoded_text = codecs.encode(data, "rot13")
    return decoded_text.encode("utf-8")

def encode_ascii85(data: bytes) -> str:
    """Encode bytes to an ASCII85 string."""
    return b64.a85encode(data).decode("ascii")


def decode_ascii85(data: str) -> bytes:
    """Decode an ASCII85 string to bytes, handling Adobe wrappers if present."""
    cleaned = data.strip()
    if cleaned.startswith("<~") and cleaned.endswith("~>"):
        cleaned = cleaned[2:-2]
    return b64.a85decode(cleaned)

def custom_base64_encode(data: bytes, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") -> str:
    """Encode bytes using a custom 64-character alphabet with manual bit shifting."""
    if len(alphabet) < 64:
        raise ValueError("Custom alphabet must contain at least 64 characters.")
    
    padding_char = alphabet[64] if len(alphabet) > 64 else "="
    
    output = []
    # Process input bytes in blocks of 3
    for i in range(0, len(data), 3):
        chunk = data[i:i+3]
        chunk_len = len(chunk)
        
        # Pack up to 3 bytes into a 24-bit integer
        val = 0
        for b in chunk:
            val = (val << 8) + b
        
        # Shift for 4 blocks of 6 bits if we have a full 3 bytes, otherwise handle padding
        if chunk_len == 3:
            output.append(alphabet[(val >> 18) & 0x3F])
            output.append(alphabet[(val >> 12) & 0x3F])
            output.append(alphabet[(val >> 6) & 0x3F])
            output.append(alphabet[val & 0x3F])
        elif chunk_len == 2:
            val = val << 2  # pad remaining bits
            output.append(alphabet[(val >> 12) & 0x3F])
            output.append(alphabet[(val >> 6) & 0x3F])
            output.append(alphabet[val & 0x3F])
            output.append(padding_char)
        elif chunk_len == 1:
            val = val << 4  # pad remaining bits
            output.append(alphabet[(val >> 6) & 0x3F])
            output.append(alphabet[val & 0x3F])
            output.append(padding_char)
            output.append(padding_char)
            
    return "".join(output)


def custom_base64_decode(data: str, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/") -> bytes:
    """Decode custom Base64 string back to raw bytes using manual bit shifting."""
    if len(alphabet) < 64:
        raise ValueError("Custom alphabet must contain at least 64 characters.")
    
    padding_char = alphabet[64] if len(alphabet) > 64 else "="
    
    # Strip padding characters for parsing length
    clean_data = data.rstrip(padding_char)
    padding_count = len(data) - len(clean_data)
    
    # Map characters back to their 6-bit index values
    char_map = {char: idx for idx, char in enumerate(alphabet[:64])}
    
    # Convert clean data characters into a continuous bit stream or blocks of 4
    output = bytearray()
    
    # Process blocks of 4 characters
    for i in range(0, len(clean_data), 4):
        chunk = clean_data[i:i+4]
        val = 0
        bits_collected = 0
        
        for c in chunk:
            if c not in char_map:
                raise ValueError(f"Character '{c}' not found in custom alphabet.")
            val = (val << 6) + char_map[c]
            bits_collected += 6
            
        # Unpack bits into bytes depending on how many characters we received in this chunk
        if len(chunk) == 4:
            output.append((val >> 16) & 0xFF)
            output.append((val >> 8) & 0xFF)
            output.append(val & 0xFF)
        elif len(chunk) == 3:
            val = val >> 2  # account for shifted padding bits
            output.append((val >> 8) & 0xFF)
            output.append(val & 0xFF)
        elif len(chunk) == 2:
            val = val >> 4  # account for shifted padding bits
            output.append(val & 0xFF)
            
    return bytes(output)

def stream_encode_base64(file_obj, chunk_size: int = 3, **kwargs):
    """Generator to stream-encode file-like objects in chunks of 3 bytes."""
    alphabet = kwargs.get("alphabet", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield custom_base64_encode(chunk, alphabet=alphabet)


def stream_decode_base64(file_obj, chunk_size: int = 4, **kwargs):
    """Generator to stream-decode file-like objects in chunks of 4 characters."""
    alphabet = kwargs.get("alphabet", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
    buffer = ""
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            if buffer:
                yield custom_base64_decode(buffer, alphabet=alphabet)
            break
        buffer += data
        if len(buffer) >= chunk_size:
            to_process = buffer[:chunk_size]
            buffer = buffer[chunk_size:]
            yield custom_base64_decode(to_process, alphabet=alphabet)

ENCODER_REGISTRY: dict[
    EncodingFormat,
    tuple[EncoderFn, DecoderFn],
] = {
    EncodingFormat.BASE64: (encode_base64, decode_base64),
    EncodingFormat.BASE64URL: (encode_base64url, decode_base64url),
    EncodingFormat.BASE32: (encode_base32, decode_base32),
    EncodingFormat.HEX: (encode_hex, decode_hex),
    EncodingFormat.URL: (
        lambda data: encode_url(data),
        lambda data: decode_url(data),
    ),
    EncodingFormat.ROT13: (encode_rot13, decode_rot13),
    EncodingFormat.ASCII85: (encode_ascii85, decode_ascii85),
}

def encode(data: bytes, fmt: EncodingFormat, **kwargs) -> str:
    """Route encoding through the registry."""
    if fmt == EncodingFormat.BASE64:
        return encode_base64(data, **kwargs)
    
    encoder, _ = ENCODER_REGISTRY[fmt]
    return encoder(data)


def decode(data: str, fmt: EncodingFormat, **kwargs) -> bytes:
    """Route decoding through the registry."""
    if fmt == EncodingFormat.BASE64:
        return decode_base64(data, **kwargs)
        
    _, decoder = ENCODER_REGISTRY[fmt]
    return decoder(data)


def try_decode(data: str, fmt: EncodingFormat) -> bytes | None:
    try:
        return decode(data, fmt)
    except (
        ValueError,
        binascii.Error,
        UnicodeDecodeError,
        UnicodeEncodeError,
    ):
        return None