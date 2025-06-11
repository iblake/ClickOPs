variable "compartment_ocid" {
  description = "OCID del compartment donde se crean las ADB"
  type        = string
}

variable "region" {
  description = "Región de OCI"
  type        = string
}

variable "inputs_json_path" {
  description = "Ruta al JSON de entrada"
  type        = string
}

variable "oci_profile" {
  description = "Profile name de ~/.oci/config"
  type        = string
  default     = "DEFAULT"
}


