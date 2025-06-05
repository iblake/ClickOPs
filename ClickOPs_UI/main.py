# ClickOPs_UI/main.py

import subprocess
import os
import shutil
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import yaml
import hashlib

from ClickOPs_UI.auth import authenticate_user, create_session, get_current_user, logout_user

app = FastAPI()

# Montamos estáticos y templates
app.mount("/static", StaticFiles(directory="ClickOPs_UI/templates/static"), name="static")
templates = Jinja2Templates(directory="ClickOPs_UI/templates")

# Paths en el repositorio
REPO_ROOT    = Path(__file__).resolve().parent.parent      # Raíz del repo Git
CATALOG_PATH = REPO_ROOT / "catalog"

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
    1) Si operation contiene 'provision', copia el módulo Terraform a la carpeta de inventario,
       crea terraform.tfvars.json y un run_terraform.txt para que el workflow de Terraform se ejecute.
    2) Si operation es 'start' o 'stop', actualiza master.yml con Ansible import_playbook y crea PR.
    """

    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Ruta de la carpeta de inventario de esta VM
    inv_path = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/{machine}"
    inv_path.mkdir(parents=True, exist_ok=True)

    # ––– CASO PROVISION VM (Terraform) –––
    if "provision" in operation:
        # 1. Copiar módulo Terraform del catálogo
        src_tf_folder  = CATALOG_PATH / operation
        dest_tf_folder = inv_path / "terraform"
        shutil.copytree(src_tf_folder, dest_tf_folder, dirs_exist_ok=True)

        # 2. Crear terraform.tfvars.json con variables de ejemplo (ajústalas a tu entorno)
        tfvars = {
            "compartment_id":      "ocid1.compartment.oc1..exampleuniqueID",
            "availability_domain": "Uocm:EU-FRANKFURT-1-AD-1",
            "subnet_id":           "ocid1.subnet.oc1..exampleuniqueID",
            "image_id":            "ocid1.image.oc1..exampleuniqueID",
            "shape":               "VM.Standard.E2.1.Micro",
            "ssh_public_key":      "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD...",  # Tu clave real
            "display_name":        machine,
            "region":              "eu-frankfurt-1",
            "profile":             "DEFAULT",
            "output_vm_vars_path": str(inv_path / "vm_vars.yml")
        }
        # Escribimos el JSON en terraform.tfvars.json
        with open(dest_tf_folder / "terraform.tfvars.json", "w") as f:
            yaml.dump(tfvars, f)

        # 3. Crear marcador para que el workflow de Terraform lo detecte
        (inv_path / "run_terraform.txt").write_text("run-do-terraform-apply")

        # Redirigimos a la página principal
        return RedirectResponse(url="/", status_code=303)

    # ––– CASO START / STOP VM (Ansible) –––
    if "start" in operation:
        playbook_file = "start_vm.yml"
    elif "stop" in operation:
        playbook_file = "stop_vm.yml"
    else:
        playbook_file = ""

    import_line = f"- import_playbook: catalog/{operation}/{playbook_file}\n"

    # Aquí vendría tu lógica existente para:
    #   a) Crear rama crq-<crq>
    #   b) Actualizar master.yml con import_line
    #   c) Git commit + push de la rama
    #   d) gh pr create para abrir el PR hacia main
    #
    # (Este bloque no se muestra aquí para no repetirlo, pues ya lo tenías anteriormente.)

    # Ejemplo simplificado (reemplaza con tu lógica real):
    branch_name = f"crq-{crq}"
    os.chdir(str(REPO_ROOT))
    subprocess.run(["git", "checkout", "main"], check=True)
    subprocess.run(["git", "pull"], check=True)
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    MASTER_FILE = REPO_ROOT / "master.yml"
    if not MASTER_FILE.exists():
        MASTER_FILE.write_text(import_line)
    else:
        content = MASTER_FILE.read_text().splitlines(keepends=True)
        if import_line not in content:
            with open(MASTER_FILE, "a") as f:
                f.write(import_line)

    subprocess.run(["git", "add", "master.yml"], check=True)
    commit_msg = f"{crq}: Launch {operation} on {provider}/{environment}/{project}/{machine}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

    pr_title = f"{crq} - {operation} on {project}/{machine}"
    pr_body = (
        f"User **{user}** requested `{operation}` on:\n"
        f"- Provider: {provider}\n"
        f"- Environment: {environment}\n"
        f"- Project: {project}\n"
        f"- Machine: {machine}\n"
        "\nPlease review and merge."
    )
    subprocess.run([
        "gh", "pr", "create",
        "--title", pr_title,
        "--body", pr_body,
        "--head", branch_name,
        "--base", "main",
        "--fill"
    ], check=False)

    subprocess.run(["git", "checkout", "main"], check=True)
    return RedirectResponse(url="/", status_code=303)

