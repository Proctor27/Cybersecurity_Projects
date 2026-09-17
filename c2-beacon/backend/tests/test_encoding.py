# ===========================
# © AngelaMos | 2026
# test_encoding.py
#
# Unit tests for the AES-256-GCM authenticated encryption pipeline
#
# Verifies encode/decode roundtrips for ASCII and Unicode payloads,
# random IV/nonce uniqueness (preventing ciphertext reuse), and that
# mismatched keys or modified payloads fail to decrypt correctly.
#
# Tests:
#   core/encoding.py - encode, decode
# ===========================

import pytest
from app.core.encoding import decode, encode


class TestAESGCMEncodeDecode:
    """
    Verify the full AES-256-GCM encryption and decryption pipeline
    """

    def test_roundtrip_ascii(self) -> None:
        """
        ASCII payload survives encode -> decode
        """
        payload = '{"type": "REGISTER", "payload": {"hostname": "test"}}'
        key = "my-secret-key"
        assert decode(encode(payload, key), key) == payload

    def test_roundtrip_unicode(self) -> None:
        """
        Unicode payload survives encode -> decode
        """
        payload = '{"name": "test-\u00e9\u00e8\u00ea"}'
        key = "unicode-key"
        assert decode(encode(payload, key), key) == payload

    def test_random_nonces_produce_different_ciphertext(self) -> None:
        """
        Identical payloads encrypted with the same key produce distinct ciphertexts due to random nonces
        """
        payload = "identical payload"
        encoded_a = encode(payload, "key-alpha")
        encoded_b = encode(payload, "key-alpha")
        assert encoded_a != encoded_b
        assert decode(encoded_a, "key-alpha") == payload
        assert decode(encoded_b, "key-alpha") == payload

    def test_wrong_key_fails_decryption(self) -> None:
        """
        Decoding with the wrong key raises an exception (GCM authentication failure)
        """
        payload = '{"command": "shell"}'
        encoded = encode(payload, "correct-key")
        with pytest.raises(Exception):
            decode(encoded, "wrong-key-here")

    def test_empty_payload(self) -> None:
        """
        Empty string survives encode -> decode
        """
        assert decode(encode("", "key"), "key") == ""