terraform {
  backend "oci" {}
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

variable "oci_profile" {
  description = "Profile name to use from ~/.oci/config"
  type        = string
  default     = "DEFAULT"
}

provider "oci" {
  config_file_profile = var.oci_profile
}

