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

from ClickOPs_UI.auth import authenticate_user, create_session, get_current_user, logout_user

app = FastAPI()

# Montamos archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="ClickOPs_UI/templates/static"), name="static")
templates = Jinja2Templates(directory="ClickOPs_UI/templates")

# Rutas dentro del repositorio
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

# --- ENDPOINTS PARA EL FORMULARIO ---

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
    # En modo 'change' para ADB, listamos subdirectorios de adb/ dentro del proyecto
    base = REPO_ROOT / f"oe_01/{provider}/{env}/{project}/adb"
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
async def launch(
    request: Request,
    provider: str = Form(...),
    environment: str = Form(...),
    project: str = Form(...),
    machine: str | None = Form(None),
    operation: str = Form(...),
    crq: str = Form(...),
    # Variables Terraform para Autonomous DB Free Tier
    tf_compartment: str | None = Form(None),
    tf_db_name: str | None = Form(None),
    tf_admin_password: str | None = Form(None),
    tf_db_workload: str | None = Form(None),
    # Variables Ansible
    ansible_extra_vars: str | None = Form(None),
    ansible_limit: str | None = Form(None)
):
    """
    1) Si 'operation' contiene 'provision', copiar el módulo Terraform al inventario,
       crear terraform.tfvars.json con las variables de la Autonomous Database Free Tier,
       agregar run_terraform.txt y hacer git add/commit/push para disparar el workflow.
    2) Si 'operation' es 'OPS105_ADB_START' o 'OPS106_ADB_STOP', actualizar master.yml con el import_playbook
       correspondiente y crear un PR en GitHub (GitOps para Ansible).
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # ––– CASO PROVISION ADB FREE TIER (Terraform + ClickOps) –––
    if "provision" in operation:
        # a) Crear carpeta de inventario para la ADB
        inv_path = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/adb/{tf_db_name}"
        inv_path.mkdir(parents=True, exist_ok=True)

        # b) Copiar módulo Terraform desde el catálogo
        src_tf_folder  = CATALOG_PATH / operation
        dest_tf_folder = inv_path / "terraform"
        shutil.copytree(src_tf_folder, dest_tf_folder, dirs_exist_ok=True)

        # c) Generar terraform.tfvars.json con variables de ADB Free Tier
        tfvars = {
            "compartment_id":         tf_compartment or "ocid1.compartment.oc1..exampleuniqueID",
            "db_name":                tf_db_name or f"{tf_db_name}",
            "cpu_core_count":         1,
            "data_storage_size_in_tbs": 1,
            "admin_password":         tf_admin_password or "DefaultPassw0rd!",
            "db_workload":            tf_db_workload or "OLTP",
            "is_free_tier":           True,
            "display_name":           tf_db_name or f"{project}-freeADB",
            "license_model":          "LICENSE_INCLUDED"
        }
        with open(dest_tf_folder / "terraform.tfvars.json", "w") as f:
            yaml.dump(tfvars, f)

        # d) Crear marcador run_terraform.txt
        marker = inv_path / "run_terraform.txt"
        marker.write_text("run-do-terraform-apply")

        # e) Git add + commit + push para disparar automáticamente el workflow
        os.chdir(str(REPO_ROOT))
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "add", str(inv_path.relative_to(REPO_ROOT))], check=True)
        commit_msg = f"ci: trigger ADB provisioning for {tf_db_name}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)

        # f) Redirigir al usuario de vuelta
        return RedirectResponse(url="/", status_code=303)

    # ––– CASO START / STOP ADB (Ansible – GitOps) –––
    if operation == "OPS105_ADB_START":
        playbook_file = "adb_start.yml"
        folder_name = "OPS105_ADB_START_STOP"
    elif operation == "OPS106_ADB_STOP":
        playbook_file = "adb_stop.yml"
        folder_name = "OPS106_ADB_START_STOP"
    else:
        playbook_file = ""
        folder_name = ""

    # Guardar valores de ansible_extra_vars en extra_vars.yml, si se proporcionaron
    if ansible_extra_vars and folder_name:
        extra_dict = {}
        try:
            extra_dict = yaml.safe_load(ansible_extra_vars)  # JSON o YAML válido
        except Exception:
            pass

        # La carpeta de inventario en este caso es: oe_01/{provider}/{environment}/{project}/adb/{machine}
        inv_path_ansible = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/adb/{machine}"
        inv_path_ansible.mkdir(parents=True, exist_ok=True)
        with open(inv_path_ansible / "extra_vars.yml", "w") as f:
            yaml.dump(extra_dict, f)

    # Construir la línea de import_playbook que se añadirá a master.yml
    if folder_name:
        import_line = f"- import_playbook: catalog/{folder_name}/{playbook_file}\n"
    else:
        import_line = ""

    if import_line:
        # Crear rama y hacer commit + push
        branch_name = f"crq-{crq}"
        os.chdir(str(REPO_ROOT))
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "pull"], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        MASTER_FILE = REPO_ROOT / "master.yml"
        if not MASTER_FILE.exists():
            MASTER_FILE.write_text(import_line)
        else:
            content_lines = MASTER_FILE.read_text().splitlines(keepends=True)
            if import_line not in content_lines:
                with open(MASTER_FILE, "a") as f:
                    f.write(import_line)

        subprocess.run(["git", "add", "master.yml"], check=True)
        commit_msg = f"{crq}: Launch {operation} on {provider}/{environment}/{project}/{machine}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        # <-- Aquí estaba la comilla extra, la hemos quitado:
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

        # Crear Pull Request en GitHub con gh
        pr_title = f"{crq} - {operation} on {project}/{machine}"
        pr_body = (
            f"User **{user}** requested `{operation}` on:\n"
            f"- Provider: {provider}\n"
            f"- Environment: {environment}\n"
            f"- Project: {project}\n"
            f"- ADB Identifier: {machine}\n"
            f"- Extra Vars: `{ansible_extra_vars or 'N/A'}`\n"
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
