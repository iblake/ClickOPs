# Configuración del proveedor de OCI
provider "oci" {
  # Si tus credenciales están configuradas en el archivo ~/.oci/config,
  # no necesitas especificar nada aquí. Si no, puedes pasar
  # region, tenancy_ocid, user_ocid, private_key_path, fingerprint
  # o usar variables de entorno.
}

# Generar una contraseña aleatoria para el usuario ADMIN
resource "random_string" "admin_password" {
  length  = 16
  special = true
  numeric = true
  lower   = true
  upper   = true
}

# Definición de la Autonomous Database
resource "oci_database_autonomous_database" "my_autonomous_database" {
  # (Requerido) OCID del compartimento donde se creará la ADB
  compartment_id = var.compartment_ocid

  # (Requerido) Nombre de visualización para la ADB
  display_name = var.adb_display_name

  # (Requerido) Nombre de la base de datos (DB_NAME)
  db_name = var.adb_db_name

  # (Requerido) Contraseña para el usuario ADMIN
  admin_password = random_string.admin_password.result

  # (Requerido) Cargas de trabajo soportadas: OLTP (Transaction Processing), DW (Data Warehouse), AJD (JSON Database), APEX (APEX Application Development)
  db_workload = var.adb_db_workload

  # (Requerido) Número de OCPUs (vCPU para ECPU)
  cpu_core_count = var.adb_cpu_core_count

  # (Requerido) Tamaño del almacenamiento en TB
  data_storage_size_in_tbs = var.adb_data_storage_size_in_tbs

  # (Opcional) Modelo de computación. Puede ser "OCPU" o "ECPU".
  # compute_model = "OCPU" # Por defecto es OCPU si no se especifica

  # (Opcional) Licencia de la base de datos. Puede ser "LICENSE_INCLUDED" o "BRING_YOUR_OWN_LICENSE"
  license_model = var.adb_license_model

  # (Opcional) Versión de la base de datos (ej. "19c", "21c")
  db_version = var.adb_db_version

  # (Opcional) Habilitar o deshabilitar el autoescalado de OCPUs
  is_auto_scaling_enabled = var.adb_is_auto_scaling_enabled

  # (Opcional) Habilitar o deshabilitar el autoescalado del almacenamiento
  # is_storage_auto_scaling_enabled = true

  # (Opcional) Configurar la lista de acceso IP para bases de datos públicas
  # Si vas a usar un punto final privado, esto no es necesario.
  # whitelisted_ips = [
  #   "0.0.0.0/0" # ¡NO RECOMENDADO PARA PRODUCCIÓN!
  # ]

  # (Opcional) Para un punto final privado (Private Endpoint)
  # Requiere una VCN y una Subnet existente
  # subnet_id               = var.adb_subnet_id
  # private_endpoint_label  = "my_private_adb_endpoint"
  # nsg_ids                 = [oci_core_network_security_group.my_nsg.id] # Opcional: para controlar el tráfico a la ADB
}

# Salida de la contraseña generada (¡manejar con cuidado!)
output "admin_password" {
  value     = random_string.admin_password.result
  sensitive = true # Marca la salida como sensible para que no se muestre en el log
}

# Salida del OCID de la Autonomous Database
output "autonomous_database_ocid" {
  value = oci_database_autonomous_database.my_autonomous_database.id
}

# Salida de la URL de la consola de servicio
output "service_console_url" {
  value = oci_database_autonomous_database.my_autonomous_database.service_console_url
}