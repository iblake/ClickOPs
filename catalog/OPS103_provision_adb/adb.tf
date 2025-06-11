locals {
  adb_resources = jsondecode(file(var.inputs_json_path))
}


module "adb" {
  source           = "github.com/oracle-devrel/terraform-oci-arch-adb.git?ref=main"
  compartment_ocid = var.compartment_ocid
  region           = var.region

  adb_databases = [
    for adb in local.adb_resources.adbs : {
      display_name               = adb.display_name
      db_name                    = adb.db_name
      admin_password             = adb.admin_password
      db_workload                = adb.db_workload
      is_free_tier               = adb.is_free_tier
      cpu_core_count             = adb.cpu_core_count
      data_storage_size_in_tbs   = adb.data_storage_size_in_tbs
      license_model              = adb.license_model
      db_version                 = try(adb.db_version, null)
      # Añade aquí otros campos del módulo si los necesitas y existen en el JSON
    }
  ]
}




