import hashlib
import secrets


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 120000).hex()
    return f'pbkdf2_sha256${salt}${digest}'


def verify_password(password, stored):
    try:
        algo, salt, digest = stored.split('$', 2)
    except ValueError:
        return False
    if algo != 'pbkdf2_sha256':
        return False
    check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 120000).hex()
    return secrets.compare_digest(check, digest)
