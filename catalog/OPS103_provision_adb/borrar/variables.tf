variable "compartment_ocid" {
  description = "OCID del compartimento donde se creará la Autonomous Database."
  type        = string
}

variable "adb_display_name" {
  description = "El nombre de visualización para la Autonomous Database."
  type        = string
  default     = "MyADBDemo"
}

variable "adb_db_name" {
  description = "El nombre de la base de datos (DB_NAME) para la Autonomous Database."
  type        = string
  default     = "MYADBDEMO"
}

variable "adb_db_workload" {
  description = "El tipo de carga de trabajo de la base de datos (OLTP, DW, AJD, APEX)."
  type        = string
  default     = "DW" # O "OLTP"
}

variable "adb_cpu_core_count" {
  description = "Número de OCPUs para la Autonomous Database."
  type        = number
  default     = 1
}

variable "adb_data_storage_size_in_tbs" {
  description = "Tamaño del almacenamiento en TB para la Autonomous Database."
  type        = number
  default     = 1
}

variable "adb_license_model" {
  description = "Modelo de licencia para la Autonomous Database (LICENSE_INCLUDED o BRING_YOUR_OWN_LICENSE)."
  type        = string
  default     = "LICENSE_INCLUDED"
}

variable "adb_db_version" {
  description = "Versión de la base de datos (ej. 19c, 21c)."
  type        = string
  default     = "19c"
}

variable "adb_is_auto_scaling_enabled" {
  description = "Indica si el autoescalado de OCPUs está habilitado."
  type        = bool
  default     = true
}

# Si planeas usar un punto final privado, descomenta estas variables
# variable "adb_subnet_id" {
#   description = "OCID de la subred donde se creará el punto final privado de la Autonomous Database."
#   type        = string
# }