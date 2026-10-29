
import pytest

from security import hash_password, verify_password


def test_password_is_not_stored_as_plain_text():
    password = "MySecurePass123!"
    stored = hash_password(password)

    assert stored != password
    assert verify_password(password, stored)


def test_wrong_password_is_rejected():
    stored = hash_password("MySecurePass123!")

    assert not verify_password("WrongPassword123!", stored)


def test_different_salts_produce_different_hashes():
    password = "MySecurePass123!"

    first = hash_password(password)
    second = hash_password(password)

    assert first != second
    assert verify_password(password, first)
    assert verify_password(password, second)


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_malformed_hash_is_rejected():
    assert not verify_password("anything", "not-a-valid-hash")
