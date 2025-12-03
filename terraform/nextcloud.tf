resource "hcloud_server" "nextcloud" {
  name        = "nextcloud-server"
  image       = "ubuntu-22.04"
  server_type = "cx21"
  location    = "hel1"
  ssh_keys    = [var.ssh_key]
  # Optionally add user_data for Docker/Nextcloud install
}

output "nextcloud_ip" {
  value = hcloud_server.nextcloud.ipv4_address
}

output "nextcloud_caddy_ports" {
  value = [80, 443, 8080, 8443]
}

output "nextcloud_redis_port" {
  value = 6379
}

output "nextcloud_smtp_vars" {
  value = {
    smtp_host     = var.nextcloud_smtp_host
    smtp_port     = var.nextcloud_smtp_port
    smtp_user     = var.nextcloud_smtp_user
    smtp_password = var.nextcloud_smtp_password
  }
}
