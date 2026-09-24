#!/usr/bin/env bash
# Release the checked-out, clean commit through the existing Azure migration gate.
set -euo pipefail
cd "$(dirname "$0")/.."
DLP_RELEASE_GROUP="${DLP_RELEASE_GROUP:-dlp-production}"
DLP_RELEASE_ACR="${DLP_RELEASE_ACR:-dlpacrhofmzccgjnr4s}"
DLP_RELEASE_PREFIX="${DLP_RELEASE_PREFIX:-dlp}"
DLP_RELEASE_REPOSITORY="${DLP_RELEASE_REPOSITORY:-MahmoudAsadi97/Dutch_Learning_Platform}"
DLP_RELEASE_ADMIN="${1:-}"
command -v az >/dev/null || { echo 'Azure CLI is required.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
  echo 'Commit or stash your local changes before building an immutable release.' >&2
  exit 1
fi
DLP_RELEASE_SHA="$(git rev-parse HEAD)"
python3 scripts/azure_release.py verify-ci --repository "$DLP_RELEASE_REPOSITORY" --commit "$DLP_RELEASE_SHA"
az account show --query '{subscription:name,id:id}' --output table
az group show --name "$DLP_RELEASE_GROUP" --query '{name:name,location:location}' --output table
python3 scripts/azure_release.py verify --resource-group "$DLP_RELEASE_GROUP" --prefix "$DLP_RELEASE_PREFIX"
az acr build --registry "$DLP_RELEASE_ACR" --image "dlp-api:$DLP_RELEASE_SHA" --file apps/api/Dockerfile .
az acr build --registry "$DLP_RELEASE_ACR" --image "dlp-web:$DLP_RELEASE_SHA" --file apps/web/Dockerfile .
DLP_RELEASE_SERVER="$(az acr show --name "$DLP_RELEASE_ACR" --query loginServer --output tsv)"
DLP_RELEASE_API_DIGEST="$(az acr repository show --name "$DLP_RELEASE_ACR" --image "dlp-api:$DLP_RELEASE_SHA" --query digest --output tsv)"
DLP_RELEASE_WEB_DIGEST="$(az acr repository show --name "$DLP_RELEASE_ACR" --image "dlp-web:$DLP_RELEASE_SHA" --query digest --output tsv)"
DLP_RELEASE_ARGS=()
if [ -n "$DLP_RELEASE_ADMIN" ]; then
  DLP_RELEASE_ARGS=(--curriculum-admin-emails "$DLP_RELEASE_ADMIN")
fi
python3 scripts/azure_release.py deploy --resource-group "$DLP_RELEASE_GROUP" --prefix "$DLP_RELEASE_PREFIX" \
  --api-image "$DLP_RELEASE_SERVER/dlp-api@$DLP_RELEASE_API_DIGEST" \
  --web-image "$DLP_RELEASE_SERVER/dlp-web@$DLP_RELEASE_WEB_DIGEST" "${DLP_RELEASE_ARGS[@]}"
DLP_RELEASE_HOST="$(az containerapp show --name "$DLP_RELEASE_PREFIX-web" --resource-group "$DLP_RELEASE_GROUP" --query properties.configuration.ingress.fqdn --output tsv)"
python3 scripts/verify_live.py --url "https://$DLP_RELEASE_HOST" --mode anonymous
printf 'Published revision: %s\nOpen https://%s and complete the signed-in checks in docs/GO_LIVE.md.\n' "$DLP_RELEASE_SHA" "$DLP_RELEASE_HOST"
