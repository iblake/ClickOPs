output "ADB-wallet-content" {
  value     = module.oci-adb.adb_database.adb_wallet_content
  sensitive = true
}

output "deployed_adbs" {
  value = {
    for adb_key, adb in module.adb : adb_key => {
      ocid          = adb.autonomous_database_id
      display_name  = adb.display_name
      compartment   = adb.compartment_ocid
      workload      = adb.db_workload
      free_tier     = adb.is_free_tier
      db_version    = adb.db_version
      cpu_cores     = adb.cpu_core_count
      storage_tbs   = adb.data_storage_size_in_tbs
      license_model = adb.license_model
      # Puedes añadir más campos si lo necesitas
    }
  }
}
