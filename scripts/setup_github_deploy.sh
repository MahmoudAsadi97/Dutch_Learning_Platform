#!/usr/bin/env bash
# One-time setup so the manual `deploy` workflow can release from GitHub without any stored password:
# an Entra application that GitHub Actions signs in to with a short-lived OIDC token, scoped to the
# resource group, plus the `production` environment on the repository with its secrets and variables.
#
#   export GITHUB_TOKEN=<a fine-grained token with Administration and Secrets/Variables write on the repo>
#   bash scripts/setup_github_deploy.sh
#
# Needs a signed-in Azure CLI (`az login`) with rights to create app registrations and role assignments
# in the resource group, and either `gh` or Python 3 with PyNaCl (installed automatically with --user)
# to encrypt the secrets. Safe to re-run: every step reuses what exists.
set -euo pipefail
cd "$(dirname "$0")/.."
GROUP="${DLP_RELEASE_GROUP:-dlp-production}"
ACR="${DLP_RELEASE_ACR:-dlpacrhofmzccgjnr4s}"
PREFIX="${DLP_RELEASE_PREFIX:-dlp}"
REPOSITORY="${DLP_RELEASE_REPOSITORY:-MahmoudAsadi97/Dutch_Learning_Platform}"
APP_NAME="${DLP_DEPLOY_APP_NAME:-dlp-github-deploy}"
ENVIRONMENT="production"
command -v az >/dev/null || { echo 'Azure CLI is required.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
[ -n "${GITHUB_TOKEN:-}" ] || { echo 'Set GITHUB_TOKEN to a token that may administer the repository.' >&2; exit 1; }

SUBSCRIPTION="$(az account show --query id -o tsv)"
TENANT="$(az account show --query tenantId -o tsv)"
GROUP_ID="$(az group show --name "$GROUP" --query id -o tsv)"
echo "Subscription $SUBSCRIPTION, tenant $TENANT, resource group $GROUP"

# 1. Application registration and service principal (reused when they exist).
APP_ID="$(az ad app list --display-name "$APP_NAME" --query '[0].appId' -o tsv)"
if [ -z "$APP_ID" ]; then
  APP_ID="$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)"
  echo "Created application $APP_NAME ($APP_ID)"
else
  echo "Application $APP_NAME exists ($APP_ID)"
fi
az ad sp show --id "$APP_ID" >/dev/null 2>&1 || az ad sp create --id "$APP_ID" >/dev/null
SP_OBJECT="$(az ad sp show --id "$APP_ID" --query id -o tsv)"

# 2. Federated credential: only workflow runs of this repository's `production` environment may sign in.
SUBJECT="repo:$REPOSITORY:environment:$ENVIRONMENT"
if ! az ad app federated-credential list --id "$APP_ID" --query "[?subject=='$SUBJECT'] | [0].name" -o tsv | grep -q .; then
  az ad app federated-credential create --id "$APP_ID" --parameters "$(python3 - "$SUBJECT" <<'EOF'
import json, sys
print(json.dumps({"name": "github-production", "issuer": "https://token.actions.githubusercontent.com",
                  "subject": sys.argv[1], "audiences": ["api://AzureADTokenExchange"]}))
EOF
)" >/dev/null
  echo "Federated credential added for $SUBJECT"
else
  echo "Federated credential for $SUBJECT exists"
fi

# 3. Rights: build and push images, update the apps, start the migration job. Contributor on the group
#    covers these; it grants no Key Vault secret reads (the vault uses role-based data access) and no Owner.
if [ -z "$(az role assignment list --assignee "$SP_OBJECT" --scope "$GROUP_ID" --role Contributor --query '[0].id' -o tsv)" ]; then
  az role assignment create --assignee-object-id "$SP_OBJECT" --assignee-principal-type ServicePrincipal \
    --role Contributor --scope "$GROUP_ID" >/dev/null
  echo "Granted Contributor on $GROUP"
else
  echo "Contributor on $GROUP already granted"
fi

# 4. GitHub: the `production` environment (owner approval, main only), its secrets and variables.
export APP_ID TENANT SUBSCRIPTION GROUP ACR PREFIX REPOSITORY ENVIRONMENT
python3 - <<'EOF'
import base64, json, os, subprocess, sys, urllib.error, urllib.request

token, repo, env_name = os.environ["GITHUB_TOKEN"], os.environ["REPOSITORY"], os.environ["ENVIRONMENT"]
api = "https://api.github.com"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "dlp-setup"}


def call(method, path, body=None, accept=()):
    """Status and decoded body; an HTTP error is fatal unless its status is listed in `accept`."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(api + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as error:
        if error.code in accept:
            return error.code, {}
        print(f"{method} {path} -> {error.code}: {error.read().decode()[:300]}", file=sys.stderr)
        raise SystemExit(1) from error


status, me = call("GET", "/user")
status, repo_info = call("GET", f"/repos/{repo}")
owner_id = repo_info["owner"]["id"]
call("PUT", f"/repos/{repo}/environments/{env_name}", {
    "reviewers": [{"type": "User", "id": owner_id}],
    "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
})
status, policies = call("GET", f"/repos/{repo}/environments/{env_name}/deployment-branch-policies")
if not any(p["name"] == "main" for p in policies.get("branch_policies", [])):
    call("POST", f"/repos/{repo}/environments/{env_name}/deployment-branch-policies", {"name": "main", "type": "branch"})
print(f"Environment {env_name}: approval by {me['login']}, deployments from main only")

try:
    from nacl import encoding, public  # type: ignore
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--user", "pynacl"], check=True)
    from nacl import encoding, public  # type: ignore

status, key = call("GET", f"/repos/{repo}/environments/{env_name}/secrets/public-key")
sealed = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder()))
for name, value in {"AZURE_CLIENT_ID": os.environ["APP_ID"], "AZURE_TENANT_ID": os.environ["TENANT"],
                    "AZURE_SUBSCRIPTION_ID": os.environ["SUBSCRIPTION"]}.items():
    encrypted = base64.b64encode(sealed.encrypt(value.encode())).decode()
    call("PUT", f"/repos/{repo}/environments/{env_name}/secrets/{name}", {"encrypted_value": encrypted, "key_id": key["key_id"]})
    print(f"Secret {name} set")

for name, value in {"AZURE_RESOURCE_GROUP": os.environ["GROUP"], "AZURE_ACR_NAME": os.environ["ACR"],
                    "AZURE_APP_PREFIX": os.environ["PREFIX"]}.items():
    status, _ = call("GET", f"/repos/{repo}/environments/{env_name}/variables/{name}", accept=(404,))
    if status == 404:
        call("POST", f"/repos/{repo}/environments/{env_name}/variables", {"name": name, "value": value})
    else:
        call("PATCH", f"/repos/{repo}/environments/{env_name}/variables/{name}", {"name": name, "value": value})
    print(f"Variable {name} = {value}")
EOF

cat <<EOF

Done. Release from GitHub: Actions → deploy → Run workflow (branch main) → approve the production
deployment when asked. The workflow refuses a commit whose main CI run did not succeed.
Revoke any personal token you created only for this setup.
EOF
