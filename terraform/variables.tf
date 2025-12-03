variable "nextcloud_smtp_host" {
  description = "SMTP host for Nextcloud"
  type        = string
}

variable "nextcloud_smtp_port" {
  description = "SMTP port for Nextcloud"
  type        = number
}

variable "nextcloud_smtp_user" {
  description = "SMTP username for Nextcloud"
  type        = string
}

variable "nextcloud_smtp_password" {
  description = "SMTP password for Nextcloud"
  type        = string
}
variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
}

variable "ssh_key" {
  description = "SSH public key for server access"
  type        = string
}

variable "nextcloud_admin_user" {
  description = "Nextcloud admin username"
  type        = string
}

variable "nextcloud_admin_password" {
  description = "Nextcloud admin password"
  type        = string
}
