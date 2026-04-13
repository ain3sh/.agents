#!/usr/bin/env python3
"""
Upload an .excalidraw file to excalidraw.com and print a shareable URL.

No account required. The diagram is encrypted client-side (AES-GCM) before
upload -- the encryption key is embedded in the URL fragment, so the server
never sees plaintext.

Requirements:
    pip install cryptography

Usage:
    python upload.py <path-to-file.excalidraw>
"""

import json
import os
import struct
import sys
import zlib
import base64
import urllib.request

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("Error: 'cryptography' package is required for upload.")
    print("Install it with: pip install cryptography")
    sys.exit(1)

UPLOAD_URL = "https://json.excalidraw.com/api/v2/post/"


def concat_buffers(*buffers: bytes) -> bytes:
    parts = [struct.pack(">I", 1)]
    for buf in buffers:
        parts.append(struct.pack(">I", len(buf)))
        parts.append(buf)
    return b"".join(parts)


def upload(excalidraw_json: str) -> str:
    file_metadata = json.dumps({}).encode("utf-8")
    data_bytes = excalidraw_json.encode("utf-8")
    inner_payload = concat_buffers(file_metadata, data_bytes)

    compressed = zlib.compress(inner_payload)

    raw_key = os.urandom(16)
    iv = os.urandom(12)
    aesgcm = AESGCM(raw_key)
    encrypted = aesgcm.encrypt(iv, compressed, None)

    encoding_meta = json.dumps({
        "version": 2,
        "compression": "pako@1",
        "encryption": "AES-GCM",
    }).encode("utf-8")

    payload = concat_buffers(encoding_meta, iv, encrypted)

    req = urllib.request.Request(UPLOAD_URL, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Upload failed with HTTP {resp.status}")
        result = json.loads(resp.read().decode("utf-8"))

    file_id = result.get("id")
    if not file_id:
        raise RuntimeError(f"Upload returned no file ID. Response: {result}")

    encoded = base64.urlsafe_b64encode(raw_key).rstrip(b"=").decode("ascii")
    return f"https://excalidraw.com/#json={file_id},{encoded}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload.py <path-to-file.excalidraw>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        doc = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: File is not valid JSON: {e}")
        sys.exit(1)

    if "elements" not in doc:
        print("Warning: File does not contain an 'elements' key. Uploading anyway.")

    url = upload(content)
    print(url)


if __name__ == "__main__":
    main()
