from typing import Any, Dict, List, Optional
import zlib
import cbor2
import zxingcpp
from PIL import Image
from .utils import CELL_MAP

# Base45 alphabet (RFC 9285) - must match encode.py
_BASE45_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
_BASE45_DECODE = {c: i for i, c in enumerate(_BASE45_ALPHABET)}


def base45_decode(data: str) -> bytes:
    """Decode Base45 string to bytes (RFC 9285)."""
    result = []
    for i in range(0, len(data), 3):
        if i + 2 < len(data):
            # Three characters -> two bytes
            n = (_BASE45_DECODE[data[i]] +
                 _BASE45_DECODE[data[i + 1]] * 45 +
                 _BASE45_DECODE[data[i + 2]] * 2025)
            result.append((n >> 8) & 0xFF)
            result.append(n & 0xFF)
        elif i + 1 < len(data):
            # Two characters -> one byte
            n = _BASE45_DECODE[data[i]] + _BASE45_DECODE[data[i + 1]] * 45
            result.append(n)
    return bytes(result)


def map_ref_to_observation(ref_id: int) -> Optional[str]:
    """Map ref_id back to observation_id."""
    cell = CELL_MAP.get_by('ref_id', ref_id)
    if not cell:
        return None
    return cell[1]


def decode_data(encoded: str, *, prefix: str = "Q1:") -> Optional[Dict[str, Any]]:
    """
    Decode a QR-encoded string back to structured data.

    Returns dict with keys: version, expiration (epoch seconds), barcode, reference_ranges
    """
    if not encoded.startswith(prefix):
        return None

    payload = encoded[len(prefix):]

    try:
        compressed = base45_decode(payload)
        raw = zlib.decompress(compressed)
        packed = cbor2.loads(raw)
    except Exception:
        return None

    if not isinstance(packed, list) or len(packed) < 4:
        return None

    version, exp_days, barcode = packed[0], packed[1], packed[2]
    count_ranges = packed[3]
    pct_ranges = packed[4] if len(packed) > 4 else []

    # Convert days back to epoch seconds
    exp_epoch = exp_days * 86400

    # Reconstruct reference ranges with observation IDs
    reference_ranges = []
    for ref in count_ranges:
        if len(ref) < 3:
            continue
        ref_id, low, high = ref[0], ref[1], ref[2]
        obs_id = map_ref_to_observation(ref_id)
        if obs_id is None:
            continue
        reference_ranges.append({
            'id': obs_id,
            'min': low,
            'max': high,
            'data_type': 'count',
        })

    for ref in pct_ranges:
        if len(ref) < 3:
            continue
        ref_id, low, high = ref[0], ref[1], ref[2]
        obs_id = map_ref_to_observation(ref_id)
        if obs_id is None:
            continue
        reference_ranges.append({
            'id': obs_id,
            'min': low,
            'max': high,
            'data_type': 'percentage',
        })

    return {
        'version': version,
        'expiration': exp_epoch,
        'barcode': barcode,
        'reference_range': reference_ranges
    }


def read_qr(path: str, *, prefix: str = "Q1:") -> Optional[Dict[str, Any]]:
    """
    Read a QR code image and decode its data.

    Args:
        path: Path to the QR code image file.
        prefix: Expected prefix of the encoded payload.

    Returns:
        Decoded dictionary or None if reading/decoding fails.
    """
    try:
        img = Image.open(path)
    except Exception:
        return None

    results = zxingcpp.read_barcodes(img)
    if not results:
        return None

    return decode_data(results[0].text, prefix=prefix)

def read_qr_to_string(path: str) -> Optional[str]:
    """
    Read a QR code image and return the raw encoded string.

    Args:
        path: Path to the QR code image file.

    Returns:
        The data string of the QR, or None if reading fails.
    """
    try:
        img = Image.open(path)
    except Exception:
        return None

    results = zxingcpp.read_barcodes(img)
    if not results:
        return None

    return results[0].text