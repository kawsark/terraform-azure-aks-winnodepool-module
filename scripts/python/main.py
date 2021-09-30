from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
import hvac
import os
import json

# TODO: get the tfc token from Vault
TFC_TOKEN = os.getenv("TFC_TOKEN", None)
TFC_URL = os.getenv("TFC_URL", None)  # ex: https://app.terraform.io

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", None)

# TODO: handle both Kawsar's public Vault instance and the local one
# TODO: have one for privileged, one for unprivileged
# TODO: how to handle the generated subscription?
VAULT_AZURE_PRIV_ROLE="my-role"
VAULT_AZURE_UNPRIV_ROLE="my-role"
VAULT_AZURE_PATH="azure"
# TODO: these roles don't work (rg-alice-demoapp-dev-role, rg-alice-demoapp-qa-role)
# VAULT_AZURE_PRIV_ROLE="rg-alice-demoapp-qa-role"
# VAULT_AZURE_UNPRIV_ROLE="rg-alice-demoapp-qa-role"
# VAULT_AZURE_PATH="azure-demo"

def get_azure_creds(vault_client, vault_azure_role):
	azure_config = vault_client.secrets.azure.read_config(mount_point=VAULT_AZURE_PATH)
	azure_creds = vault_client.secrets.azure.generate_credentials(mount_point=VAULT_AZURE_PATH, name=vault_azure_role)

	subscription_id = azure_config["subscription_id"]
	tenant_id = azure_config["tenant_id"]
	client_id = azure_creds["client_id"]
	client_secret = azure_creds["client_secret"]

	merged_creds_data = [
		{
			"key": "ARM_SUBSCRIPTION_ID",
			"value": subscription_id,
			"sensitive": False,
			"hcl": False,
			"category": "env"
		},
		{
			"key": "ARM_TENANT_ID",
			"value": tenant_id,
			"sensitive": True,
			"hcl": False,
			"category": "env"
		},
		{
			"key": "ARM_CLIENT_ID",
			"value": client_id,
			"sensitive": True,
			"hcl": False,
			"category": "env"
		},
		{
			"key": "ARM_CLIENT_SECRET",
			"value": client_secret,
			"sensitive": True,
			"hcl": False,
			"category": "env"
		},
	]

	return merged_creds_data


def build_create_ws_payload(ws):
	return {
		"data": {
			"type": "workspaces",
			"attributes": {
				"name": ws["ws_name"],
				"terraform_version": ws["tf_version"],
				"working-directory": ws["working_dir"],
				"auto-apply": ws["auto_apply"],
				"global-remote-state": True,
				"vcs-repo": {
					"identifier": ws["vcs_repo"],
					"oauth-token-id": ws["vcs_oauth_id"],
					"branch": ws["branch"]
				}
			}
		}
	}


def build_create_var_payload(ws_id, var):
	# TODO: have defaults for each variable
	return  {
		"data": {
			"type": "vars",
			"attributes": {
				"key": var["key"],
				"value": var["value"],
				"description": "TODO",
				"category": var["category"],
				"hcl": var["hcl"],
				"sensitive": var["sensitive"]
			},
			"relationships": {
				"workspace": {
					"data": {
						"id": ws_id,
						"type": "workspaces"
					}
				}
			}
		}
	}

def build_create_run_payload(ws_id):
	return {
		"data": {
			"attributes": {
				"message": "TODO: creating a run from script"
			},
			"type":"runs",
			"relationships": {
				"workspace": {
					"data": {
						"type": "workspaces",
						"id": ws_id
					}
				},
			}
		}
	}


def create_ws(ws_config, tfc_client, vault_client):
	org_name = ws_config["org_name"]
	ws_name = ws_config["ws_name"]

	tfc_client.set_org(org_name)

	workspace = None
	try:
		workspace = tfc_client.workspaces.show(workspace_name=ws_name)
		# NOTE: only use this when not auto-applying, as then we may have orphaned resources
		# TODO: remove this when I'm not iterating, as this deletes the workspace
		print(f"Workspace {ws_name} found, deleting it while iterating...")
		tfc_client.workspaces.destroy(workspace_name=ws_name)
		# workspace = None
	except TFCHTTPNotFound:
		print(f"Workspace {ws_name} not found.")

	if workspace is None:
		print(f"Creating workspace {ws_name}")
		create_ws_payload = build_create_ws_payload(ws_config)
		workspace = tfc_client.workspaces.create(create_ws_payload)

	return workspace


def populate_tf_vars(ws_id, ws_config):
	# Once the workspace is created, inject the user defined variables
	# TODO: try catch on the variables if they already exist?
	print("Populating TF variables...")
	for var in ws_config["variables"]:
		create_var_payload = build_create_var_payload(ws_id, var)
		tfc_client.workspace_vars.create(ws_id, create_var_payload)
	print("TF variables populated.")


def populate_env_vars(ws_id, vault_azure_role):
	# Once the workspace is created, get the variables that are needed from Vault
	print("Getting Azure Creds from Vault, this may take a moment...")
	# TODO: the creds don't have enough privileges to create
	azure_creds_vars = get_azure_creds(vault_client, vault_azure_role)
	print("Azure Creds retrieved from Vault.")

	# Inject the credentials into the workspace
	print("Populating environment variables...")
	for var in azure_creds_vars:
		create_var_payload = build_create_var_payload(ws_id, var)
		tfc_client.workspace_vars.create(ws_id, create_var_payload)
	print("Environment variables populated.")


def trigger_run(ws_id):
	# Trigger a run on the workspace
	create_run_payload = build_create_run_payload(ws_id)
	created_run = tfc_client.runs.create(create_run_payload)
	print(created_run)

	# Wait for the run to complete, then create the next workspace


if __name__ == "__main__":
	config = {}
	with open("config.json", "r") as infile:
		config = json.loads(infile.read())

	tfc_client = TFC(TFC_TOKEN, url=TFC_URL, verify=False)

	# TODO: why does this take so long?
	TIMEOUT_TIME=120
	vault_client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN, timeout=TIMEOUT_TIME)
	# get_azure_creds(vault_client, VAULT_AZURE_PRIV_ROLE)
	test_azure(vault_client)

	priv_config = config["privileged"]
	unpriv_config = config["unprivileged"]

	# Create the AKS cluster w/ elevated credentials
	# priv_ws = create_ws(priv_config, tfc_client, vault_client)
	# priv_ws_id = priv_ws["data"]["id"]
	# populate_tf_vars(priv_ws_id, priv_config)
	# populate_env_vars(priv_ws_id, VAULT_AZURE_PRIV_ROLE)

	# Create the secondary workspace with non-elevated credentials
	# create_ws(config["unprivileged"], tfc_client, vault_client)
