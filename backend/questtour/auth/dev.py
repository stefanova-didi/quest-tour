import secrets

from fastapi import HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from questtour.settings import Settings

from .deps import AuthProvider

# Module-level replay tracker so the dev provider rejects consumed tokens across requests.
_CONSUMED: set[str] = set()


class DevAuthProvider(AuthProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self._serializer = URLSafeTimedSerializer(settings.admin_session_secret, salt="admin-magic")

    def _allowed(self, email: str) -> bool:
        return email.casefold() in {e.strip().casefold() for e in self.settings.admin_dev_emails}

    async def request_magic(self, request, email: str) -> str:
        if not self._allowed(email):
            raise HTTPException(status_code=400, detail="email not in allowlist")
        token = self._serializer.dumps({"email": email, "nonce": secrets.token_urlsafe(8)})
        return token

    async def consume_magic(self, request, token: str, email: str) -> str:
        try:
            data = self._serializer.loads(token, max_age=15 * 60)
        except (BadSignature, SignatureExpired):
            raise HTTPException(status_code=400, detail="invalid or expired token")
        if data.get("email", "").casefold() != email.casefold() or token in _CONSUMED:
            raise HTTPException(status_code=400, detail="invalid or expired token")
        if not self._allowed(email):
            raise HTTPException(status_code=400, detail="email not in allowlist")
        _CONSUMED.add(token)
        return email

    async def login_url(self, request):
        raise NotImplementedError("dev provider uses magic link, not /login")

    async def process_callback(self, request):
        raise NotImplementedError("dev provider uses magic link, not Entra callback")
