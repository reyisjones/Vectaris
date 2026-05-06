// deploy/azure/main.bicep
// Vectaris – top-level orchestration template
//
// Deploy with:
//   az deployment sub create \
//     --location eastus \
//     --template-file deploy/azure/main.bicep \
//     --parameters environmentName=vectaris-prod \
//                  backendImage=<acr>.azurecr.io/vectaris-backend:latest \
//                  frontendImage=<acr>.azurecr.io/vectaris-frontend:latest

targetScope = 'subscription'

@minLength(3)
@maxLength(20)
param environmentName string

@description('Primary Azure region for all resources.')
param location string = 'eastus'

param backendImage string
param frontendImage string

var resourceGroupName = 'rg-${environmentName}'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: {
    environment: environmentName
    managedBy: 'bicep'
  }
}

module app './app.bicep' = {
  name: 'app-deploy'
  scope: rg
  params: {
    environmentName: environmentName
    location: location
    backendImage: backendImage
    frontendImage: frontendImage
  }
}

output resourceGroupName string = rg.name
output backendUrl string = app.outputs.backendUrl
output frontendUrl string = app.outputs.frontendUrl
