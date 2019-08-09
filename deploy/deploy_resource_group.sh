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

# install iot cli extension
az extension add --name azure-cli-iot-ext
az extension update --name azure-cli-iot-ext

# deploy iot hub to configured location
az login
az group create --location $config_region --name $config_resource_group --subscription $config_subscription
az iot hub create --name $config_iot_hub_name --resource-group $config_resource_group --location $config_region --subscription $config_subscription --sku $config_iot_hub_sku
# az ml workspace create is called from inside the python script via the python azure SDK!