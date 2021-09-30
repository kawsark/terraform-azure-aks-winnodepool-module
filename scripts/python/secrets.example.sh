#!/bin/bash

eval $(op signin hashi)

# Terraform Cloud/Enterprise Creds
export TFC_URL=""
export TFC_TOKEN=""

# Required Vault Creds
export VAULT_ADDR=""
export VAULT_TOKEN=""

# Initial Azure Credentials for configuring Vault
export ARM_CLIENT_ID=""
export ARM_TENANT_ID=""
export ARM_CLIENT_SECRET=""
