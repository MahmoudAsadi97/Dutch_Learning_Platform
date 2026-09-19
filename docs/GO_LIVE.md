# Go live (Phase B) — the owner's runbook

Nothing in this document has been executed. It is the ordered list of what the owner does, once, to put
release 0.1 on Azure with the shape in `infra/main.bicep`: a public web app behind Microsoft Entra sign-in,
an internal API, PostgreSQL, blob storage and Azure AI Speech reached with managed identities, and an
optional Azure OpenAI deployment for the chat provider. Every step names the command and what it costs
in effort or money. Record the outcome of step 0 in `DECISIONS.md` before step 3.

## 0. Decide and record the allowance

Before anything is created, write in `DECISIONS.md` (new entry) the subscription used, the monthly
allowance, whether free credit applies, and the SKUs you accept. The template's defaults are the
smallest paid tiers: Container Apps consumption (scale to zero), PostgreSQL Flexible Server
`Standard_B1ms` burstable with 32 GB, Storage `Standard_LRS`, Speech `S0`, Container Registry `Basic`,
Log Analytics pay-per-GB with 30-day retention, Key Vault standard. Azure OpenAI is off
(`deployChat=false`) until you turn it on. Expect the idle cost to be dominated by PostgreSQL and the
registry; the rest is pay-per-use.

## 1. Prerequisites on your laptop

- Azure CLI signed in: `az login`, `az account set --subscription <id>`.
- Bicep CLI (`az bicep install`).
- A resource group: `az group create --name dlp-rg --location westeurope`.

## 2. App registration for the sign-in wall

The web app uses Container Apps built-in authentication with Microsoft Entra.

1. `az ad app create --display-name "Nederlands oefenen" --sign-in-audience AzureADMyOrg` (or
   `AzureADandPersonalMicrosoftAccount` if the learner signs in with a personal Microsoft account;
   then `--sign-in-audience` accordingly). Note the application (client) id.
2. After step 3 add the redirect URI `https://<web fqdn>/.auth/login/aad/callback` to the registration
   and enable ID tokens.
3. Look up the object ids of the users allowed to sign in: `az ad user show --id <email> --query id -o tsv`
   (personal accounts: the object id appears after their first sign-in attempt in the Entra sign-in logs).
   Put them in `allowedPrincipalObjectIds`; put the e-mail addresses in `ownerAllowlist`.

## 3. Create the infrastructure

```
cp infra/parameters.example.json infra/parameters.json      # git-ignored; fill in the ids
az deployment group create --resource-group dlp-rg --template-file infra/main.bicep \
  --parameters @infra/parameters.json \
  --parameters postgresAdminPassword='<32+ random characters>' assertionSigningKey='<32+ random characters>'
```

Outputs: `webUrl`, `apiInternalFqdn`, `registryLoginServer`, `keyVaultName`, `storageAccountName`,
`speechResourceId`, `postgresHost`. The two container apps start with a placeholder image until step 4.
The Speech resource has local (key) authentication disabled: the API authenticates with its managed
identity (`AZURE_SPEECH_RESOURCE_ID` is set by the template). The Storage account has shared-key access
disabled for the same reason.

## 4. Build and deploy the images

Either run the GitHub workflow `deploy` (manual, OIDC — see step 6) or do it by hand once:

```
az acr build --registry <registry name> --image dlp-api:v0.1.0 --file apps/api/Dockerfile .
az acr build --registry <registry name> --image dlp-web:v0.1.0 --file apps/web/Dockerfile .
az containerapp update -g dlp-rg -n dlp-api --image <registryLoginServer>/dlp-api:v0.1.0
az containerapp update -g dlp-rg -n dlp-web --image <registryLoginServer>/dlp-web:v0.1.0
```

The API image runs `alembic upgrade head` and loads the mission fixture on every start.

## 5. Verify

1. Open `webUrl` in a browser: you must be sent to Microsoft sign-in; after signing in with an allowed
   account the home page shows the status panel with the Azure providers.
2. From your laptop: `python scripts/verify_live.py --url <webUrl>` (anonymous checks), then with the
   cookie of your signed-in session (`AppServiceAuthSession`, copied from the browser's storage panel):
   `python scripts/verify_live.py --url <webUrl> --session-cookie "AppServiceAuthSession=..."`. It runs
   the preflight, one synthesis (label must be `azure-neural`), the usage counters and the acceptance
   checks A01–A06. All PASS moves the Azure adapters from `integration_pending` to `verified_live` in
   `VALIDATION_REPORT.md`; write the date and the output there.
3. On the phone: the full journey (OWNER_ACTIONS 8).

## 6. GitHub Actions with OpenID Connect (no cloud secret in GitHub)

1. Create a deployment app registration: `az ad app create --display-name "dlp-deploy"`, a service
   principal for it (`az ad sp create --id <app id>`), and give it `Contributor` on the resource group
   plus `AcrPush` on the registry.
2. Add a federated credential for the repository:
   issuer `https://token.actions.githubusercontent.com`, subject
   `repo:MahmoudAsadi97/Dutch_Learning_Platform:environment:production`, audience `api://AzureADTokenExchange`.
3. In the repository settings: environment `production`; secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
   `AZURE_SUBSCRIPTION_ID`; variables `AZURE_RESOURCE_GROUP`, `AZURE_ACR_NAME`.
4. Run the `deploy` workflow from the Actions tab. It never runs on push.

## 7. Chat provider in Azure

Ollama does not run in Azure. Set `deployChat=true` to create an Azure OpenAI account with a
`gpt-4o-mini` deployment (`chat-small`); then put the key in Key Vault as `azure-chat-api-key`, add
`AZURE_CHAT_API_KEY` as a Key Vault-backed secret on `dlp-api`, and redeploy. Run
`benchmarks/language/harness.py --provider azure` before relying on it: the local benchmark rows were
plumbing dry runs (D-06), not a model selection. Until then the API runs with the fixture chat model,
which the status panel shows plainly.

## 8. Fixed audio with the Azure voice

Delete the stored clip so it is re-synthesised with `nl-BE-DenaNeural`:
`az storage blob delete --account-name <storage> --container-name learner-audio --name fixed/appointment-change/voicemail-base.wav --auth-mode login`
(and its `.json` sidecar). The next listening step synthesises and stores it again with the label `azure-neural`.

## 9. Rollback

`az containerapp revision list -g dlp-rg -n dlp-web -o table` shows revisions; activate the previous one
with `az containerapp revision activate` and route traffic to it. The database keeps its migrations; a
downgrade needs `alembic downgrade <rev>` from an API container (`az containerapp exec`).

## 10. What stays open after go-live

- The language reviewer's approval per fixed text (`docs/GATE2_DEMO.md`).
- A private endpoint for PostgreSQL instead of the "Azure services" firewall rule (D-15).
- The pricing table (`pricing_entries`) filled from the invoice so `/usage` can estimate cost.
