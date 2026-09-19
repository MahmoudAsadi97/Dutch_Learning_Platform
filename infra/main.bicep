// Release 0.1, Phase B target: one resource group, one Container Apps environment.
//
//   web (public, built-in authentication with Microsoft Entra) ──/api──▶ api (internal ingress only)
//   api ──managed identity──▶ Storage (blob), Speech; api ──password from Key Vault──▶ PostgreSQL
//
// Not executed in Phase A. The owner records the authorised allowance and SKUs in DECISIONS.md before
// the first `az deployment group create` (docs/GO_LIVE.md).

targetScope = 'resourceGroup'

@description('Short name used as a prefix for every resource (letters and digits, 3-12 characters).')
@minLength(3)
@maxLength(12)
param name string = 'dlp'

@description('Azure region for every resource.')
param location string = resourceGroup().location

@description('Microsoft Entra tenant id used by the built-in authentication of the web app.')
param tenantId string = tenant().tenantId

@description('Application (client) id of the app registration created for the built-in authentication.')
param authClientId string

@description('Object ids of the Entra users allowed to sign in (the owner, later the learner).')
param allowedPrincipalObjectIds array

@description('Owner allowlist as the API sees it: comma-separated e-mail addresses.')
param ownerAllowlist string

@description('Administrator login of the PostgreSQL flexible server.')
param postgresAdminLogin string = 'dlpadmin'

@secure()
@description('Administrator password of the PostgreSQL flexible server; stored in Key Vault, never in a template output.')
param postgresAdminPassword string

@secure()
@description('Shared secret (32+ random characters) that signs the web→API assertions.')
param assertionSigningKey string

@description('Container image for the API, as pushed to the registry created here (tag included).')
param apiImage string = ''

@description('Container image for the web app, as pushed to the registry created here (tag included).')
param webImage string = ''

@description('Deploy an Azure OpenAI account and a small deployment for the chat provider (costs money; record the allowance first).')
param deployChat bool = false

@description('Azure OpenAI model deployed when deployChat is true.')
param chatModelName string = 'gpt-4o-mini'

@description('Azure OpenAI model version deployed when deployChat is true.')
param chatModelVersion string = '2024-07-18'

var suffix = toLower(uniqueString(resourceGroup().id))
var storageName = toLower(take('${name}st${suffix}', 24))
var registryName = toLower('${name}acr${suffix}')
var keyVaultName = toLower('${name}-kv-${suffix}')
var postgresName = toLower('${name}-pg-${suffix}')
var speechName = toLower('${name}-speech-${suffix}')
var openAiName = toLower('${name}-oai-${suffix}')
var containerName = 'learner-audio'
var databaseName = 'dlp'

// Built-in role definition ids (stable GUIDs)
var roleAcrPull = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var roleStorageBlobDataContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var roleCognitiveServicesSpeechUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
var roleKeyVaultSecretsUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var roleCognitiveServicesOpenAiUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')

// ----- observability ---------------------------------------------------------------------------------------------

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${name}-logs-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ----- identities ------------------------------------------------------------------------------------------------

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-api-id'
  location: location
}

resource webIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-web-id'
  location: location
}

// ----- registry --------------------------------------------------------------------------------------------------

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource apiAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, apiIdentity.id, roleAcrPull)
  scope: registry
  properties: {
    roleDefinitionId: roleAcrPull
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, webIdentity.id, roleAcrPull)
  scope: registry
  properties: {
    roleDefinitionId: roleAcrPull
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- secrets ---------------------------------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

resource secretSigningKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'assertion-signing-key'
  properties: { value: assertionSigningKey }
}

resource secretPostgresPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-admin-password'
  properties: { value: postgresAdminPassword }
}

resource apiKeyVaultReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, apiIdentity.id, roleKeyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: roleKeyVaultSecretsUser
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webKeyVaultReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, webIdentity.id, roleKeyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: roleKeyVaultSecretsUser
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- storage ---------------------------------------------------------------------------------------------------

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 14 }
  }
}

resource audioContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: { publicAccess: 'None' }
}

resource apiBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, apiIdentity.id, roleStorageBlobDataContributor)
  scope: storage
  properties: {
    roleDefinitionId: roleStorageBlobDataContributor
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- speech ----------------------------------------------------------------------------------------------------

resource speech 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: speechName // required for Entra ID (managed identity) authentication
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true // keys off: the API authenticates with its managed identity
  }
}

resource apiSpeechUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speech.id, apiIdentity.id, roleCognitiveServicesSpeechUser)
  scope: speech
  properties: {
    roleDefinitionId: roleCognitiveServicesSpeechUser
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- chat (optional) -------------------------------------------------------------------------------------------

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = if (deployChat) {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false // the chat client authenticates with a key held in Key Vault for 0.1
  }
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployChat) {
  parent: openAi
  name: 'chat-small'
  sku: { name: 'Standard', capacity: 10 }
  properties: {
    model: { format: 'OpenAI', name: chatModelName, version: chatModelVersion }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

resource apiOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployChat) {
  name: guid(resourceGroup().id, apiIdentity.id, roleCognitiveServicesOpenAiUser, 'openai')
  scope: openAi
  properties: {
    roleDefinitionId: roleCognitiveServicesOpenAiUser
    principalId: apiIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- database --------------------------------------------------------------------------------------------------

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgresName
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32, autoGrow: 'Enabled' }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    network: { publicNetworkAccess: 'Enabled' }
    authConfig: { passwordAuth: 'Enabled', activeDirectoryAuth: 'Disabled' }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: databaseName
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}

// Container Apps have no fixed egress addresses on the consumption plan; the server accepts Azure
// services and the API requires TLS. A private endpoint is the Phase B follow-up once the allowance
// permits a VNet-integrated environment.
resource postgresAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgres
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

// ----- container apps environment --------------------------------------------------------------------------------

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${name}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

var databaseUrl = 'postgresql+psycopg://${postgresAdminLogin}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${databaseName}?sslmode=require'

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${name}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${apiIdentity.id}': {} }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: false // reachable only inside the environment: the web app is the single public entry
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        { server: registry.properties.loginServer, identity: apiIdentity.id }
      ]
      secrets: [
        { name: 'assertion-signing-key', keyVaultUrl: secretSigningKey.properties.secretUri, identity: apiIdentity.id }
        { name: 'database-url', value: databaseUrl }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: empty(apiImage) ? 'mcr.microsoft.com/k8se/quickstart:latest' : apiImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'APP_ENV', value: 'production' }
            { name: 'API_HOST', value: '0.0.0.0' }
            { name: 'DEV_AUTH_ENABLED', value: 'false' }
            { name: 'OWNER_ALLOWLIST', value: ownerAllowlist }
            { name: 'ASSERTION_SIGNING_KEY', secretRef: 'assertion-signing-key' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'CHAT_PROVIDER', value: deployChat ? 'azure' : 'fixture' }
            { name: 'AZURE_CHAT_ENDPOINT', value: deployChat ? 'https://${openAiName}.openai.azure.com' : '' }
            { name: 'AZURE_CHAT_DEPLOYMENT_SMALL', value: deployChat ? 'chat-small' : '' }
            { name: 'STT_PROVIDER', value: 'azure' }
            { name: 'TTS_PROVIDER', value: 'azure' }
            { name: 'AZURE_SPEECH_REGION', value: location }
            { name: 'AZURE_SPEECH_RESOURCE_ID', value: speech.id }
            { name: 'AZURE_STT_LOCALE', value: 'nl-BE' }
            { name: 'AZURE_TTS_VOICE', value: 'nl-BE-DenaNeural' }
            { name: 'BLOB_PROVIDER', value: 'azure' }
            { name: 'AZURE_STORAGE_ACCOUNT_URL', value: storage.properties.primaryEndpoints.blob }
            { name: 'BLOB_CONTAINER', value: containerName }
            { name: 'AZURE_CLIENT_ID', value: apiIdentity.properties.clientId }
            { name: 'JOB_LOOP_ENABLED', value: 'true' }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, initialDelaySeconds: 10, periodSeconds: 30 }
            { type: 'Readiness', httpGet: { path: '/health', port: 8000 }, initialDelaySeconds: 5, periodSeconds: 10 }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
  dependsOn: [apiAcrPull, apiKeyVaultReader]
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${name}-web'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${webIdentity.id}': {} }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        { server: registry.properties.loginServer, identity: webIdentity.id }
      ]
      secrets: [
        { name: 'assertion-signing-key', keyVaultUrl: secretSigningKey.properties.secretUri, identity: webIdentity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: empty(webImage) ? 'mcr.microsoft.com/k8se/quickstart:latest' : webImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'NODE_ENV', value: 'production' }
            { name: 'APP_ENV', value: 'production' }
            { name: 'DEV_AUTH_ENABLED', value: 'false' }
            { name: 'OWNER_ALLOWLIST', value: ownerAllowlist }
            { name: 'ASSERTION_SIGNING_KEY', secretRef: 'assertion-signing-key' }
            { name: 'API_INTERNAL_URL', value: 'https://${api.properties.configuration.ingress.fqdn}' }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
  dependsOn: [webAcrPull, webKeyVaultReader]
}

// Built-in authentication: every request to the web app must carry a signed-in Microsoft Entra identity;
// the platform injects X-MS-CLIENT-PRINCIPAL-* headers that the web proxy reads and checks against the allowlist.
resource webAuth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: web
  name: 'current'
  properties: {
    platform: { enabled: true }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: authClientId
          openIdIssuer: '${az.environment().authentication.loginEndpoint}${tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: ['api://${authClientId}', authClientId]
          defaultAuthorizationPolicy: {
            allowedPrincipals: { identities: allowedPrincipalObjectIds }
          }
        }
      }
    }
    login: {
      preserveUrlFragmentsForLogins: false
    }
  }
}

output webUrl string = 'https://${web.properties.configuration.ingress.fqdn}'
output apiInternalFqdn string = api.properties.configuration.ingress.fqdn
output registryLoginServer string = registry.properties.loginServer
output keyVaultName string = keyVault.name
output storageAccountName string = storage.name
output speechResourceId string = speech.id
output postgresHost string = postgres.properties.fullyQualifiedDomainName
