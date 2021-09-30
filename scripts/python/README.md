# Setting up Vault from Scratch

[Kawsar's Blog](https://medium.com/hashicorp-engineering/onboarding-the-azure-secrets-engine-for-vault-f09d48c68b69) outlines what happens below.

## Start a Vault Dev Server

```bash
vault server -dev -dev-root-token-id=root
```

## Export the Vault Env Vars

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root"
```

## Log in to Azure

```bash
az login
az account list
```

## TODO: Title

```bash
export CREDS_FILE_PATH="vault-demo.json"
export ARM_SP_NAME="neil_vault_demo"
export ARM_SUBSCRIPTION_ID=$(az account list | jq -r ".[0].id")
```

## TODO: Title

```bash
az ad sp create-for-rbac -n $ARM_SP_NAME --role="Owner" --scopes="/subscriptions/$ARM_SUBSCRIPTION_ID" > $CREDS_FILE_PATH
```

## TODO: Title

```bash
export ARM_CLIENT_ID="$(cat ${CREDS_FILE_PATH} | jq -r .appId)"
export ARM_TENANT_ID="$(cat ${CREDS_FILE_PATH} | jq -r .tenant)"
export ARM_CLIENT_SECRET="$(cat ${CREDS_FILE_PATH} | jq -r .password)"
export RESOURCE_GROUP="rg-alice-demoapp-dev" # TODO: why is this name hardcoded?
```

## TODO: Title

```bash
# Create owner Role assignment
az role assignment create --assignee ${ARM_CLIENT_ID} \
  --role "Owner" \
  --subscription ${ARM_SUBSCRIPTION_ID}

# Setting permission ID variables
resourceAccessid1="311a71cc-e848-46a1-bdf8-97ff7156d8e6=Scope"
resourceAccessid2="1cda74f2-2616-4834-b122-5cb1b07f8a59=Role"
resourceAccessid3="78c8a3c8-a07e-4b9e-af1b-b5ccab50a175=Role"
resourceAppId="00000002-0000-0000-c000-000000000000"

# Assign permissions
az ad app permission add --id ${ARM_CLIENT_ID} \
  --api ${resourceAppId} \
  --api-permissions ${resourceAccessid1} ${resourceAccessid2} ${resourceAccessid3}

# Admin grant
az ad app permission grant --id ${ARM_CLIENT_ID} --api ${resourceAppId}

# Grant Admin consent
az ad app permission admin-consent --id ${ARM_CLIENT_ID}

# Displaying permissions
az ad app permission list --id ${ARM_CLIENT_ID}
```

Then create the resource group:

```bash
az group create -l westus -n "${RESOURCE_GROUP}"
```

# TODO: set the role name in an env var

```bash
vault secrets enable azure

vault write azure/config \
    subscription_id=$ARM_SUBSCRIPTION_ID \
    tenant_id=$ARM_TENANT_ID \
    client_id=$ARM_CLIENT_ID \
    client_secret=$ARM_CLIENT_SECRET

vault write azure/roles/my-role ttl=1h azure_roles=-<<EOF
    [
        {
            "role_name": "Owner",
            "scope":  "/subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
        }
    ]
EOF

vault read azure/creds/my-role
```
