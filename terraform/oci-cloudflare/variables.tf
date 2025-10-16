variable "oci_region" {
  type        = string
  description = "OCI region where resources will be created (e.g., us-ashburn-1)."
}
variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID for the account."
}
variable "user_ocid" {
  type        = string
  description = "OCI user OCID for API authentication."
}
variable "api_fingerprint" {
  type        = string
  description = "Fingerprint of the OCI API key."
}
variable "api_private_key_path" {
  type        = string
  description = "Path to the OCI API private key file."
  sensitive   = true
}
variable "compartment_ocid" {
  type        = string
  description = "OCI compartment OCID where resources will be created."
}
variable "subnet_ocid" {
  type        = string
  description = "OCI subnet OCID for resource networking."
}
variable "ssh_public_key" {
  type        = string
  description = "SSH public key for accessing compute instances."
}
variable "db_display_name" {
  type        = string
  description = "Display name for the database instance."
}
variable "db_hostname" {
  type        = string
  description = "Hostname for the database instance."
}

variable "cloudflare_account_id" {
  type        = string
  description = "Cloudflare account ID for API operations."
}
variable "cloudflare_api_token" {
  type        = string
  description = "API token for authenticating with Cloudflare."
  sensitive   = true
}
variable "tunnel_name" {
  type        = string
  description = "Name of the Cloudflare tunnel."
}
variable "tunnel_secret" {
  type        = string
  description = "Secret for the Cloudflare tunnel."
  sensitive   = true
}
variable "r2_bucket_name" {
  type        = string
  description = "Name of the Cloudflare R2 bucket."
}
