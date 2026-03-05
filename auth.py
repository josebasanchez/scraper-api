import secrets

TOKENS = {}

def generar_token(user):
    token = secrets.token_hex(16)
    TOKENS[token] = user
    return token

def verificar_token(token):
    return token in TOKENS