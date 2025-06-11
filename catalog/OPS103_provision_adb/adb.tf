locals {
  adbs = jsondecode(file(var.inputs_json_path))["adbs"]
}

module "adb" {
  for_each = { for adb in local.adbs : adb.name => adb }
  source   = "github.com/oracle-devrel/terraform-oci-arch-adb"

  compartment_id           = each.value.compartment_id
  cpu_core_count           = each.value.cpu_core_count
  data_storage_size_in_tbs = each.value.data_storage_size_in_tbs
  admin_password           = each.value.admin_password
  db_name                  = each.value.db_name
  db_workload              = each.value.db_workload
  is_free_tier             = each.value.is_free_tier
  display_name             = each.value.display_name
  license_model            = each.value.license_model
  # Añade aquí cualquier otro parámetro requerido por el módulo original.
}