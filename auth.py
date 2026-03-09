import secrets
TOKENS = {}
USERS = {
    "admin": "admin123"  
}
def login(user, password):
    if USERS.get(user) == password:
        token = secrets.token_hex(16)
        TOKENS[token] = user
        return token
    return None
def verificar_token(token):
    return token in TOKENS
