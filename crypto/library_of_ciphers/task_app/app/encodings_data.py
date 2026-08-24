import secrets
import string

B32_ALPHABET = string.ascii_uppercase + "234567"
B64_ALPHABET = string.ascii_letters + string.digits + "+/"
HEX_ALPHABET = "0123456789abcdef"


def _rand(alphabet: str, n: int) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(n))


def _make_b32() -> str:
    body = _rand(B32_ALPHABET, secrets.randbelow(4) * 8 + 32)
    return body + "=" * (-len(body) % 8)


def _make_b64() -> str:
    pad = secrets.choice((0, 1, 2))
    return _rand(B64_ALPHABET, secrets.randbelow(4) * 4 + 28 - pad) + "=" * pad


def _make_binary() -> str:
    return "".join(f"{secrets.randbelow(256):08b}" for _ in range(secrets.randbelow(5) + 24))


def _make_hex() -> str:
    return _rand(HEX_ALPHABET, (secrets.randbelow(5) + 24) * 2)


def _make_url() -> str:
    return "".join(f"%{secrets.randbelow(256):02X}" for _ in range(secrets.randbelow(5) + 24))


def _make_ascii() -> str:
    chars = string.ascii_letters + string.digits
    return " ".join(str(ord(secrets.choice(chars))) for _ in range(secrets.randbelow(5) + 24))


ENCODINGS = {
    "binary (base2)": _make_binary,
    "hex (base16)": _make_hex,
    "base32": _make_b32,
    "base64": _make_b64,
    "url encode": _make_url,
    "ascii": _make_ascii,
}


def make_question() -> dict:
    name = secrets.choice(list(ENCODINGS.keys()))
    return {"encoding": name, "data": ENCODINGS[name]()}
