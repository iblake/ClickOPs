# ClickOPs_UI/main.py

import subprocess
import os
import sys
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import yaml
import hashlib

from ClickOPs_UI.auth import authenticate_user, create_session, get_current_user, logout_user

app = FastAPI()

# Montamos los estáticos y templates
app.mount("/static", StaticFiles(directory="ClickOPs_UI/templates/static"), name="static")
templates = Jinja2Templates(directory="ClickOPs_UI/templates")

# Rutas de repositorio
REPO_ROOT = Path(__file__).resolve().parent.parent      # Raíz del repo Git
CATALOG_PATH = REPO_ROOT / "catalog"
MASTER_FILE = REPO_ROOT / "master.yml"

# --- AUTENTICACIÓN ---

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if authenticate_user(username, password):
        response = RedirectResponse(url="/", status_code=303)
        create_session(response, username)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    logout_user(response)
    return response

# --- PÁGINA PRINCIPAL ---

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # No es estrictamente necesario pasar providers/envs aquí, ya que se cargan via JS
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# --- ENDPOINTS DINÁMICOS PARA EL FORMULARIO ---

def get_subdirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted([d.name for d in path.iterdir() if d.is_dir()])

@app.get("/api/providers")
def api_providers():
    base = REPO_ROOT / "oe_01"
    return JSONResponse(get_subdirs(base))

@app.get("/api/environments/{provider}")
def api_envs(provider: str):
    base = REPO_ROOT / f"oe_01/{provider}"
    return JSONResponse(get_subdirs(base))

@app.get("/api/projects/{provider}/{env}")
def api_projects(provider: str, env: str):
    base = REPO_ROOT / f"oe_01/{provider}/{env}"
    return JSONResponse(get_subdirs(base))

@app.get("/api/machines/{provider}/{env}/{project}")
def api_machines(provider: str, env: str, project: str):
    base = REPO_ROOT / f"oe_01/{provider}/{env}/{project}"
    return JSONResponse(get_subdirs(base))

# --- ENDPOINT PARA LEER docs.md DEL CATÁLOGO ---

@app.get("/api/docs/{operation}")
def read_docs(operation: str):
    doc_path = REPO_ROOT / f"catalog/{operation}/docs.md"
    if doc_path.exists():
        return JSONResponse({"content": doc_path.read_text()})
    return JSONResponse({"content": "No documentation found for this operation."})

# --- ENDPOINT PRINCIPAL PARA LANZAR LA OPERACIÓN ---

@app.post("/launch")
def launch(
    request: Request,
    provider: str = Form(...),
    environment: str = Form(...),
    project: str = Form(...),
    machine: str = Form(...),
    operation: str = Form(...),
    crq: str = Form(...)
):
    """
    1) Crea una rama nueva llamada crq-<crq>
    2) Actualiza master.yml agregando la línea import_playbook
    3) Hace commit + push de la rama
    4) Lanza 'gh pr create' para abrir el PR automáticamente
    """

    # --- 0. Verificar usuario ---
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # --- 1. Definir nombres y paths ---
    branch_name = f"crq-{crq}"
    playbook_file = "start_vm.yml" if "start" in operation else "stop_vm.yml"
    import_line = f"- import_playbook: catalog/{operation}/{playbook_file}\n"

    # --- 2. Ir al repositorio Git ---
    os.chdir(str(REPO_ROOT))

    # 2A. Verificar que no exista ya la rama
    existing_branches = subprocess.run(
        ["git", "branch", "--list", branch_name], capture_output=True, text=True
    ).stdout.strip()
    if existing_branches:
        # Si la rama ya existe, la eliminamos localmente para recrear
        subprocess.run(["git", "branch", "-D", branch_name], check=True)

    # 2B. Crear rama desde main
    subprocess.run(["git", "checkout", "main"], check=True)
    subprocess.run(["git", "pull"], check=True)  # para estar al día
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # --- 3. Actualizar master.yml agregando la línea al final ---
    # Si el archivo no existe, lo creamos con la import_line
    if not MASTER_FILE.exists():
        MASTER_FILE.write_text(import_line)
    else:
        # Para no duplicar líneas, verificamos antes
        content = MASTER_FILE.read_text().splitlines(keepends=True)
        if import_line not in content:
            with open(MASTER_FILE, "a") as f:
                f.write(import_line)

    # --- 4. Git add / commit / push ---
    subprocess.run(["git", "add", "master.yml"], check=True)
    commit_msg = f"{crq}: Launch {operation} on {provider}/{environment}/{project}/{machine}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

    # --- 5. Crear Pull Request con GitHub CLI ---
    pr_title = f"{crq} - {operation} on {project}/{machine}"
    pr_body = (
        f"User **{user}** requested `{operation}` on:\n"
        f"- Provider: {provider}\n"
        f"- Environment: {environment}\n"
        f"- Project: {project}\n"
        f"- Machine: {machine}\n\n"
        f"Please review and merge."
    )
    # El comando 'gh pr create' lanzará un prompt si no está autenticado, 
    # o fallará si no hay permisos. Asegúrate de hacer `gh auth login` antes.
    subprocess.run([
        "gh", "pr", "create",
        "--title", pr_title,
        "--body", pr_body,
        "--head", branch_name,
        "--base", "main"
    ], check=False)

    # --- 6. Volver a main (opcional) ---
    subprocess.run(["git", "checkout", "main"], check=True)

    # Redirigir a home (o podrías redirigir a un "dashboard")
    return RedirectResponse(url="/", status_code=303)
