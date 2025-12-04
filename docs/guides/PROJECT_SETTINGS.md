# Project Settings & Credentials

## Server & Infrastructure
- Primary database: Oracle Cloud Free Tier PostgreSQL (provisioned via Terraform)
- Cloudflare tunnel hostname: see `.env` (`CLOUDFLARE_TUNNEL_HOSTNAME`)
- All environment variables: `.env` (not for secrets)
- Sensitive secrets: Use Ansible Vault or Bitwarden, not in git
- Terraform variables: `terraform/oci-cloudflare/terraform.tfvars` (never commit secrets)
- Ansible inventory: `ansible/hosts.ini`

## Workflow
- Use `.env` for non-secret config
- Use Markdown files for project notes and documentation
- Use Ansible for provisioning and deployment
- Use Terraform for infrastructure provisioning

## File Locations
- `.env` — project environment variables
- `ansible/` — Ansible playbooks, roles, inventory
- `terraform/` — Terraform scripts and variables
- `PROJECT_SETTINGS.md` — this file, for reference
