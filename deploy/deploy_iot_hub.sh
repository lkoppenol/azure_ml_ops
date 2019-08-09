#!/bin/sh
parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

# read yaml file
eval $(parse_yaml config.yml "config_")

echo "Adding azure-cli-iot extension"
az extension add --name azure-cli-iot-ext
echo "Deleting old deployment, throw & ignore error if already exists"
az iot edge deployment delete --deployment-id $config_iot_hub_deployment_name --hub-name $config_iot_hub_name || true
echo "Creating new deployment"
az iot edge deployment create --content iot-deployment-configuration.json --deployment-id $config_iot_hub_deployment_name --hub-name $config_iot_hub_name --priority 10 --target-condition "$config_iot_hub_edge_condition"
