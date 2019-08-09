#!/bin/sh

# Parse YAML
deployment_name=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['iot_hub']['deployment_name']);")
hub_name=$(python -c "import yaml; print(yaml.safe_load(open('config.yml', 'r'))['iot_hub']['name']);")

echo "Adding azure-cli-iot extension"
az extension add --name azure-cli-iot-ext
echo "Deleting old deployment, throw & ignore error if already exists"
az iot edge deployment delete --deployment-id $deployment_name --hub-name $hub_name || true
echo "Creating new deployment"
az iot edge deployment create --content iot-deployment-configuration.json --deployment-id $deployment_name --hub-name $hub_name --priority 10 --target-condition '*'
