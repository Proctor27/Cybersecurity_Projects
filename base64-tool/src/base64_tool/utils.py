"""
©AngelaMos | 2026
utils.py

Input resolution and string/bytes utility functions

Handles the three input sources the CLI accepts: a positional
argument, a --file path, or piped stdin. Also provides truncate()
for capping display strings, safe_bytes_preview() for converting
raw bytes to a readable preview, and is_printable_text() for
checking whether decoded bytes look like human-readable output.

Key exports:
  resolve_input_bytes() - Returns raw bytes from argument, file, or stdin
  resolve_input_text() - Returns decoded text from argument, file, or stdin
  truncate() - Truncates a string with "..." if it exceeds the length limit
  safe_bytes_preview() - Converts bytes to UTF-8 string or hex fallback
  is_printable_text() - Returns True if bytes decode to mostly printable characters

Connects to:
  detector.py - imports is_printable_text
  peeler.py - imports safe_bytes_preview, truncate
  formatter.py - imports safe_bytes_preview
  cli.py - imports resolve_input_bytes, resolve_input_text
"""

import sys
from pathlib import Path

import typer

import math

from collections import Counter

import urllib.parse


def resolve_input_bytes(
    data: str | None,
    file: Path | None,
) -> bytes:
    if file is not None:
        if not file.exists():
            raise typer.BadParameter(f"File not found: {file}")
        return file.read_bytes()
    if data is not None:
        return data.encode("utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.buffer.read()
    raise typer.BadParameter(
        "No input provided. Pass an argument, use --file, or pipe stdin."
    )


def resolve_input_text(
    data: str | None,
    file: Path | None,
) -> str:
    if file is not None:
        if not file.exists():
            raise typer.BadParameter(f"File not found: {file}")
        return file.read_text("utf-8").strip()
    if data is not None:
        return data.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise typer.BadParameter(
        "No input provided. Pass an argument, use --file, or pipe stdin."
    )


def truncate(text: str, length: int = 72) -> str:
    if len(text) <= length:
        return text
    return text[: length] + "..."


def safe_bytes_preview(data: bytes, length: int = 72) -> str:
    try:
        text = data.decode("utf-8")
        return truncate(text, length)
    except (UnicodeDecodeError, ValueError):
        return truncate(data.hex(), length)


def is_printable_text(data: bytes, threshold: float = 0.8) -> bool:
    try:
        text = data.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return False
    if not text:
        return False
    printable_count = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
    return (printable_count / len(text)) >= threshold


def detect_file_type(data: bytes) -> str | None:
    """Detect file type based on magic bytes / file signatures."""
    if not data or len(data) < 2:
        return None
        
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG image"
    elif data.startswith(b"PK\x03\x04"):
        return "ZIP/DOCX/JAR archive"
    elif data.startswith(b"\x7fELF"):
        return "ELF executable (Linux binary)"
    elif data.startswith(b"MZ"):
        return "PE executable (Windows binary)"
    elif data.startswith(b"%PDF"):
        return "PDF document"
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "GIF image"
        
    return "Unknown binary / text data"



def calculate_shannon_entropy(data: bytes | str) -> float:
    """Calculate the Shannon entropy of a byte string or text on a 0-8 scale."""
    if not data:
        return 0.0
        
    if isinstance(data, str):
        data = data.encode("utf-8")
        
    if len(data) == 0:
        return 0.0
        
    entropy = 0.0
    length = len(data)
    counts = Counter(data)
    
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
        
    return round(entropy, 4)

def interpret_entropy(score: float) -> str:
    """Interpret entropy score based on malware analysis heuristics."""
    if score < 1.0:
        return "Highly structured / repetitive (padding or zeros)"
    elif score < 5.0:
        return "Likely plain text, source code, or low-entropy markup"
    elif score < 7.0:
        return "Compressed data or structured binary format"
    else:
        return "High entropy: Likely encrypted data, packed code, or random bytes"



def encode_url(data: str | bytes) -> str:
    """Encode string or bytes for URLs."""
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="ignore")
    return urllib.parse.quote(data)

def decode_url(data: str, form: bool = False) -> str:
    """Decode URL-encoded strings."""
    if form:
        data = data.replace("+", " ")
    return urllib.parse.unquote(data)