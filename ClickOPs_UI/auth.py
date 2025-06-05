import hashlib
import yaml
from fastapi import Request
from fastapi.responses import Response

USERS_FILE = "ClickOPs_UI/users.yaml"
SESSION_COOKIE = "clickops_user"

def load_users():
    with open(USERS_FILE, "r") as f:
        return yaml.safe_load(f)

def hash_password(password: str) -> str:
    return hashlib.sha1(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> bool:
    users = load_users()
    hashed = hash_password(password)
    print(f"DEBUG login: {username=} {hashed=} expected={users.get(username, {}).get('password')}")
    return users.get(username, {}).get("password") == hashed

def create_session(response: Response, username: str):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=username,
        httponly=True,
        samesite="strict",
        max_age=3600
    )

def get_current_user(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)

def logout_user(response: Response):
    response.delete_cookie(key=SESSION_COOKIE)
