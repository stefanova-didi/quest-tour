from typing import TypedDict

from fastapi import HTTPException, Request, status


class AdminSession(TypedDict):
    email: str
    provider: str


def require_admin(request: Request) -> AdminSession:
    session = request.session
    admin = session.get("admin")
    if not admin or not isinstance(admin, dict) or "email" not in admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="admin session required"
        )
    return AdminSession(email=admin["email"], provider=admin.get("provider", ""))
