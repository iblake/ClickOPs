locals {
  adb_resources = jsondecode(file(var.inputs_json_path))
}

module "adb" {
  source           = "github.com/oracle-devrel/terraform-oci-arch-adb.git?ref=main"
  compartment_ocid = var.compartment_ocid
  region           = var.region
  adb_databases    = local.adb_resources.adbs
}




