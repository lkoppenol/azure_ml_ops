# MLOps for IoT Edge

## 1. Introduction


## 2. Setup
### 2.1 Prerequisites
- az command line installed
- azure account + subscription, enough rights to create a resources and resource groups
- azure devops enabled
- have linux edge device (for now)

### 2.2 Setup resource group
1. Fill out all values in `deploy/config.yml`.  
   Anything that does not exist yet will be automatically created
2. Deploy resources
   **Linux** Manually run `deploy/deploy_resource_group.sh`  
   **Windows** Manually run `powershell -ExecutionPolicy ByPass -File .\deploy_resource_group.ps1`  
   This will install az iot extension locally, create a resource group and iot hub as specified in the config.

### 2.3 Setup iot edge
1. Make your device / vm iot ready  
   Follow the `Install the latest runtime version` steps found here:
   https://docs.microsoft.com/nl-nl/azure/iot-edge/how-to-install-iot-edge-linux
2. After running 2.2 (sub 2) you can find an iot hub instance in the configured resource group. 
    1. Go to `portal.azure.com` > `<your resource group>` > `<your iot hub>` > `IoT Edge` > `Add an IoT Edge device`
    2. Enter a name for the device and click `Save`
    3. Click refresh
    4. Click on the device name
    5. Copy the primary connection string
3. Make your device register itself to iot hub  
   Follow the `Configure the security daemon > Option 1: Manual provisioning` steps found here:
   https://docs.microsoft.com/nl-nl/azure/iot-edge/how-to-install-iot-edge-linux

### 2.4 Setup azure devops
1. Open azure devops (dev.azure.com)
2. Clone the repo to your devops environment  
   Go to `repos` > `<current repository>` > `import repository`.
   Enter `git` / `<url to this repo>` > `<your repo name>`.
3. Generate build pipeline  
   `pipelines` > `build` > `new` > `azure repos git` > `your repo` > `run`
4. Create service principal  
   Go to `project settings` > `service connections` > `new service connection` > `azure resource manager` and select the
   subscription and resource group that you specified in the config file
5. Manually create release pipeline  
   Go to `pipelines` > `releases` > `new` > `new release pipeline` > `empty job`.
    1. Add your repo as artifact. Set trigger to continuous deployment on your desired branch. Create branch if needed
    2. Select stage 1
    3. add 2 tasks;
        1. Use python 3.7
        2. Azure CLI.        
            Set service principal (4) as subscription.  
            Browse to repo/deploy.sh.  
            Select `Access service principal details in script`
    4. Save

### 2.5 Test run
1. Push something to the branch you selected in 2.4 (sub 5.1)
2. Verify build success on azure devops
3. Verify release success on azure devops
4. Verify the following responds `Healthy` on the IoT Edge device: `curl localhost:5001; echo ""`

## 3. Debugging
### 3.1 Azure DevOps
- Check build status
- Check build feedback
- Check release status
- check release loggings

### 3.2 Azure machine learning service
- Check existence of AMLS in your resource group
- Check existence of workspace, model and image in AMLS via portal

### 3.3 IoT Hub
- Check hub exists in your resource group
- Check device is registered in your hub
- Check device is available in your hub
- Check number of modules listed in the hub for your device
- Verify 3 modules listed per `sudo iotedge list` on your edge device
- Verify status of modules/containers per `sudo iotedge list` and `docker ps`
