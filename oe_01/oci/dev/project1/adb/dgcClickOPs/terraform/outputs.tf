output "ADB-wallet-content" {
  value     = module.oci-adb.adb_database.adb_wallet_content
  sensitive = true
}
