from aiohttp import web

@web.middleware
async def base_middleware(request, handler):
    try:
        print(f"[{request.method}] {request.path}")
        return await handler(request)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
