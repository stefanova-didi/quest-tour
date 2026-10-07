import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

from questtour.settings import Settings

from .deps import AuthProvider

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName"


class EntraAuthProvider(AuthProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.oauth = OAuth()
        self.oauth.register(
            name="microsoft",
            client_id=settings.admin_entra_client_id,
            client_secret=settings.admin_entra_client_secret,
            server_metadata_url=(
                f"https://login.microsoftonline.com/{settings.admin_entra_tenant_id}"
                "/v2.0/.well-known/openid-configuration"
            ),
            # User.Read lets us call /me and /me/transitiveMemberOf for the signed-in user.
            # If group claims are not returned for the target tenant, switch to GroupMember.Read.All
            # and document it here.
            client_kwargs={"scope": "openid email profile User.Read"},
        )

    async def login_url(self, request: Request) -> str:
        redirect_uri = self.settings.admin_entra_redirect_uri
        return await self.oauth.microsoft.authorize_redirect(request, redirect_uri)

    async def process_callback(self, request: Request) -> str:
        token = await self.oauth.microsoft.authorize_access_token(request)
        access_token = token.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="missing access token")

        group_id = self.settings.admin_entra_group_object_id
        filter_query = f"id eq '{group_id}'"
        member_url = (
            "https://graph.microsoft.com/v1.0/me/transitiveMemberOf/"
            "microsoft.graph.group?$select=id&$filter=" + filter_query
        )

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0, read=10.0)
        ) as client:
            user_resp = await client.get(
                GRAPH_ME_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            member_resp = await client.get(
                member_url, headers={"Authorization": f"Bearer {access_token}"}
            )

        if user_resp.status_code != 200 or member_resp.status_code != 200:
            raise HTTPException(status_code=403, detail="cannot verify group membership")
        if not member_resp.json().get("value"):
            raise HTTPException(status_code=403, detail="not in admin group")

        user = user_resp.json()
        email = user.get("mail") or user.get("userPrincipalName")
        if not email:
            raise HTTPException(
                status_code=403, detail="account has no usable email"
            )
        return email

    async def request_magic(self, request, email: str):
        raise NotImplementedError()

    async def consume_magic(self, request, token: str, email: str):
        raise NotImplementedError()
