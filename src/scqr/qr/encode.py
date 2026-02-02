from typing import Any, Dict, List, Optional
import zlib
import cbor2
from datetime import datetime, timezone
import segno
from .utils import to_epoch_seconds, map_observation_to_ref

# Base45 alphabet (RFC 9285) - optimized for QR alphanumeric mode
_BASE45_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

def base45_encode(data: bytes) -> str:
    """Encode bytes to Base45 string (RFC 9285)."""
    result = []
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            # Two bytes -> three characters
            n = (data[i] << 8) | data[i + 1]
            result.append(_BASE45_ALPHABET[n % 45])
            result.append(_BASE45_ALPHABET[(n // 45) % 45])
            result.append(_BASE45_ALPHABET[n // 2025])
        else:
            # One byte -> two characters
            n = data[i]
            result.append(_BASE45_ALPHABET[n % 45])
            result.append(_BASE45_ALPHABET[n // 45])
    return ''.join(result)

def encode_data(data: dict, *, prefix: str = "Q1:"):
    barcode = data.get('barcode', 'mb')
    expiration = data.get('expiration', None)
    reference_ranges = data.get('reference_range', [])
    exp_epoch = to_epoch_seconds(expiration)

    if not exp_epoch:
        return None

    # Convert to days since epoch (smaller integer for CBOR)
    exp_days = exp_epoch // 86400

    refined_ranges = []
    for refe in reference_ranges:
        id = refe.get('id', None)
        low = refe.get('min', None)
        high = refe.get('max', None)
        if not (id or low or high):
            continue
        refined_ranges.append([map_observation_to_ref(id), low, high])

    packed = [1, exp_days, barcode, refined_ranges]
    raw = cbor2.dumps(packed)
    compressed = zlib.compress(raw, level=9)
    encoded = base45_encode(compressed)

    return prefix + encoded

def generate_qr(data,path,*, scale=5, border=4):
    qr = segno.make(data, error='M')
    qr.save(path + 'qr.png', scale=scale, border=border)


def create_qr_from_data(data,path,*,scale=1,border=4):
    data_str = encode_data(data)
    generate_qr(data_str,scale=scale,border=border,path=path)