import json
import os

import pytest
import segno

from scqr import encode_data, decode_data, generate_qr, read_qr
from scqr.qr.encode import base45_encode
from scqr.qr.decode import base45_decode


@pytest.fixture
def test_ranges():
    """Load test data from JSON file."""
    test_data_path = os.path.join(os.path.dirname(__file__), 'data', 'test_ranges.json')
    with open(test_data_path, 'r') as f:
        return json.load(f)


class TestQRGeneration:
    def test_encode_has_prefix(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        assert encoded.startswith("Q1:")

    def test_generate_qr_creates_file(self, test_ranges, tmp_path):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        generate_qr(encoded, path=str(tmp_path) + '/')
        assert (tmp_path / 'qr.png').exists()

    def test_qr_version(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        qr = segno.make(encoded, error='M')
        assert isinstance(qr.version, int)
        assert qr.version <= 10

class TestDecodeRoundtrip:
    def test_decode_returns_valid_data(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        decoded = decode_data(encoded)
        assert decoded is not None

    def test_decode_version(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        decoded = decode_data(encoded)
        assert decoded is not None
        assert decoded['version'] == 1

    def test_decode_barcode(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        decoded = decode_data(encoded)
        assert decoded is not None
        assert decoded['barcode'] == test_ranges['barcode']

    def test_decode_reference_ranges(self, test_ranges):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        decoded = decode_data(encoded)
        assert decoded is not None

        original_ranges = {r['id']: r for r in test_ranges['reference_range']}
        decoded_ranges = {r['id']: r for r in decoded['reference_range']}

        assert len(decoded_ranges) == len(original_ranges)

        for obs_id, original in original_ranges.items():
            assert obs_id in decoded_ranges
            assert decoded_ranges[obs_id]['min'] == original['min']
            assert decoded_ranges[obs_id]['max'] == original['max']
            assert decoded_ranges[obs_id]['data_type'] == original['data_type']


class TestDecodeInvalid:
    @pytest.mark.parametrize("invalid_input", [
        "INVALID",
        "Q1:!!!",
        "",
        "Q2:VALIDBASE45",
    ])
    def test_invalid_input_returns_none(self, invalid_input):
        assert decode_data(invalid_input) is None


class TestReadQR:
    def test_read_qr_roundtrip(self, test_ranges, tmp_path):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        generate_qr(encoded, path=str(tmp_path) + '/')
        qr_path = str(tmp_path / 'qr.png')
        decoded = read_qr(qr_path)
        assert decoded is not None
        assert decoded['version'] == 1
        assert decoded['barcode'] == test_ranges['barcode']
        assert len(decoded['reference_range']) == len(test_ranges['reference_range'])

    def test_read_qr_reference_ranges(self, test_ranges, tmp_path):
        encoded = encode_data(test_ranges)
        assert encoded is not None
        generate_qr(encoded, path=str(tmp_path) + '/')
        qr_path = str(tmp_path / 'qr.png')
        decoded = read_qr(qr_path)
        assert decoded is not None

        original_ranges = {r['id']: r for r in test_ranges['reference_range']}
        decoded_ranges = {r['id']: r for r in decoded['reference_range']}

        for obs_id, original in original_ranges.items():
            assert obs_id in decoded_ranges
            assert decoded_ranges[obs_id]['min'] == original['min']
            assert decoded_ranges[obs_id]['max'] == original['max']

    def test_read_qr_invalid_image(self, tmp_path):
        fake_img = tmp_path / 'fake.png'
        fake_img.write_bytes(b'\x00\x00\x00')
        assert read_qr(str(fake_img)) is None


class TestBase45:
    @pytest.mark.parametrize("data", [
        b'hello',
        b'\x00\xff',
        b'',
        b'a',
        b'ab',
        b'abc',
        bytes(range(256)),
    ])
    def test_roundtrip(self, data):
        encoded = base45_encode(data)
        decoded = base45_decode(encoded)
        assert decoded == data
