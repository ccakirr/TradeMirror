from ..app.core.security import hash_password, verify_password


password = "test1234"
hashed_password = hash_password(password)


def test_hash_password_does_not_return_plain_password():
    assert hashed_password != password


def test_verify_password_returns_true_for_correct_password():
    assert verify_password(password, hashed_password) is True


def test_verify_password_returns_false_for_wrong_password():
    assert verify_password("wrongpassword", hashed_password) is False
