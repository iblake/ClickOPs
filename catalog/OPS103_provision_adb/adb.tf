locals {
  adb_resources = jsondecode(file(var.inputs_json_path))
}

module "adb" {
  for_each = { for adb in local.adb_resources.adbs : adb.display_name => adb }

  source                   = "github.com/oracle-devrel/terraform-oci-arch-adb.git?ref=main"
  compartment_ocid         = each.value.compartment_ocid
  display_name             = each.value.display_name
  admin_password           = each.value.admin_password
  db_workload              = each.value.db_workload
  is_free_tier             = each.value.is_free_tier
  cpu_core_count           = each.value.cpu_core_count
  data_storage_size_in_tbs = each.value.data_storage_size_in_tbs
  license_model            = try(each.value.license_model, null)
  db_version               = try(each.value.db_version, null)
}






