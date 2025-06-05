# main.tf for DEP001_create_vm
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


variable "compartment_id" {
  description = "OCID of the compartment where the VM will be created"
  type        = string
}

variable "availability_domain" {
  description = "Availability domain, e.g., Uocm:EU-FRANKFURT-1-AD-1"
  type        = string
}

variable "subnet_id" {
  description = "OCID of the subnet for the VNIC"
  type        = string
}

variable "image_id" {
  description = "OCID of the image (oracle linux, ubuntu, etc.)"
  type        = string
}

variable "shape" {
  description = "Instance shape, e.g. VM.Standard.E2.1.Micro"
  type        = string
}

variable "ssh_public_key" {
  description = "Public SSH key for the VM"
  type        = string
}

variable "display_name" {
  description = "Name to assign to the new VM"
  type        = string
}

variable "region" {
  description = "Region, e.g. eu-frankfurt-1"
  type        = string
}

variable "profile" {
  description = "OCI CLI profile, e.g. DEFAULT"
  type        = string
}

variable "output_vm_vars_path" {
  description = "Path (relativo a workspace) donde escribir vm_vars.yml"
  type        = string
}

# Crea la instancia en OCI
resource "oci_core_instance" "vm" {
  provider          = oci.default
  compartment_id    = var.compartment_id
  availability_domain = var.availability_domain
  shape             = var.shape
  display_name      = var.display_name

  create_vnic_details {
    subnet_id       = var.subnet_id
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = var.image_id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }

  # Espera hasta que esté RUNNING
  wait_for_state = "RUNNING"
  # timeouts opcionales
  timeouts {
    create = "10m"
  }
}

# Escribir el instance_id en YAML dentro de la carpeta de inventario:
# usa un "local_file" para generar el archivo vm_vars.yml
resource "local_file" "vm_vars" {
  content  = templatefile("${path.module}/vm_vars.tmpl", {
    instance_id = oci_core_instance.vm.id
    region      = var.region
    profile     = var.profile
  })
  filename = var.output_vm_vars_path
}
