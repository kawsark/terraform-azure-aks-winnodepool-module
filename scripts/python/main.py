from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
import hvac
import os
import json

TFC_TOKEN = os.getenv("TFC_TOKEN", None)
TFC_URL = os.getenv("TFC_URL", None)  # ex: https://app.terraform.io

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", None)

VAULT_AZURE_PRIV_ROLE="my-role"
VAULT_AZURE_UNPRIV_ROLE="my-role"


def build_create_ws_payload(ws_name, tf_version, working_dir, vcs_repo, vcs_oauth_id, branch):
	return {
		"data": {
			"type": "workspaces",
			"attributes": {
				"name": ws_name,
				"terraform_version": tf_version,
				"working-directory": working_dir,
				"global-remote-state": True,
				"vcs-repo": {
					"identifier": vcs_repo,
					"oauth-token-id": vcs_oauth_id,
					"branch": branch
				}
			}
		}
	}


def build_create_var_payload(ws_id, var):
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


def create_privileged_ws(ws_config, tfc_client, vault_client):
	org_name = ws_config["org_name"]
	ws_name = ws_config["ws_name"]

	tfc_client.set_org(org_name)

	workspace = None
	try:
		workspace = tfc_client.workspaces.show(workspace_name=ws_name)
	except TFCHTTPNotFound as notfound:
		print(f"Workspace {ws_name} not found.")

	if workspace is None:
		print(f"Creating workspace {ws_name}")
		create_ws_payload = build_create_ws_payload(\
			ws_name, ws_config["tf_version"], ws_config["working_dir"], ws_config["vcs_repo"], \
				ws_config["vcs_oauth_id"], ws_config["branch"])
		workspace = tfc_client.workspaces.create(create_ws_payload)

	ws_id = workspace["data"]["id"]

	# Once the workspace is created, inject the user defined variables
	# TODO: try catch on the variables if they already exist?
	for var in ws_config["variables"]:
		create_var_payload = build_create_var_payload(ws_id, var)
		tfc_client.workspace_vars.create(ws_id, create_var_payload)

	# Once the workspace is created, get the variables that are needed from Vault
	azure_creds_vars = get_azure_creds(vault_client)

	# Inject the credentials into the workspace
	for var in azure_creds_vars:
		create_var_payload = build_create_var_payload(ws_id, var)
		tfc_client.workspace_vars.create(ws_id, create_var_payload)

	# Trigger a run on the workspace

	# Wait for the run to complete, then create the next workspace


def create_unprivileged_ws(ws_config, tfc_client):
	org_name = ws_config["org_name"]
	ws_name = ws_config["ws_name"]

	tfc_client.set_org(org_name)

	existing_ws = None
	try:
		existing_ws = tfc_client.workspaces.show(workspace_name=ws_name)
	except TFCHTTPNotFound as notfound:
		print(f"Workspace {ws_name} not found.")

	if existing_ws is None:
		print(f"Creating workspace {ws_name}")
		create_ws_payload = build_create_ws_payload(\
			ws_name, ws_config["tf_version"], ws_config["working_dir"], ws_config["vcs_repo"], \
				ws_config["vcs_oauth_id"], ws_config["branch"])
		created_ws = tfc_client.workspaces.create(create_ws_payload)
		print("UNPRIVILEGED", created_ws)

	# TODO: populate the unprivileged credentials
	# TODO: provide the outputs


def get_azure_creds(vault_client):
	# TODO: take the role as a variable
	azure_config = vault_client.secrets.azure.read_config()
	azure_creds = vault_client.secrets.azure.generate_credentials(name="my-role")

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


if __name__ == "__main__":
	config = {}
	with open("config.json", "r") as infile:
		config = json.loads(infile.read())

	tfc_client = TFC(TFC_TOKEN, url=TFC_URL, verify=False)

	# TODO: why does this take so long?
	TIMEOUT_TIME=120
	vault_client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN, timeout=TIMEOUT_TIME)
	# get_azure_creds(vault_client)

	# TODO: Create the AKS cluster w/ elevated credentials
	create_privileged_ws(config["privileged"], tfc_client, vault_client)
	# create_unprivileged_ws(config["unprivileged"], tfc_client, vault_client)
