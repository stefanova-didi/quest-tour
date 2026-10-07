from abc import ABC, abstractmethod

from fastapi import Request

from questtour.settings import Settings


class AuthProvider(ABC):
    @abstractmethod
    async def login_url(self, request: Request) -> str: ...

    @abstractmethod
    async def process_callback(self, request: Request) -> str: ...  # returns email

    @abstractmethod
    async def request_magic(self, request: Request, email: str) -> str: ...  # dev only

    @abstractmethod
    async def consume_magic(self, request: Request, token: str, email: str) -> str: ...


def get_auth_provider(settings: Settings) -> AuthProvider:
    if settings.admin_auth_provider == "dev":
        from .dev import DevAuthProvider

        return DevAuthProvider(settings)
    from .entra import EntraAuthProvider

    return EntraAuthProvider(settings)
