from ..app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

import pytest

password = "test1234"
hashed_password = hash_password(password)


def test_hash_password_does_not_return_plain_password():
    assert hashed_password != password


def test_verify_password_returns_true_for_correct_password():
    assert verify_password(password, hashed_password) is True


def test_verify_password_returns_false_for_wrong_password():
    assert verify_password("wrongpassword", hashed_password) is False


def test_create_access_token_returns_token():
    token = create_access_token(
        {"sub": "test-user-id"}
    )

    assert isinstance(token, str)
    assert token.count(".") == 2


def test_decode_access_token_returns_payload():
    token = create_access_token(
        {"sub": "test-user-id"}
    )

    decoded_token = decode_access_token(token)

    assert decoded_token["sub"] == "test-user-id"
    assert "exp" in decoded_token


def test_decode_invalid_token_raises_error():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("invalid-token")
