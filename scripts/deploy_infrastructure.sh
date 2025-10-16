#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TERRAFORM_DIR="$SCRIPT_DIR/../terraform/oci-cloudflare"

if [ ! -d "$TERRAFORM_DIR" ]; then
  echo "Terraform directory not found: $TERRAFORM_DIR" >&2
  exit 1
fi

cd "$TERRAFORM_DIR"
terraform init
terraform apply "$@"
