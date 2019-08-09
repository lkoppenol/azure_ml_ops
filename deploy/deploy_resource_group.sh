#!/bin/sh

# Parse YAML
resource_group=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['resource_group']);")
subscription=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['subscription']);")
region=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['region']);")
hub_sku=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['iot_hub']['sku']);")
hub_name=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['iot_hub']['name']);")

# install iot cli extension
az extension add --name azure-cli-iot-ext
az extension update --name azure-cli-iot-ext

# deploy iot hub to configured location
az login
az group create --location $config_region --name $resource_group --subscription $subscription
az iot hub create --name $hub_name --resource-group $resource_group --location $region --subscription $subscription --sku $hub_sku
# az ml workspace create is called from inside the python script via the python azure SDK!