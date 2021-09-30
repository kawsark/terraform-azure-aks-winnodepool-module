from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
import os
import json

TFC_TOKEN = os.getenv("TFC_TOKEN", None)
TFC_URL = os.getenv("TFC_URL", None)  # ex: https://app.terraform.io
# set to True if you want to use HTTP or insecure HTTPS
SSL_VERIFY = os.getenv("SSL_VERIFY", False)

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

def build_create_var_payload(ws_id, key, value, env=False, sensitive=False, hcl=False):
	return  {
		"data": {
			"type": "vars",
			"attributes": {
				"key": key,
				"value": value,
				"description": "TODO",
				"category": "terraform" if not env else "env",
				"hcl": hcl,
				"sensitive": sensitive
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

def create_privileged_ws(ws_config, api):
	org_name = ws_config["org_name"]
	ws_name = ws_config["ws_name"]

	api.set_org(org_name)

	workspace = None
	try:
		workspace = api.workspaces.show(workspace_name=ws_name)
	except TFCHTTPNotFound as notfound:
		print(f"Workspace {ws_name} not found.")

	if workspace is None:
		print(f"Creating workspace {ws_name}")
		create_ws_payload = build_create_ws_payload(\
			ws_name, ws_config["tf_version"], ws_config["working_dir"], ws_config["vcs_repo"], \
				ws_config["vcs_oauth_id"], ws_config["branch"])
		workspace = api.workspaces.create(create_ws_payload)

	ws_id = workspace["data"]["id"]
	# print(workspace)

	# Once the workspace is created, inject the user defined variables
	for k in ws_config["variables"]:
		var = ws_config["variables"][k]
		create_var_payload = build_create_var_payload(ws_id, k, var["value"], var["sensitive"], var["hcl"])
		api.workspace_vars.create(ws_id, create_var_payload)
		# created_var = api.workspace_vars.create(ws_id, create_var_payload)
		# print(created_var)

	# Once the workspace is created, need to inject the privileged variables
	# TODO: set up a local Vault.
	# TODO: Get the variables from Vault

	# TODO: apply a policy set to the workspace to restrict the use of anything but modules

	# TODO: Need to plan and apply the privileged workspace, wait for it to complete, then
	# TODO: can I do this with variable sets?

def create_unprivileged_ws(ws_config, api):
	org_name = ws_config["org_name"]
	ws_name = ws_config["ws_name"]

	api.set_org(org_name)

	existing_ws = None
	try:
		existing_ws = api.workspaces.show(workspace_name=ws_name)
	except TFCHTTPNotFound as notfound:
		print(f"Workspace {ws_name} not found.")

	if existing_ws is None:
		print(f"Creating workspace {ws_name}")
		create_ws_payload = build_create_ws_payload(\
			ws_name, ws_config["tf_version"], ws_config["working_dir"], ws_config["vcs_repo"], \
				ws_config["vcs_oauth_id"], ws_config["branch"])
		created_ws = api.workspaces.create(create_ws_payload)
		print("UNPRIVILEGED", created_ws)

	# TODO: populate the unprivileged credentials
	# TODO: provide the outputs

if __name__ == "__main__":
	config = {}
	with open("config.json", "r") as infile:
		config = json.loads(infile.read())

	api = TFC(TFC_TOKEN, url=TFC_URL, verify=False)

	# TODO: Create the AKS cluster w/ elevated credentials
	create_privileged_ws(config["privileged"], api)
	create_unprivileged_ws(config["unprivileged"], api)
