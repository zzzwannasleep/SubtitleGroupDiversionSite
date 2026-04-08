import secrets


def generate_passkey() -> str:
    return secrets.token_hex(16)
