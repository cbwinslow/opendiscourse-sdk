terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
      version = ">= 1.36.2"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

resource "hcloud_server" "main" {
  name        = "cloudcurio"
  image       = "ubuntu-22.04"
  server_type = "cx21"
  location    = "hel1"
  ssh_keys    = [var.ssh_key]
}
