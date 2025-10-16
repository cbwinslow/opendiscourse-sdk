terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }
  }
}

provider "oci" {
  region           = var.oci_region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.api_fingerprint
  private_key_path = var.api_private_key_path
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# Oracle Cloud free-tier PostgreSQL database
resource "oci_database_postgresql_db_system" "pg" {
  compartment_id      = var.compartment_ocid
  display_name        = var.db_display_name
  database_edition    = "STANDARD"
  db_version          = "15"
  storage_size_in_gbs = 10
  ocpu_count          = 1
  subnet_id           = var.subnet_ocid
  ssh_public_keys     = [var.ssh_public_key]
}

# Cloudflare tunnel to securely expose the database
resource "cloudflare_tunnel" "db" {
  account_id = var.cloudflare_account_id
  name       = var.tunnel_name
  secret     = var.tunnel_secret
}

resource "cloudflare_tunnel_config" "db" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_tunnel.db.id

  config_json = jsonencode({
    ingress = [
      {
        hostname = var.db_hostname
        service  = "tcp://${oci_database_postgresql_db_system.pg.private_ip}:${var.postgres_port}"
      },
      {
        service = "http_status:404"
      }
    ]
  })
}

# Example R2 bucket for AutoRAG assets
resource "cloudflare_r2_bucket" "autorag" {
  account_id = var.cloudflare_account_id
  name       = var.r2_bucket_name
}

output "postgres_private_ip" {
  value = oci_database_postgresql_db_system.pg.private_ip
}

output "cloudflare_tunnel_id" {
  value = cloudflare_tunnel.db.id
}
