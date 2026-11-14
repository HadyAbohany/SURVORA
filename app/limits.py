"""Bound JSON input before FastAPI parses it, including chunked requests."""
import json
import math

from starlette.responses import JSONResponse


class RequestLimit:
    def __init__(self, app, max_bytes=32_768):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST':
            await self.app(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body.extend(message.get('body', b''))
            if len(body) > self.max_bytes:
                await JSONResponse({'detail': 'Request exceeds 32 KiB'}, status_code=413)(
                    scope, receive, send)
                return
            if not message.get('more_body'):
                break

        # Preserve FastAPI's malformed-JSON diagnostics while rejecting non-finite numbers
        # in the legacy arbitrary dictionaries, which cannot be serialized in a reply.
        def finite(value):
            result = float(value)
            if not math.isfinite(result):
                raise OverflowError
            return result

        try:
            json.loads(body, parse_constant=finite, parse_float=finite)
        except (ValueError, UnicodeError):
            pass
        except (OverflowError, RecursionError):
            await JSONResponse({'detail': 'Invalid JSON number or nesting'}, status_code=422)(
                scope, receive, send)
            return

        async def buffered_receive():
            nonlocal body
            if body is None:
                return await receive()
            data, body = bytes(body), None
            return {'type': 'http.request', 'body': data, 'more_body': False}

        await self.app(scope, buffered_receive, send)
