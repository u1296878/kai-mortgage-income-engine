from app.security.passwords import hash_password, verify_password


def test_hash_password_does_not_return_plaintext():
    hashed_password = hash_password("secret-password")

    assert hashed_password != "secret-password"


def test_verify_password_accepts_correct_password():
    hashed_password = hash_password("secret-password")

    result = verify_password("secret-password", hashed_password)

    assert result is True


def test_verify_password_rejects_wrong_password():
    hashed_password = hash_password("secret-password")

    result = verify_password("wrong-password", hashed_password)

    assert result is False
