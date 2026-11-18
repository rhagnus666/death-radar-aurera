import hmac
from fastapi import Request

def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))

def password_matches(candidate: str, configured: str) -> bool:
    return bool(configured) and hmac.compare_digest(candidate.encode(), configured.encode())
