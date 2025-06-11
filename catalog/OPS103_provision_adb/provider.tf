terraform {
  backend "oci" {}
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

# Permite definir el perfil (profile) a usar en ~/.oci/config (útil para desarrollo local y runners)
variable "oci_profile" {
  description = "Profile name to use from ~/.oci/config"
  type        = string
  default     = "DEFAULT"
}

provider "oci" {
  config_file_profile = var.oci_profile
}
