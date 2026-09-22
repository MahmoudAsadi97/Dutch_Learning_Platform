# Azure release guide — Taalstudio 0.2

This is a controlled, owner-only release of the appointment mission, not the entire future A1–C2
platform. Infrastructure and containers are checked in CI. They have **not** been deployed to Azure
by this update. Only actual authenticated provider calls can establish `verified_live`.

## 1. What to create

Create one resource group and a single-tenant Microsoft Entra app registration. The Bicep template
creates the remaining Azure resources. Do not also create duplicate services manually.

| Resource | Initial configuration | Purpose |
|---|---|---|
| Container Apps environment | Consumption workload profile, VNet integration | Managed application hosting |
| Web Container App | 0.25 vCPU / 0.5 GiB, 0–1 replicas | Next.js, one origin, Easy Auth, signed API proxy |
| API Container App | 0.25 vCPU / 0.5 GiB, exactly 1 replica | FastAPI, LangGraph, PostgreSQL job loop |
| Manual Container Apps Job | Same API image, 15-minute limit, no automatic retry | Migrations and content loading, separate credentials |
| Container Registry | Basic, administrator login disabled | Release images referenced by digest |
| PostgreSQL Flexible Server | PostgreSQL 16, B1ms, 32 GB, 7-day backup, no HA | Private database; runtime DML role and release administrator |
| Storage | Standard LRS, private blob container, 14-day soft delete | Retained practice audio; no account keys |
| Azure Speech | S0, managed identity, nl-BE | Short-turn transcription and synthetic Belgian Dutch playback |
| Azure OpenAI account | Usage-based regional deployment, explicit model/version | Conversation and evidence-based feedback |
| Optional second deployment | Same account, only after selecting a supported model/version | Strong-model comparison; absent means small deployment is reused |
| Key Vault | Standard, RBAC, purge protection | Separate secrets for API, web and migration identities |
| Log Analytics + Application Insights | 30-day logs, 0.1 GB/day ingestion target, sampled request telemetry | Operational errors, latency and health |
| VNet + private DNS | Separate delegated application and database subnets | Database has no public endpoint |
| Cost Management budget | Owner-selected amount, 80% and 100% email alerts | Cost warnings, **not a hard spending cap** |

There is no Front Door, Service Bus, Translator, OCR, Kubernetes, creative-media provider or separate
vector store. Private study notes, scans, local models, recordings, environment files and instructions
remain on the laptop and are excluded from Git and container build context. Production progress and
any explicitly retained practice recordings live in the configured database and blob container.

## 2. Owner preflight — do this before spending

1. Revoke any GitHub token previously pasted into chat. Use the normal signed-in GitHub/Azure tools.
2. Confirm subscription/credits, region and quotas. Check current prices in the Azure calculator for
   your region and currency, including the warm API, database, registry, logs, storage and speech.
   The default `monthlyBudget=50` is an alert amount in the billing currency, **not a price estimate**.
3. Record the approved allowance and provider limits privately. Set `paidUsageApproved=true` only
   after that decision. Defaults limit calls, tokens and audio; they do not guarantee an exact euro cap.
   Budgets are delayed alerts; inspect actual Cost Management usage during the first week.
4. Select a region-supported chat model and version. This client requires Chat Completions, JSON
   mode, `temperature` and `max_tokens`. A reasoning-only deployment with different request semantics
   is not interchangeable. Do not silently select a Global deployment if regional processing matters.
   Confirm both candidate deployments when running a two-model language benchmark; one deployment
   alone is not a comparison. Availability, quotas and expiry are subscription-dependent.
5. Sign in with Azure CLI and choose the intended subscription. Install/update the `containerapp`
   extension and Bicep. The bootstrap identity needs resource creation plus role-assignment rights
   on this resource group; the deployment identity is a separate, narrower identity.
6. Create an Entra app registration for this tenant, a client secret with a recorded expiry, and note
   the application ID and **user object ID** (not the application object ID). Personal Microsoft users
   must exist as a member/guest in this tenant. The intended user's email claim must match the API allowlist.

## 3. Prepare the ignored parameter file

Copy `infra/parameters.example.json` to `infra/parameters.local.json`. Fill every `REPLACE_…` value in
your editor. The local file is ignored by Git and Docker. Do not put secrets in command-line arguments,
screenshots or public documentation. Prefer Key Vault parameter references for a mature deployment.

- Generate three separate random secrets: administrator password, application password (both at least
  24 characters), and signing key (at least 32). Keep them in a password manager. Do not regenerate them
  between the bootstrap steps: the template is declarative and reuses these values.
- Supply the Entra client secret, IDs, owner email and alert email.
- `budgetStartDate` must be the first day of the current month, e.g. `2026-09-01T00:00:00Z` when deploying
  in September 2026. Adjust for the actual deployment month.
- Fill model name/version and supported SKU/capacity. Supply `strongModelName` and
  `strongModelVersion` together, or leave both empty.
- Leave `deployApplications`, `deployMigrationJob` and `publicWeb` false initially.

The examples below run in Bash/WSL, **not Windows Command Prompt**. Use a real Windows path in cmd;
use `/mnt/c/...` only after entering WSL. A trailing `$` is a shell prompt symbol, not part of the folder name.

```bash
cd "/mnt/c/Users/Nima/Desktop/MINE/My_projects/Dutch Learning Platform/Final_Project_v1"
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
az extension add --name containerapp --upgrade
az bicep install
export DLP_RG="dlp-production"
export DLP_PREFIX="dlp"
az group create --name "$DLP_RG" --location westeurope
az bicep build --file infra/main.bicep --outfile /tmp/dlp-template.json
az deployment group what-if --resource-group "$DLP_RG" --template-file infra/main.bicep \
  --parameters @infra/parameters.local.json
```

Read the plan. This is for a **new** environment. An existing public PostgreSQL server/Container Apps
environment cannot be assumed to convert in place to this private topology. Back up and plan a
side-by-side migration instead of forcing replacement of existing learner data.

## 4. Foundation, real images and migration — in that order

```bash
az deployment group create --name foundation --resource-group "$DLP_RG" \
  --template-file infra/main.bicep --parameters @infra/parameters.local.json
export DLP_ACR="$(az deployment group show -g "$DLP_RG" -n foundation --query properties.outputs.registryName.value -o tsv)"
export DLP_REGISTRY="$(az acr show -n "$DLP_ACR" --query loginServer -o tsv)"
export DLP_SHA="$(git rev-parse HEAD)"
az acr build --registry "$DLP_ACR" --image "dlp-api:$DLP_SHA" --file apps/api/Dockerfile .
az acr build --registry "$DLP_ACR" --image "dlp-web:$DLP_SHA" --file apps/web/Dockerfile .
export DLP_API_DIGEST="$(az acr repository show -n "$DLP_ACR" --image "dlp-api:$DLP_SHA" --query digest -o tsv)"
export DLP_WEB_DIGEST="$(az acr repository show -n "$DLP_ACR" --image "dlp-web:$DLP_SHA" --query digest -o tsv)"
az deployment group create --name release-job --resource-group "$DLP_RG" \
  --template-file infra/main.bicep --parameters @infra/parameters.local.json \
  --parameters deployMigrationJob=true apiImage="$DLP_REGISTRY/dlp-api@$DLP_API_DIGEST"
python scripts/azure_release.py migrate --resource-group "$DLP_RG" --prefix "$DLP_PREFIX"
```

Stop if migration fails. Do not continue to the web deployment. The job takes an advisory lock,
applies Alembic, loads the original versioned mission pack without approving its language, and grants
the runtime role DML privileges only. Database administrator credentials never enter the API container.
On Azure, RBAC propagation can take time: investigate the deployment/job status and retry only after
the permission configuration is correct; do not broaden the role to fix a timing issue.

## 5. Deploy privately, configure sign-in, then publish

```bash
az deployment group create --name runtime --resource-group "$DLP_RG" \
  --template-file infra/main.bicep --parameters @infra/parameters.local.json \
  --parameters deployApplications=true publicWeb=false \
  apiImage="$DLP_REGISTRY/dlp-api@$DLP_API_DIGEST" webImage="$DLP_REGISTRY/dlp-web@$DLP_WEB_DIGEST"
export DLP_HOST="$(az containerapp show -g "$DLP_RG" -n "$DLP_PREFIX-web" --query properties.configuration.ingress.fqdn -o tsv)"
```

In the Entra app registration, add the **Web** redirect URI
`https://<DLP_HOST>/.auth/login/aad/callback` and enable the ID-token setting required by the selected
Easy Auth flow. Confirm the tenant and client-secret expiry. No application code changes are needed.
Keep all paths behind sign-in except the web `/health` probe (which returns no user information).

```bash
python scripts/azure_release.py verify --resource-group "$DLP_RG" --prefix "$DLP_PREFIX"
python scripts/azure_release.py publish --resource-group "$DLP_RG" --prefix "$DLP_PREFIX"
python scripts/verify_live.py --url "https://$DLP_HOST" --mode anonymous
```

The publication command checks internal API ingress, production flags, restricted Easy Auth and
healthy revisions before enabling external web ingress. The anonymous script checks the sign-in
boundary only; it does not claim the model or microphone works. Keep `publicWeb=true` and the real
image references in subsequent approved infrastructure deployments, or a later template application
will deliberately make the web private again. Never set `publicWeb=true` for initial bootstrap.

## 6. Live acceptance — required, not replaceable by fixtures

- Sign in as the allowlisted owner. Confirm another account and an anonymous browser cannot access
  learner pages/API; sign out and test again. Verify `/api/health/ready` succeeds when signed in.
- Inspect Settings: production, managed-identity Azure providers, correct limits, no fixture identity.
- For the scripted authenticated check, put the browser's `AppServiceAuthSession=…` cookie in the
  temporary `DLP_SESSION_COOKIE` environment variable using a hidden prompt/password manager. Do not
  put it in shell history or pass it as a command argument. Then run:

  ```bash
  python scripts/verify_live.py --url "https://$DLP_HOST" --mode authenticated --allow-paid-smoke
  unset DLP_SESSION_COOKIE
  ```

  This makes one short, budgeted synthesis and verifies provider configuration, counters and acceptance
  rules. It does **not** prove STT, model language quality or a complete conversation.
- Complete the four steps with actual model/speech services. Confirm dates are validated, feedback cites
  saved evidence, typed input does not become spoken evidence, assistance is tracked and a draft survives
  reload and navigation. Inspect the deployment/model labels; record latency and actual usage.
- On the **actual phone/browser over HTTPS**: allow/deny microphone permission, record, replay, send,
  interrupt playback, background the page and return. Test network interruption, retry, audio autoplay
  restrictions and a transcript correction. Emulated mobile screenshots are not this test.
- Run the 40-case language harness with each real candidate model and get qualified Belgian Dutch
  review of the fixed pack and sampled responses. The harness's expected/wrong dry runs prove plumbing
  only. Do not mark content reviewed until a real reviewer approves it. No pronunciation scores or
  certificates are issued by this release.
- Lower a daily usage limit temporarily to check the stop/recovery UI; restore the approved value.
  Check Application Insights for route/status/duration only, not prompts or recordings.
- Perform a PostgreSQL point-in-time restore to a **separate server**, validate row counts and sample
  evidence, then document the measured recovery time and recovery point. Never test by deleting the
  only database. Test blob recovery separately; database backup does not back up Blob Storage.

Record date, commit/image digests, region, provider versions, physical device, results and unresolved
items privately. Only evidence from the corresponding real service changes its status to `verified_live`.

## 7. Subsequent releases

Create GitHub environment `production`, require owner approval, and restrict deployments to `main`.
Configure OIDC federation for subject `repo:MahmoudAsadi97/Dutch_Learning_Platform:environment:production`.
Store `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` as environment secrets; set variables
`AZURE_RESOURCE_GROUP`, `AZURE_ACR_NAME`, `AZURE_APP_PREFIX`.

The deployment identity needs ACR build/push and Container Apps/job update/execute rights scoped to this
group. It does not need Key Vault secret-read rights or Owner. Job execution is privileged because it
uses the migration identity; protect workflow edits and the production approval accordingly.

Run the manual `deploy` workflow after **main CI succeeds for the exact commit**. It builds images,
resolves digests, verifies topology, runs migrations, waits for each new healthy revision and checks
anonymous access. It never creates the foundation or publishes a private initial site automatically.
Deployments are serialized. Use additive/backward-compatible migrations; the tiny single-replica setup
does not promise zero downtime or high availability.

## 8. Operations and recovery

- **Rollback:** record the previous image digests before a release. If only code changed and schema is
  compatible, redeploy the prior digests and verify readiness. Do not run Alembic downgrade blindly.
  An older image fails readiness against a newer migration head by design: use a forward fix or a
  separately restored database with a reviewed recovery procedure. Keep the current database intact.
- **Pause exposure:** set the web ingress to internal with Azure CLI/Portal. This stops browser access
  but does not stop database/storage billing. Pausing/stopping resources is a separate owner action.
- **Alerts:** budget emails are provisioned. Set Azure Monitor notifications for failed revisions,
  repeated 5xx and job failures after the first live telemetry check; no alert channel is claimed tested.
- **Rotation:** rotate the Entra secret before expiry; update the vault and affected app revisions.
  Rotate web/API signing secrets together. Database role changes require the controlled release job.
- **Data:** microphone-test recordings are local replay only and not retained as cloud blobs. Practice
  recordings can be retained. Agree retention and deletion before inviting anyone else; soft delete
  retains deleted blobs for 14 days and backups retain older database records for 7 days. JSON export
  is an export of progress/evidence, not a database backup. No general multi-user deletion SLA is claimed.
- **Dependency updates:** API production dependencies are hash-locked; web dependencies use npm's lock.
  Regenerate, inspect and run CI before updating. Rebuild images for base-image security patches.

## References

Configuration follows [Container Apps Entra authentication](https://learn.microsoft.com/en-us/azure/container-apps/authentication-entra),
[Key Vault references](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets),
[health probes](https://learn.microsoft.com/en-us/azure/container-apps/health-probes),
[PostgreSQL private networking](https://learn.microsoft.com/en-us/azure/postgresql/network/concepts-networking-private),
[Azure OpenAI managed identity](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/managed-identity?view=foundry-classic),
and [Next.js nonce-based CSP](https://nextjs.org/docs/app/guides/content-security-policy).
Compile success is not a substitute for subscription-specific Azure validation and a real deployment.
