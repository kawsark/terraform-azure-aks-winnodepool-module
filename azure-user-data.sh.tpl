#!/bin/bash
set +e 
echo "[Startup] - Startup script for terraform"


echo "[Startup] - Installing kubectl"
# https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl
curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
apt-get update -y
apt-get install -y kubectl

echo "[Startup] - Installing other tools"
sudo apt-get install jq git -y

echo "[Startup] - Write kube config"
cd /home/azureuser/
mkdir -p ./.kube
echo ${kube_config} > .kube/config
chown azureuser:azureuser -R /home/azureuser/.kube

echo "[Startup] - Clone this repo"
git clone https://gitlab.com/kawsark/terraform-azure-aks-winnodepool.git
cd terraform-azure-aks-winnodepool
kubectl apply -R -f kube-manifests/

# List Pods
kubectl get pods -o wide

# Adjust permissions
chown azureuser:azureuser -R /home/azureuser/terraform-azure-aks-winnodepool

# Install Waypoint
# https://www.waypointproject.io/downloads
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
apt-get update -y && sudo apt-get install -y waypoint

echo "[Startup] - completed"