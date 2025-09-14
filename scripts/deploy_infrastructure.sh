#!/bin/bash
set -euo pipefail

# deploy_infrastructure.sh - Deploy OpenDiscourse infrastructure using Terraform
#
# USAGE:
#   ./scripts/deploy_infrastructure.sh [--auto-approve] [--help]
#
# DESCRIPTION:
#   This script safely deploys OpenDiscourse infrastructure to Hetzner Cloud
#   using Terraform. It runs 'terraform plan' first to show what changes will
#   be made, then prompts for confirmation before applying changes.
#
# OPTIONS:
#   --auto-approve    Skip interactive approval and apply changes automatically
#   --help           Show this help message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    sed -n '3,16p' "$0" | sed 's/^# \?//'
}

# Parse command line arguments
AUTO_APPROVE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if terraform directory exists
if [[ ! -d "$TERRAFORM_DIR" ]]; then
    print_error "Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

print_info "Starting infrastructure deployment..."
print_info "Working directory: $TERRAFORM_DIR"

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Initialize terraform if needed
if [[ ! -d ".terraform" ]]; then
    print_info "Initializing Terraform..."
    terraform init
fi

# Validate terraform configuration
print_info "Validating Terraform configuration..."
if ! terraform validate; then
    print_error "Terraform configuration is invalid. Please fix the errors and try again."
    exit 1
fi

print_success "Terraform configuration is valid."

# Run terraform plan and capture output
print_info "Running terraform plan to show what changes will be made..."
PLAN_FILE="/tmp/terraform-plan-$(date +%s).tfplan"

if ! terraform plan -out="$PLAN_FILE"; then
    print_error "Terraform plan failed. Please check the configuration and try again."
    exit 1
fi

print_success "Terraform plan completed successfully."

# Show the plan in a more readable format
print_info "Here's what Terraform will do:"
terraform show "$PLAN_FILE"

# Ask for confirmation unless auto-approve is set
if [[ "$AUTO_APPROVE" == "false" ]]; then
    echo
    print_warning "The above changes will be applied to your infrastructure."
    read -p "Do you want to proceed with applying these changes? (y/N): " -r REPLY
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled by user."
        rm -f "$PLAN_FILE"
        exit 0
    fi
fi

# Apply the planned changes
print_info "Applying Terraform changes..."
if terraform apply "$PLAN_FILE"; then
    print_success "Infrastructure deployment completed successfully!"
    
    # Show outputs if any
    if terraform output &> /dev/null; then
        print_info "Terraform outputs:"
        terraform output
    fi
else
    print_error "Terraform apply failed. Please check the logs above."
    rm -f "$PLAN_FILE"
    exit 1
fi

# Clean up the plan file
rm -f "$PLAN_FILE"

print_success "Infrastructure deployment script completed."