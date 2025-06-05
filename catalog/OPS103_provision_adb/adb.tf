module "oci-adb" {
  source                    = "github.com/oracle-devrel/terraform-oci-arch-adb"
  adb_database_db_name      = var.adb_database_db_name
  adb_database_display_name = var.adb_database_display_name
  adb_database_db_version   = var.adb_database_db_version
  adb_password              = local.adb_password_decoded
  adb_database_db_workload  = var.adb_database_db_workload
  compartment_ocid          = var.compartment_ocid
  use_existing_vcn          = false
  adb_private_endpoint      = false
  whitelisted_ips           = [""]
}