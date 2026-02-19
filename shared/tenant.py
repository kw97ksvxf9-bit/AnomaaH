from fastapi import Request, HTTPException


class TenantMiddleware:
    """Simple tenant extraction/validation helper.

    Rules:
    - Expects `X-Tenant-ID` header on requests from tenant owners or services.
    - Allows `X-Super-Admin` header to bypass tenant filters (for super admin).
    - Attaches `tenant_id` to `request.state` for downstream usage.
    """

    @staticmethod
    async def attach_tenant(request: Request):
        tenant_id = request.headers.get("X-Tenant-ID")
        is_super = request.headers.get("X-Super-Admin") == "1"

        if not tenant_id and not is_super:
            raise HTTPException(status_code=400, detail="Missing X-Tenant-ID header")

        request.state.tenant_id = None if is_super else tenant_id
        request.state.is_super_admin = is_super
        return


def require_tenant(request: Request):
    if getattr(request.state, "is_super_admin", False):
        return None
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")
    return tenant_id
