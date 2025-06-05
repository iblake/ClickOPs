variable "adb_password_secret_ocid" {
  description = "OCID of the secret in OCI Vault for the ADB password"
  type        = string
}

data "oci_secrets_secretbundle" "adb_password" {
  secret_id = var.adb_password_secret_ocid
}

locals {
  adb_password_decoded = base64decode(data.oci_secrets_secretbundle.adb_password.secret_bundle_content[0].content)
}
