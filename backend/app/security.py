import base64
import hashlib
import hmac
import os

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390_000
SESSION_COOKIE_NAME = "happy_post_session"
SESSION_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)


def create_session_token() -> str:
    return base64.urlsafe_b64encode(os.urandom(SESSION_TOKEN_BYTES)).decode("ascii").rstrip("=")


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
