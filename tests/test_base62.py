import pytest

from app.utils.base62 import decode_base62, encode_base62


@pytest.mark.parametrize(
    ("number", "encoded"),
    [
        (0, "0"),
        (1, "1"),
        (61, "z"),
        (62, "10"),
        (3843, "zz"),
        (3844, "100"),
    ],
)
def test_encode_base62(number: int, encoded: str) -> None:
    assert encode_base62(number) == encoded


def test_encode_base62_with_min_length() -> None:
    assert encode_base62(62, min_length=4) == "0010"


def test_decode_base62_round_trip() -> None:
    for number in [0, 1, 62, 999, 100000, 999999999]:
        assert decode_base62(encode_base62(number)) == number


def test_encode_base62_rejects_negative_numbers() -> None:
    with pytest.raises(ValueError):
        encode_base62(-1)
