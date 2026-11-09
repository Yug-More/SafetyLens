"""Count bytes as received, before multipart spooling; never buffer request bodies."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class BodyBudgetMiddleware:
    def __init__(self, app, *, maximum_bytes, metadata_bytes=262144):
        self.app, self.maximum_bytes, self.metadata_bytes = (
            app,
            maximum_bytes,
            metadata_bytes,
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        multipart = (
            headers.get(b"content-type", b"").lower().startswith(b"multipart/form-data")
        )
        path = scope.get("path", "").rstrip("/")
        media_route = path in {
            "/api/videos/upload",
            "/api/procedures/upload",
            "/api/detector/events",
        }
        snapshot_route = path.startswith("/api/detector/snapshot/")
        limit = self.metadata_bytes
        if multipart and scope.get("method") == "POST":
            if media_route:
                limit = self.maximum_bytes
            elif snapshot_route:
                limit = min(self.maximum_bytes, 2 * 1024 * 1024)
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0:
                raise ValueError()
        except ValueError:
            return await JSONResponse(
                {
                    "error": {
                        "code": "INVALID_CONTENT_LENGTH",
                        "message": "Invalid body length.",
                    }
                },
                status_code=400,
            )(scope, receive, send)
        if length > limit:
            return await JSONResponse(
                {
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": "Request exceeds ingress byte budget.",
                    }
                },
                status_code=413,
            )(scope, receive, send)
        consumed = 0

        async def bounded_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > limit:
                    raise HTTPException(413, "Request exceeds ingress byte budget.")
            return message

        await self.app(scope, bounded_receive, send)
