import hashlib


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def file_size_bytes(content: bytes) -> int:
    return len(content)