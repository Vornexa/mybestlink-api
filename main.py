from aiohttp import web
from route import setup_routes
from src.middleware.base_middleware import base_middleware
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def create_app():
    app = web.Application(middlewares=[base_middleware])
    setup_routes(app)
    return app

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("\n✅ API Running!")
    print(f"➡ Local:    http://127.0.0.1:8000/")
    print(f"➡ Network:  http://{local_ip}:8000/\n")
    web.run_app(create_app(), host="0.0.0.0", port=8000)