locals {
  adbs = jsondecode(file(var.inputs_json_path))["adbs"]
}

module "adb" {
  for_each = { for adb in local.adbs : adb.name => adb }
  source  = "oracle-devrel/oci-arch-adb/oci"
  # version = "1.0.0"  # pon la versión que uses

  compartment_ocid             = each.value.compartment_ocid  # cambia a ..._ocid
  adb_display_name             = each.value.display_name
  adb_db_name                  = each.value.db_name
  adb_workload                 = each.value.db_workload
  adb_db_version               = each.value.db_version        # debes añadirlo al JSON
  adb_password                 = each.value.adb_password      # debes añadirlo al JSON
  adb_cpu_core_count           = each.value.cpu_core_count
  adb_data_storage_size_in_tbs = each.value.data_storage_size_in_tbs
  adb_license_model            = each.value.license_model
  adb_free_tier                = each.value.is_free_tier
}
