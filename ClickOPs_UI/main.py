import subprocess
import os
import shutil
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import yaml

from ClickOPs_UI.auth import authenticate_user, create_session, get_current_user, logout_user

app = FastAPI()

app.mount("/static", StaticFiles(directory="ClickOPs_UI/templates/static"), name="static")
templates = Jinja2Templates(directory="ClickOPs_UI/templates")

REPO_ROOT    = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog"

def load_adbs_json(path: Path) -> dict:
    if not path.exists():
        return {"adbs": []}
    with open(path, "r") as f:
        return json.load(f)

def save_adbs_json(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

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

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

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

# NUEVO: Endpoint para listar ADBs centralizadas desde JSON
@app.get("/api/adbs/{provider}/{environment}/{project}")
def api_adbs(provider: str, environment: str, project: str):
    adb_json_path = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/adb/adb_resources.json"
    data = load_adbs_json(adb_json_path)
    return JSONResponse([adb["name"] for adb in data["adbs"]])

@app.get("/api/docs/{operation}")
def read_docs(operation: str):
    doc_path = REPO_ROOT / f"catalog/{operation}/docs.md"
    if doc_path.exists():
        return JSONResponse({"content": doc_path.read_text()})
    return JSONResponse({"content": "No documentation found for this operation."})

@app.post("/launch")
async def launch(
    request: Request,
    provider: str = Form(...),
    environment: str = Form(...),
    project: str = Form(...),
    machine: str | None = Form(None),
    operation: str = Form(...),
    crq: str = Form(...),
    tf_compartment: str | None = Form(None),
    tf_db_name: str | None = Form(None),
    tf_admin_password: str | None = Form(None),
    tf_db_workload: str | None = Form(None),
    ansible_extra_vars: str | None = Form(None),
    ansible_limit: str | None = Form(None)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Provision ADB usando JSON centralizado
    if operation == "OPS103_provision_adb":
        if not (tf_compartment and tf_db_name and tf_admin_password and tf_db_workload):
            return JSONResponse({"error": "Faltan variables Terraform para ADB"}, status_code=400)
        adb_json_path = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/adb/adb_resources.json"
        adb_json_path.parent.mkdir(parents=True, exist_ok=True)
        data = load_adbs_json(adb_json_path)
        new_adb = {
            "name": tf_db_name,
            "compartment_id": tf_compartment,
            "cpu_core_count": 1,
            "data_storage_size_in_tbs": 1,
            "admin_password": tf_admin_password,
            "db_name": tf_db_name,
            "db_workload": tf_db_workload,
            "is_free_tier": True,
            "display_name": tf_db_name,
            "license_model": "LICENSE_INCLUDED",
            "tags": {}
        }
        data["adbs"] = [adb for adb in data["adbs"] if adb["name"] != tf_db_name]
        data["adbs"].append(new_adb)
        save_adbs_json(adb_json_path, data)

        branch_name = f"crq-{crq}-provision-{tf_db_name}"
        os.chdir(str(REPO_ROOT))
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "pull"], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        rel_path = adb_json_path.relative_to(REPO_ROOT)
        subprocess.run(["git", "add", str(rel_path)], check=True)
        commit_msg = f"{crq}: Update ADB JSON with {tf_db_name} on {provider}/{environment}/{project}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

        pr_title = f"{crq} - Add or Update ADB {tf_db_name}"
        pr_body = (
            f"User **{user}** requested provisioning or update of ADB **{tf_db_name}** in:\n"
            f"- Provider: {provider}\n"
            f"- Environment: {environment}\n"
            f"- Project: {project}\n"
            f"- Compartment OCID: {tf_compartment}\n\n"
            "This PR updates the central adb_resources.json. Please review and merge to apply changes via Terraform."
        )
        subprocess.run([
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--head", branch_name,
            "--base", "main",
            "--fill"
        ], check=False)
        return RedirectResponse(url="/", status_code=303)

    # START/STOP ADB usando JSON centralizado
    if operation in ("OPS105_ADB_START", "OPS106_ADB_STOP"):
        if not machine:
            return JSONResponse({"error": "ADB name is required to start/stop."}, status_code=400)
        if not ansible_extra_vars:
            return JSONResponse({"error": "Faltan variables Ansible"}, status_code=400)

        adb_dir = REPO_ROOT / f"oe_01/{provider}/{environment}/{project}/adb"
        adb_dir.mkdir(parents=True, exist_ok=True)
        extra_vars_file = adb_dir / f"{machine}_extra_vars.yml"
        try:
            extra_dict = yaml.safe_load(ansible_extra_vars)
            with open(extra_vars_file, "w") as f:
                yaml.dump(extra_dict, f)
        except Exception:
            pass

        import_line = f"- import_playbook: catalog/OPS105_ADB_START_STOP/{'adb_start.yml' if operation == 'OPS105_ADB_START' else 'adb_stop.yml'}\n"

        branch_name = f"crq-{crq}-{operation}-{machine}"
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
        subprocess.run(["git", "add", str(extra_vars_file)], check=True)

        commit_msg = f"{crq}: {operation} on {provider}/{environment}/{project}/{machine}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

        pr_title = f"{crq} - {operation} on {project}/{machine}"
        pr_body = (
            f"User **{user}** requested `{operation}` on:\n"
            f"- Provider: {provider}\n"
            f"- Environment: {environment}\n"
            f"- Project: {project}\n"
            f"- ADB Name: {machine}\n"
            f"- Extra Vars: `{ansible_extra_vars}`\n\n"
            "Por favor revisar y hacer merge para ejecutar el Ansible Playbook.\n"
            "**El playbook buscará los datos de la ADB en adb_resources.json**."
        )
        subprocess.run([
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--head", branch_name,
            "--base", "main",
            "--fill"
        ], check=False)
        return RedirectResponse(url="/", status_code=303)

    return RedirectResponse(url="/", status_code=303)
