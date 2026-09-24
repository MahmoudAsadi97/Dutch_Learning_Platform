// Create the foundation, build images, run the migration job, then enable the web app.
targetScope = 'resourceGroup'

@minLength(3)
@maxLength(12)
param name string = 'dlp'
param location string = resourceGroup().location
param tenantId string = tenant().tenantId
param deployApplications bool = false
param deployMigrationJob bool = false
// Keep false until Easy Auth and migrations have been verified.
param publicWeb bool = false
param apiImage string = ''
param webImage string = ''
param authClientId string = ''
param allowedPrincipalObjectIds array = []
param ownerAllowlist string = ''
@secure()
param authClientSecret string
@secure()
@minLength(32)
param assertionSigningKey string
@secure()
@minLength(24)
param postgresAdminPassword string
@secure()
@minLength(24)
param postgresAppPassword string
param postgresAdminLogin string = 'dlpadmin'
// Explicit region-supported selections; no silent model upgrades.
param chatModelName string
param chatModelVersion string
@allowed(['Standard', 'DataZoneStandard', 'GlobalStandard'])
param chatDeploymentSku string = 'Standard'
@minValue(1)
param chatCapacity int = 1
param strongModelName string = ''
param strongModelVersion string = ''
param paidUsageApproved bool = false
@minValue(1)
param dailyModelCalls int = 80
@minValue(1)
param totalModelCalls int = 2000
@minValue(1)
param dailyTokens int = 80000
@minValue(1)
param totalTokens int = 2000000
@minValue(1)
param dailyAudioSeconds int = 1200
@minValue(1)
param totalAudioSeconds int = 18000
@minValue(1)
param monthlyBudget int = 50
param budgetStartDate string
param budgetAlertEmails array

var suffix = toLower(uniqueString(resourceGroup().id))
var acrPull = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var secretsUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${name}-logs-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    workspaceCapping: { dailyQuotaGb: json('0.1') }
  }
}
resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${name}-insights'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web', WorkspaceResourceId: logs.id, IngestionMode: 'LogAnalytics' }
}
resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: '${name}-monthly'
  properties: {
    category: 'Cost'
    amount: monthlyBudget
    timeGrain: 'Monthly'
    timePeriod: { startDate: budgetStartDate }
    notifications: {
      warning: { enabled: true, operator: 'GreaterThanOrEqualTo', threshold: 80, contactEmails: budgetAlertEmails, thresholdType: 'Actual' }
      limit: { enabled: true, operator: 'GreaterThanOrEqualTo', threshold: 100, contactEmails: budgetAlertEmails, thresholdType: 'Actual' }
    }
  }
}
resource identities 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = [for role in ['api', 'web', 'migration']: {
  name: '${name}-${role}-id'
  location: location
}]
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: toLower('${name}acr${suffix}')
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}
resource imageReaders 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for i in range(0, 3): {
  name: guid(registry.id, identities[i].id, acrPull)
  scope: registry
  properties: { roleDefinitionId: acrPull, principalId: identities[i].properties.principalId, principalType: 'ServicePrincipal' }
}]
resource network 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${name}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.30.0.0/16'] }
    subnets: [
      { name: 'apps', properties: { addressPrefix: '10.30.0.0/23', delegations: [{ name: 'apps', properties: { serviceName: 'Microsoft.App/environments' } }] } }
      { name: 'database', properties: { addressPrefix: '10.30.2.0/24', delegations: [{ name: 'postgres', properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' } }] } }
    ]
  }
}
resource databaseDns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${name}.private.postgres.database.azure.com'
  location: 'global'
}
resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: databaseDns
  name: '${name}-link'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: network.id } }
}
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${name}-pg-${suffix}'
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32, autoGrow: 'Enabled' }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    network: {
      publicNetworkAccess: 'Disabled'
      delegatedSubnetResourceId: '${network.id}/subnets/database'
      privateDnsZoneArmResourceId: databaseDns.id
    }
    authConfig: { passwordAuth: 'Enabled', activeDirectoryAuth: 'Disabled' }
  }
  dependsOn: [dnsLink]
}
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'dlp'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: take('${name}-kv-${suffix}', 24)
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 14
  }
}
var secretNames = ['assertion-signing-key', 'database-url', 'migration-database-url', 'database-app-password', 'auth-client-secret']
var secretValues = [
  assertionSigningKey
  'postgresql+psycopg://dlp_app:${uriComponent(postgresAppPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/dlp?sslmode=verify-full'
  'postgresql+psycopg://${postgresAdminLogin}:${uriComponent(postgresAdminPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/dlp?sslmode=verify-full'
  postgresAppPassword
  authClientSecret
]
resource secrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = [for i in range(0, length(secretNames)): {
  parent: vault
  name: secretNames[i]
  properties: { value: secretValues[i] }
}]
var grants = [
  { secret: 0, identity: 0 }
  { secret: 1, identity: 0 }
  { secret: 0, identity: 1 }
  { secret: 4, identity: 1 }
  { secret: 2, identity: 2 }
  { secret: 3, identity: 2 }
]
resource secretReaders 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for grant in grants: {
  name: guid(secrets[grant.secret].id, identities[grant.identity].id, secretsUser)
  scope: secrets[grant.secret]
  properties: { roleDefinitionId: secretsUser, principalId: identities[grant.identity].properties.principalId, principalType: 'ServicePrincipal' }
}]
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(take('${name}st${suffix}', 24))
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false, allowSharedKeyAccess: false, supportsHttpsTrafficOnly: true, accessTier: 'Hot' }
}
resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: { deleteRetentionPolicy: { enabled: true, days: 14 }, containerDeleteRetentionPolicy: { enabled: true, days: 14 } }
}
resource audio 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobs
  name: 'learner-audio'
  properties: { publicAccess: 'None' }
}
resource blobWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(audio.id, identities[0].id, 'blob-writer')
  scope: audio
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: identities[0].properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource speech 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: '${name}-speech-${suffix}'
  location: location
  kind: 'SpeechServices'
  sku: { name: 'S0' }
  properties: { customSubDomainName: '${name}-speech-${suffix}', publicNetworkAccess: 'Enabled', disableLocalAuth: true }
}
resource speechUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speech.id, identities[0].id, 'speech-user')
  scope: speech
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
    principalId: identities[0].properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: '${name}-oai-${suffix}'
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: { customSubDomainName: '${name}-oai-${suffix}', publicNetworkAccess: 'Enabled', disableLocalAuth: true }
}
resource smallModel 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: 'chat-small'
  sku: { name: chatDeploymentSku, capacity: chatCapacity }
  properties: { model: { format: 'OpenAI', name: chatModelName, version: chatModelVersion }, versionUpgradeOption: 'NoAutoUpgrade' }
}
resource strongModel 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (!empty(strongModelName)) {
  parent: openAi
  name: 'chat-strong'
  sku: { name: chatDeploymentSku, capacity: chatCapacity }
  properties: { model: { format: 'OpenAI', name: strongModelName, version: strongModelVersion }, versionUpgradeOption: 'NoAutoUpgrade' }
  dependsOn: [smallModel]
}
resource modelUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identities[0].id, 'chat-user')
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: identities[0].properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${name}-env'
  location: location
  properties: {
    vnetConfiguration: { infrastructureSubnetId: '${network.id}/subnets/apps', internal: false }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: { customerId: logs.properties.customerId, sharedKey: logs.listKeys().primarySharedKey }
    }
  }
}
resource migration 'Microsoft.App/jobs@2024-03-01' = if (deployApplications || deployMigrationJob) {
  name: '${name}-migrate'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identities[2].id}': {} } }
  properties: {
    environmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 900
      replicaRetryLimit: 0
      manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
      registries: [{ server: registry.properties.loginServer, identity: identities[2].id }]
      secrets: [
        { name: 'migration-database-url', keyVaultUrl: secrets[2].properties.secretUri, identity: identities[2].id }
        { name: 'database-app-password', keyVaultUrl: secrets[3].properties.secretUri, identity: identities[2].id }
      ]
    }
    template: {
      containers: [{
        name: 'migration'
        image: apiImage
        command: ['python', '-m', 'dlp.release', 'migrate']
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        env: [
          { name: 'MIGRATION_DATABASE_URL', secretRef: 'migration-database-url' }
          { name: 'DATABASE_APP_PASSWORD', secretRef: 'database-app-password' }
          { name: 'PGSSLROOTCERT', value: '/etc/ssl/certs/ca-certificates.crt' }
        ]
      }]
    }
  }
  dependsOn: [imageReaders, secretReaders, database]
}
resource api 'Microsoft.App/containerApps@2024-03-01' = if (deployApplications) {
  name: '${name}-api'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identities[0].id}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: false, targetPort: 8000, transport: 'http', allowInsecure: false }
      registries: [{ server: registry.properties.loginServer, identity: identities[0].id }]
      secrets: [
        { name: 'assertion-signing-key', keyVaultUrl: secrets[0].properties.secretUri, identity: identities[0].id }
        { name: 'database-url', keyVaultUrl: secrets[1].properties.secretUri, identity: identities[0].id }
      ]
    }
    template: {
      containers: [{
        name: 'api'
        image: apiImage
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        env: [
          { name: 'APP_ENV', value: 'production' }
          { name: 'DEV_AUTH_ENABLED', value: 'false' }
          { name: 'OWNER_ALLOWLIST', value: ownerAllowlist }
          { name: 'ASSERTION_SIGNING_KEY', secretRef: 'assertion-signing-key' }
          { name: 'DATABASE_URL', secretRef: 'database-url' }
          { name: 'PGSSLROOTCERT', value: '/etc/ssl/certs/ca-certificates.crt' }
          { name: 'PAID_USAGE_ENABLED', value: string(paidUsageApproved) }
          { name: 'CHAT_PROVIDER', value: 'azure' }
          { name: 'AZURE_CHAT_ENDPOINT', value: openAi.properties.endpoint }
          { name: 'AZURE_CHAT_API_VERSION', value: 'v1' }
          { name: 'AZURE_CHAT_DEPLOYMENT_SMALL', value: 'chat-small' }
          { name: 'AZURE_CHAT_DEPLOYMENT_STRONG', value: empty(strongModelName) ? 'chat-small' : 'chat-strong' }
          { name: 'STT_PROVIDER', value: 'azure' }
          { name: 'TTS_PROVIDER', value: 'azure' }
          { name: 'AZURE_SPEECH_REGION', value: location }
          { name: 'AZURE_SPEECH_RESOURCE_ID', value: speech.id }
          { name: 'AZURE_STT_LOCALE', value: 'nl-BE' }
          { name: 'AZURE_TTS_VOICE', value: 'nl-BE-DenaNeural' }
          { name: 'BLOB_PROVIDER', value: 'azure' }
          { name: 'AZURE_STORAGE_ACCOUNT_URL', value: storage.properties.primaryEndpoints.blob }
          { name: 'BLOB_CONTAINER', value: 'learner-audio' }
          { name: 'AZURE_CLIENT_ID', value: identities[0].properties.clientId }
          { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
          { name: 'JOB_LOOP_ENABLED', value: 'true' }
          { name: 'USAGE_DAILY_MODEL_CALLS', value: string(dailyModelCalls) }
          { name: 'USAGE_TOTAL_MODEL_CALLS', value: string(totalModelCalls) }
          { name: 'USAGE_DAILY_TOKENS', value: string(dailyTokens) }
          { name: 'USAGE_TOTAL_TOKENS', value: string(totalTokens) }
          { name: 'USAGE_DAILY_AUDIO_SECONDS', value: string(dailyAudioSeconds) }
          { name: 'USAGE_TOTAL_AUDIO_SECONDS', value: string(totalAudioSeconds) }
        ]
        probes: [
          { type: 'Startup', httpGet: { path: '/health', port: 8000 }, periodSeconds: 10, failureThreshold: 30 }
          { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 30 }
          { type: 'Readiness', httpGet: { path: '/health/ready', port: 8000 }, periodSeconds: 10, timeoutSeconds: 10 }
        ]
      }]
      // Keep the database-backed job loop alive; no separate worker service.
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
  dependsOn: [imageReaders, secretReaders, speechUser, blobWriter, modelUser, smallModel]
}
resource web 'Microsoft.App/containerApps@2024-03-01' = if (deployApplications) {
  name: '${name}-web'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identities[1].id}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: publicWeb, targetPort: 3000, transport: 'http', allowInsecure: false }
      registries: [{ server: registry.properties.loginServer, identity: identities[1].id }]
      secrets: [
        { name: 'assertion-signing-key', keyVaultUrl: secrets[0].properties.secretUri, identity: identities[1].id }
        { name: 'auth-client-secret', keyVaultUrl: secrets[4].properties.secretUri, identity: identities[1].id }
      ]
    }
    template: {
      containers: [{
        name: 'web'
        image: webImage
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        env: [
          { name: 'NODE_ENV', value: 'production' }
          { name: 'APP_ENV', value: 'production' }
          { name: 'DEV_AUTH_ENABLED', value: 'false' }
          { name: 'OWNER_ALLOWLIST', value: ownerAllowlist }
          { name: 'ASSERTION_SIGNING_KEY', secretRef: 'assertion-signing-key' }
          { name: 'API_INTERNAL_URL', value: 'https://${api!.properties.configuration.ingress.fqdn}' }
          { name: 'PUBLIC_ORIGIN', value: 'https://${name}-web.${environment.properties.defaultDomain}' }
        ]
        probes: [
          { type: 'Startup', httpGet: { path: '/health', port: 3000 }, periodSeconds: 10, failureThreshold: 30 }
          { type: 'Readiness', httpGet: { path: '/health', port: 3000 }, periodSeconds: 10 }
          { type: 'Liveness', httpGet: { path: '/health', port: 3000 }, periodSeconds: 30 }
        ]
      }]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
  dependsOn: [imageReaders, secretReaders]
}
resource webAuth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = if (deployApplications) {
  parent: web
  name: 'current'
  properties: {
    platform: { enabled: true }
    globalValidation: { unauthenticatedClientAction: 'RedirectToLoginPage', redirectToProvider: 'azureactivedirectory', excludedPaths: ['/health'] }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: authClientId
          clientSecretSettingName: 'auth-client-secret'
          openIdIssuer: '${az.environment().authentication.loginEndpoint}${tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: ['api://${authClientId}', authClientId]
          defaultAuthorizationPolicy: { allowedPrincipals: { identities: allowedPrincipalObjectIds } }
        }
      }
    }
    login: { preserveUrlFragmentsForLogins: false }
  }
}
output registryLoginServer string = registry.properties.loginServer
output registryName string = registry.name
output keyVaultName string = vault.name
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output webUrl string = deployApplications ? 'https://${web!.properties.configuration.ingress.fqdn}' : ''
output apiInternalFqdn string = deployApplications ? api!.properties.configuration.ingress.fqdn : ''
output migrationJobName string = '${name}-migrate'
