from __future__ import annotations

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(BASE62_ALPHABET)


def encode_base62(number: int, min_length: int = 1) -> str:
    if number < 0:
        raise ValueError("Base62 input must be non-negative")

    if number == 0:
        encoded = BASE62_ALPHABET[0]
    else:
        chars: list[str] = []
        while number:
            number, remainder = divmod(number, BASE)
            chars.append(BASE62_ALPHABET[remainder])
        encoded = "".join(reversed(chars))

    return encoded.rjust(min_length, BASE62_ALPHABET[0])


def decode_base62(value: str) -> int:
    if not value:
        raise ValueError("Base62 value cannot be empty")

    number = 0
    for char in value:
        try:
            digit = BASE62_ALPHABET.index(char)
        except ValueError as exc:
            raise ValueError(f"Invalid Base62 character: {char}") from exc
        number = number * BASE + digit
    return number
