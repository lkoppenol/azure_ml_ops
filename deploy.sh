#!/bin/sh

pip install --upgrade pip
pip install -r requirements.txt

# AZ CLI in devops cannot look outside of directory for this python file
echo "Copying score to deploy directory"
cp model/score.py deploy

cd deploy
python deploy_amls.py
./deploy_iot_hub.sh
