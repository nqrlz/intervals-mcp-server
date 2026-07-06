"""
Remote (HTTP) entrypoint for deploying this MCP server on a public host (e.g. Fly.io).

Claude's custom-connector UI for remote MCP servers has no field for a bearer
token or API key -- only a URL. So the shared secret lives in the URL path
itself (https://<host>/<MCP_URL_SECRET>/mcp) and this middleware strips it
after checking it, rather than requiring a header.
"""

import os

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from intervals_mcp_server.mcp_instance import mcp

# Import server.py for its side effect of importing every tools.* module,
# which registers all @mcp.tool() functions on the shared `mcp` instance.
import intervals_mcp_server.server  # noqa: E402,F401  pylint: disable=wrong-import-position,unused-import

SECRET = os.environ["MCP_URL_SECRET"]

# The MCP SDK's DNS-rebinding protection checks the Host/Origin headers
# against an allowlist meant for localhost dev servers. This server is
# intentionally public and gated by the URL secret instead, so disable it
# rather than maintaining a Host allowlist per deployment hostname.
mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)


class SecretPathMiddleware(BaseHTTPMiddleware):
    """Require the first path segment to match MCP_URL_SECRET, then strip it."""

    async def dispatch(self, request: Request, call_next):
        parts = request.url.path.lstrip("/").split("/", 1)
        if not parts or parts[0] != SECRET:
            return PlainTextResponse("Not found", status_code=404)

        remainder = "/" + (parts[1] if len(parts) > 1 else "")
        request.scope["path"] = remainder
        request.scope["raw_path"] = remainder.encode()
        return await call_next(request)


app = mcp.streamable_http_app()
app.add_middleware(SecretPathMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
