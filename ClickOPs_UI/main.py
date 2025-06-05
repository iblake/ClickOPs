from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import yaml

app = FastAPI(title="ClickOps GitOps UI")

# Static + template config
BASE_PATH = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_PATH / "ClickOPs_UI/templates/static"), name="static")
templates = Jinja2Templates(directory=str(BASE_PATH / "ClickOPs_UI/templates"))

# Paths
REPO_PATH = BASE_PATH
CATALOG_PATH = REPO_PATH / "catalog"
MASTER_FILE = REPO_PATH / "master.yml"

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "operations": [
            {"code": "DEP001_create_vm", "label": "DEP001 - Create VM"},
            {"code": "OPS101_start_vm", "label": "OPS101 - Start VM"},
            {"code": "OPS102_stop_vm", "label": "OPS102 - Stop VM"}
        ],
        "providers": ["oci", "aws", "azure"],
        "environments": ["dev", "prod", "staging"]
    })

@app.post("/launch")
def launch_operation(
    request: Request,
    provider: str = Form(...),
    env: str = Form(...),
    project: str = Form(...),
    machine: str = Form(...),
    operation: str = Form(...)
):
    inv_path = REPO_PATH / "oe_01" / provider / env / project / machine
    inv_path.mkdir(parents=True, exist_ok=True)

    if operation.startswith("DEP001"):
        tf_path = CATALOG_PATH / operation / "main.tf"
        (inv_path / "main.tf").write_text(tf_path.read_text())

        tfvars = {
            "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
            "subnet_id": "ocid1.subnet.oc1..exampleuniqueID",
            "image_id": "ocid1.image.oc1..exampleuniqueID",
            "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD...",
            "vm_name": machine
        }
        with open(inv_path / "tfvars.json", "w") as f:
            yaml.dump(tfvars, f)

        update_master_file({
            "terraform": {
                "path": str(inv_path.relative_to(REPO_PATH)),
                "action": "apply"
            }
        })

    else:
        playbook = "start_vm.yml" if "start" in operation else "stop_vm.yml"
        update_master_file({
            "import_playbook": f"catalog/{operation}/{playbook}"
        })

    return RedirectResponse(url="/", status_code=303)

def update_master_file(entry):
    if MASTER_FILE.exists():
        data = yaml.safe_load(MASTER_FILE.read_text()) or []
    else:
        data = []
    data.append(entry)
    with open(MASTER_FILE, "w") as f:
        yaml.dump(data, f)
