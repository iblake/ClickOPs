variable "compartment_ocid" {
  description = "OCID of the compartment where ADB will be deployed"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
}

variable "inputs_json_path" {
  description = "Path to the input JSON describing the ADBs"
  type        = string
}


