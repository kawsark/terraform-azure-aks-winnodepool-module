# Define Input Variables
# 1. Azure Location (CentralUS)
# 2. Azure Resource Group Name 
# 3. Azure AKS Environment Name (Dev, QA, Prod)

# Azure Location
variable "location" {
  type        = string
  description = "Azure Region where all these resources will be provisioned"
  default     = "Central US"
}

# Azure Resource Group Name
variable "resource_group_name" {
  type        = string
  description = "This variable defines the Resource Group"
  default     = "terraform-aks"
}

# Azure AKS Environment Name
variable "environment" {
  type        = string
  description = "This variable defines the Environment"
  default     = "dev3"
}

# Add some tags
variable "tags" {
  type = map(string)
  default = {
    env   = "dev"
    TTL   = "48h"
    owner = "demouser"
  }
  description = "Tags that should be assigned to the resources in this example"
}

# SSH key variables
variable "ssh_key" {
  description = "The name of a SSH key pair saved in azure"
  default     = "demouser-dev-ssh_key"
}

variable "ssh_key_resource_group" {
  description = "The name of the resource group in Azure"
  default     = "demouser-dev-ssh_rg"
}


# AKS Input Variables


# Windows Admin Username for k8s worker nodes
variable "windows_admin_username" {
  type        = string
  default     = "azureuser" # Should be obtained from Vault secrets management
  description = "This variable defines the Windows admin username k8s Worker nodes"
}

# Windows Admin Password for k8s worker nodes
variable "windows_admin_password" {
  type        = string
  default     = "P@ssw0rd123456789" # Should be obtained from Vault secrets management
  description = "This variable defines the Windows admin password k8s Worker nodes"
}

