# This terraform configuration will create a VM from which kubectl commands can be issued
# Example adopted from: https://docs.microsoft.com/en-us/azure/developer/terraform/create-linux-virtual-machine-with-infrastructure

# Lookup SSH key
data "azurerm_ssh_public_key" "devvm_ssh" {
  name                = var.ssh_key
  resource_group_name = var.ssh_key_resource_group
}


# Create public IP
resource "azurerm_public_ip" "devvm_publicip" {
  name                = "devvm-PublicIP"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name
  allocation_method   = "Dynamic"

  tags = var.tags
}

# Create Network Security Group and rule
resource "azurerm_network_security_group" "devvm_nsg" {
  name                = "devvm-SecurityGroup"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

# Create network interface
resource "azurerm_network_interface" "devvm_nic" {
  name                = "devvm-NIC"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name

  ip_configuration {
    name                          = "myNicConfiguration"
    subnet_id                     = azurerm_subnet.aks-default.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.devvm_publicip.id
  }

  tags = {
    environment = "Terraform Demo"
  }
}

# Connect the security group to the network interface
resource "azurerm_network_interface_security_group_association" "example" {
  network_interface_id      = azurerm_network_interface.devvm_nic.id
  network_security_group_id = azurerm_network_security_group.devvm_nsg.id
}

# Create virtual machine
resource "azurerm_linux_virtual_machine" "devvm" {
  name                  = "devvm"
  location              = azurerm_resource_group.aks_rg.location
  resource_group_name   = azurerm_resource_group.aks_rg.name
  network_interface_ids = [azurerm_network_interface.devvm_nic.id]
  size                  = "Standard_DS1_v2"

  os_disk {
    name                 = "myOsDisk"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  computer_name                   = "terraform-devvm"
  admin_username                  = "azureuser"
  disable_password_authentication = true

  admin_ssh_key {
    username   = "azureuser"
    public_key = data.azurerm_ssh_public_key.devvm_ssh.public_key
  }

  tags = var.tags
}