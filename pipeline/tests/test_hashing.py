import pytest

from pipeline.hashing import _compute_hash_of_string


@pytest.mark.unit
@pytest.mark.parametrize(
    "string, result",
    [
        ("a", "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"),
        (
            "Hello/alsdkasd/{{}}asdsad",
            "86d6fce6d34c8a84a7f84906ad5b0db146efa8d60cff0cd73e5e2122bb9930cf",
        ),
    ],
)
def test_compute_hash_of_string(string, result):
    hash_ = _compute_hash_of_string(string)
    assert hash_ == result
