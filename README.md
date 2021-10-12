## terraform-azure-aks-winnodepool-module

This module can be used to provision an AKS cluster with a Linux and Windows Node Pool. It was adapted from this GitHub repo: [skamasam/TF-Code-Azure-Win-Nodepool](https://github.com/skamasam/TF-Code-Azure-Win-Nodepool). 

### How to use

We recommend using this repo by first publishing it as a module in a TFC/TFE Private Module Registry (PMR) of your TFE/TFE Organization. Please see: [Publishing Modules to the Terraform Cloud Private Module Registry](https://www.terraform.io/docs/cloud/registry/publish.html)

Once it is published, please write a main.tf file to use this module as shown in the snippet below. A full example is provided in this repo: [terraform-azure-aks-winnodepool](https://gitlab.com/kawsark/terraform-azure-aks-winnodepool/-/blob/main/README.md).
```bash
# main.tf:
module "aks_winnodepool_module" {
  source  = "app.terraform.io/GitlabCI-demos/aks-winnodepool-module/azure"
  version = "1.1.7"
...
```

### Module Inputs
Please see the [02-variables.tf](./02-variables.tf) file for inputs. 

### Module Outputs
Please see the [08-outputs.tf](./08-outputs.tf) file for outputs. 
- **Note**: One of the important items exported in this repo is `kube_config`. This is an attribute of the `azurerm_kubernetes_cluster` resource. This output is used in an upstream Workspace to allow developer access to AKS. For more information, please see: [Reading the kubeconfig](https://gitlab.com/kawsark/terraform-azure-devvm-aks#reading-the-kubeconfig) for more information.
