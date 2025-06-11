variable "compartment_ocid" {
  description = "OCID of the compartment where ADBs will be provisioned"
  type        = string
}

variable "region" {
  description = "Region where ADBs will be provisioned"
  type        = string
}

variable "inputs_json_path" {
  description = "Path to the input JSON describing the ADBs"
  type        = string
}

