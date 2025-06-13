function clickOpsApp() {
  return {
    mode: 'provision',
    providers: [], environments: [], projects: [],
    provider: '', environment: '', project: '',
    machine: '', adbs: [], selectedAdb: null,
    operation: '', crq: '',
    showModal: false,
    ops: {
      provision: [{ value: 'OPS103_provision_adb', label: 'Provision ADB Free Tier' }],
      change: [
        { value: 'OPS105_ADB_START', label: 'Start ADB' },
        { value: 'OPS106_ADB_STOP', label: 'Stop ADB' }
      ]
    },
    async fetchProviders() {
      this.providers = await (await fetch('/api/providers')).json();
    },
    async onProviderChange() {
      this.environment = this.project = this.machine = '';
      this.environments = this.projects = this.adbs = [];
      this.selectedAdb = null;
      if (!this.provider) return;
      this.environments = await (await fetch(`/api/environments/${this.provider}`)).json();
    },
    async onEnvironmentChange() {
      this.project = this.machine = '';
      this.projects = this.adbs = [];
      this.selectedAdb = null;
      if (!this.provider || !this.environment) return;
      this.projects = await (await fetch(`/api/projects/${this.provider}/${this.environment}`)).json();
    },
    async onProjectChange() {
      this.machine = '';
      this.adbs = [];
      this.selectedAdb = null;
      if (!this.provider || !this.environment || !this.project) return;
      if (this.mode === 'change') await this.fetchDeployedAdbs();
    },
    async fetchDeployedAdbs() {
      try {
        let url = `/api/deployed_adbs/${this.provider}/${this.environment}/${this.project}`;
        let res = await fetch(url);
        if (!res.ok) throw new Error('No deployed ADBs');
        let dbs = await res.json();
        // Convert dict to array with id
        this.adbs = Object.entries(dbs).map(([id, adb]) => ({
          ...adb, id
        }));
      } catch {
        this.adbs = [];
      }
    },
    onMachineChange() {
      this.selectedAdb = this.adbs.find(adb => adb.id === this.machine) || null;
    },
    setMode(newMode) {
      this.mode = newMode;
      this.operation = '';
      document.getElementById("docsContent").value = '';
      this.machine = '';
      this.adbs = [];
      this.selectedAdb = null;
      if (newMode === 'change' && this.provider && this.environment && this.project) {
        this.fetchDeployedAdbs();
      }
    },
    async loadDocs() {
      const el = document.getElementById("docsContent");
      if (!this.operation) { el.value = ''; return; }
      const res = await fetch(`/api/docs/${this.operation}`);
      const data = await res.json();
      el.value = data.content || '';
    },
    openConfirmModal() {
      // Aquí puedes implementar la lógica del modal si quieres.
      alert('Confirm modal (to be implemented)');
    },
    init() { this.fetchProviders(); }
  }
}
document.addEventListener("alpine:init", () => { Alpine.data("clickOpsApp", clickOpsApp); });

