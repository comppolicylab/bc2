import pytest

from .codec import EmbeddingCodec


@pytest.mark.parametrize(
    "dimensionality,expected_size",
    [
        (0, 0),
        (1, 8),
        (1024, 8192),
        (2048, 16384),
        (4096, 32768),
    ],
)
def test_calc_binary_size(dimensionality: int, expected_size: int):
    assert EmbeddingCodec.calc_binary_size(dimensionality) == expected_size


def test_to_and_from_binary():
    vector = [-0.002, -0.023, 0.005, 0.027]
    embedding = EmbeddingCodec(vector)
    binary = embedding.to_binary()
    assert binary == (
        b"\xbf`bM\xd2\xf1\xa9\xfc\xbf\x97\x8dO"
        b"\xdf;dZ?tz\xe1G\xae\x14{?\x9b\xa5\xe3S\xf7\xce\xd9"
    )

    assert EmbeddingCodec.pack(vector) == bytearray(binary)

    e2 = EmbeddingCodec.from_binary(binary)
    assert e2.to_list() == vector
    assert list(EmbeddingCodec.unpack(binary)) == vector


def test_to_and_from_base64():
    vector = [-0.002, -0.023, 0.005, 0.027]
    embedding = EmbeddingCodec(vector)
    base64_str = embedding.to_base64()
    assert base64_str == "v2BiTdLxqfy/l41P3ztkWj90euFHrhR7P5ul41P3ztk="

    e2 = EmbeddingCodec.from_binary(base64_str)
    assert e2.to_list() == vector


def test_to_list():
    vector = [-0.002, -0.023, 0.005, 0.027]
    embedding = EmbeddingCodec(vector)
    assert embedding.to_list() == vector
    # But the list should be a _copy_, and internally stored as a tuple.
    assert embedding.vector == tuple(vector)
    assert embedding.to_list() is not vector
