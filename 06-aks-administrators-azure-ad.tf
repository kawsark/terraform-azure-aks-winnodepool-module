data "azuread_client_config" "current" {}


# Create Azure AD Group in Active Directory for AKS Admins
resource "azuread_group" "aks_administrators" {
  display_name = "${azurerm_resource_group.aks_rg.name}-cluster-administrators"
  owners       = [data.azuread_client_config.current.object_id]
  # security_enabled = true
  description = "Azure AKS Kubernetes administrators for the ${azurerm_resource_group.aks_rg.name}-cluster."
}

# To fetech current user data
#data "azuread_user" "azuread_existing_user" {
#  user_principal_name = "satish.kamasamudram@atyeti.com"
#}

# link existing user to the new group
#resource "azuread_group_member" "link_existing_user" {
#  group_object_id  = azuread_group.aks_administrators.id
#  member_object_id = data.azuread_user.azuread_existing_user.id
#}

# For creating new users - we need the below resource block. Left the below block for your reference
/*
resource "azuread_user" "example" {
  user_principal_name = "jdoe@hashicorp.com"
  display_name        = "J. Doe"
  mail_nickname       = "jdoe"
  password            = "SecretP@sswd99!"
}
*/