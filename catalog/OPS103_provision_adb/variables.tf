variable "compartment_ocid" {}
variable "region" {}


variable "adb_password" {
  description = "ADB password (used only if not using Vault)"
  type        = string
  sensitive   = true
  default     = null
}

variable "adb_database_db_version" {
  description = "Autonomous Database version"
  type        = string
  default     = "19.0.0"
}

variable "adb_database_db_name" {
  description = "Autonomous Database name"
  type        = string
  default     = "dgcadb"
}

variable "adb_database_display_name" {
  description = "Autonomous Database display name"
  type        = string
  default     = "dgcadb"
}

variable "adb_database_db_workload" {
  description = "Autonomous Database workload type"
  type        = string
  default     = "OLTP" # Options: OLTP, DW, AJD
}

variable "inputs_json_path" {
  description = "Path to the input JSON describing the ADBs"
  type        = string
}
