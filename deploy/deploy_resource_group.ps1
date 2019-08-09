python -c "import yaml, json; yml_file = yaml.safe_load(open('config.yml', 'r')); open('config.json', 'w').write(json.dumps(yml_file));"

$config = Get-content config.json | ConvertFrom-Json
rm config.json

# install iot cli extension
az extension add --name azure-cli-iot-ext
az extension update --name azure-cli-iot-ext

# deploy iot hub to configured location
az login
az group create --location $config.region --name $config.resource_group --subscription $config.subscription
az iot hub create --name $config.iot_hub.name --resource-group $config.resource_group --location $config.region --subscription $config.subscription --sku $config.iot_hub.sku
# az ml workspace create is called from inside the python script via the python azure SDK!