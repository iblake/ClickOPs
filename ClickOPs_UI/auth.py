from fastapi import Response, Request

# Usuarios hardcodeados con contraseña y entorno asignado
USERS = {
    "admindev": {"password": "devpass123", "env": "dev"},
    "adminpro": {"password": "propass123", "env": "prod"},
}

# Sesiones en memoria simple (solo para demo)
sessions = {}

def authenticate_user(username: str, password: str) -> bool:
    user = USERS.get(username)
    return user is not None and user["password"] == password

def create_session(response: Response, username: str):
    sessions[username] = True
    response.set_cookie(key="session_user", value=username)

def get_current_user(request: Request) -> str | None:
    username = request.cookies.get("session_user")
    if username in sessions:
        return username
    return None

def logout_user(response: Response):
    response.delete_cookie("session_user")
