variable "region" {
  description = "OCI region to use (e.g., eu-frankfurt-1)"
  type        = string
}

variable "inputs_json_path" {
  description = "Path to the input JSON describing the ADBs"
  type        = string
}
