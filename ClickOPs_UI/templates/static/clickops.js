function clickOpsApp() {
  return {
    mode: 'provision',
    provider: '', environment: '', project: '', machine: '', operation: '', crq: '',
    providers: [], environments: [], projects: [], machines: [],
    showModal: false,
    tf_vars: { compartment: '', db_name: '', admin_password: '', db_workload: '' },
    ansible_vars: { extra: '', limit: '' },
    ops: {
      provision: [{ value: 'OPS103_provision_adb', label: 'Provision ADB Free Tier' }],
      change: [{ value: 'OPS105_ADB_START', label: 'Start ADB' }, { value: 'OPS106_ADB_STOP', label: 'Stop ADB' }]
    },
    async fetchProviders() {
      this.providers = await (await fetch('/api/providers')).json();
    },
    async onProviderChange() {
      this.environment = this.project = this.machine = '';
      this.environments = this.projects = this.machines = [];
      if (!this.provider) return;
      this.environments = await (await fetch(`/api/environments/${this.provider}`)).json();
    },
    async onEnvironmentChange() {
      this.project = this.machine = '';
      this.projects = this.machines = [];
      if (!this.provider || !this.environment) return;
      this.projects = await (await fetch(`/api/projects/${this.provider}/${this.environment}`)).json();
    },
    async onProjectChange() {
      this.machine = '';
      this.machines = [];
      if (!this.provider || !this.environment || !this.project) return;
      if (this.mode === 'change') await this.fetchAdbsFromJson();
    },
    async fetchAdbsFromJson() {
      try { this.machines = await (await fetch(`/api/adbs/${this.provider}/${this.environment}/${this.project}`)).json(); }
      catch { this.machines = []; }
    },
    async loadDocs() {
      const el = document.getElementById("docsContent");
      if (!this.operation) { el.innerHTML = ''; return; }
      const res = await fetch(`/api/docs/${this.operation}`);
      const data = await res.json();
      el.innerHTML = marked.parse(data.content);
    },
    setMode(newMode) {
      this.mode = newMode;
      this.operation = '';
      document.getElementById("docsContent").innerHTML = '';
      this.tf_vars = { compartment: '', db_name: '', admin_password: '', db_workload: '' };
      this.ansible_vars = { extra: '', limit: '' };
      this.machine = ''; this.machines = [];
      if (newMode === 'change' && this.provider && this.environment && this.project) this.fetchAdbsFromJson();
    },
    resetForm() {
      this.provider = this.environment = this.project = this.machine = this.operation = this.crq = '';
      this.environments = this.projects = this.machines = [];
      this.tf_vars = { compartment: '', db_name: '', admin_password: '', db_workload: '' };
      this.ansible_vars = { extra: '', limit: '' };
      document.getElementById("docsContent").innerHTML = '';
    },
    openConfirmModal() {
      if (!this.provider || !this.environment || !this.project || !this.operation || !this.crq)
        return alert("Please fill out all required fields.");
      if (this.mode === 'provision' && Object.values(this.tf_vars).some(v => !v.trim()))
        return alert("Please complete all ADB variables before continuing.");
      if (this.mode === 'change') {
        if (!this.machine.trim())
          return alert("Please select an existing ADB to start or stop.");
        if (!this.ansible_vars.extra.trim())
          return alert("Please provide Extra Vars (compartment + adb_ocid).");
      }
      this.showModal = true;
    },
    async submitOperation() {
      this.showModal = false;
      if (this.mode === 'provision') this.machine = this.project;
      const formData = new FormData();
      formData.append("provider", this.provider);
      formData.append("environment", this.environment);
      formData.append("project", this.project);
      formData.append("machine", this.machine);
      formData.append("operation", this.operation);
      formData.append("crq", this.crq);
      if (this.mode === 'provision') {
        formData.append("tf_compartment", this.tf_vars.compartment);
        formData.append("tf_db_name", this.tf_vars.db_name);
        formData.append("tf_admin_password", this.tf_vars.admin_password);
        formData.append("tf_db_workload", this.tf_vars.db_workload);
      }
      if (this.mode === 'change') {
        formData.append("ansible_extra_vars", this.ansible_vars.extra);
        formData.append("ansible_limit", this.ansible_vars.limit);
      }
      const res = await fetch("/launch", { method: "POST", body: formData });
      if (res.ok) {
        alert("Operation submitted!");
        this.resetForm();
        this.fetchProviders();
      } else {
        alert("There was a problem launching the operation.");
      }
    },
    init() { this.fetchProviders(); }
  }
}
document.addEventListener("alpine:init", () => { Alpine.data("clickOpsApp", clickOpsApp); });
