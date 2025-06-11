locals {
  adb_resources = jsondecode(file(var.inputs_json_path))
}

module "adb" {
  source  = "github.com/oracle-devrel/terraform-oci-arch-adb//modules/adb"
  # version = "v2.0.0"      # Solo puedes fijar una versión si usas el registry público, pero aquí puedes hacer checkout a una rama/commit.

  # Cada ADB definido en el JSON se despliega como un recurso
  for_each = { for adb in local.adb_resources.adbs : adb.name => adb }

  compartment_ocid           = each.value.compartment_ocid
  region                     = var.region
  adb_password               = each.value.adb_password
  db_name                    = each.value.db_name
  display_name               = each.value.display_name
  db_workload                = each.value.db_workload
  db_version                 = each.value.db_version
  cpu_core_count             = each.value.cpu_core_count
  data_storage_size_in_tbs   = each.value.data_storage_size_in_tbs
  is_free_tier               = each.value.is_free_tier
  license_model              = each.value.license_model

  # Puedes añadir aquí más variables opcionales según tu módulo y necesidades.
}


