#!/bin/bash

FILE='/home/aws_cam/Desktop/controller.txt'
echo 'Operation = '${1,,}

if [ "${1,,}" = "switch" ]; then
    echo "Switch ${2,,} analysis"

    if [ "${2,,}" = "on" ]; then
        echo "${3}" > $FILE
        echo "Model ${3} has been deployed"

    elif [ "${2,,}" = "off" ]; then
        if [ -f $FILE ]; then
            rm $FILE
        fi
    fi

elif [ "${1,,}" = "run" ]; then

    if [ "${2,,}" = "real-time-test" ]; then
        python src/worker/script.py -f intel_mo_IR -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s AWSCAM -n deploy_ssd_mobilenet_512
    elif [ "${2,,}" = "local-disk-test" ]; then
        python src/worker/script.py -f intel_mo_IR -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s /home/aws_cam/Desktop/traffic.mp4
    elif [ "${2,,}" = "backward-test" ]; then
        python src/worker/script_local.py -st $3 -d $4 -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s AWSCAM -n deploy_ssd_mobilenet_512
    elif [ "${2,,}" = "datamanagement" ]; then
        echo "Data Management Start"
        python src/worker/dataManagement.py -t 60
    elif [ "${2,,}" = "modelmanagement" ]; then
        echo "Model Management Start"
        python src/worker/modelManagement.py -mps /opt/awscam/artifacts/mxnet_deploy_ssd_resnet50_300_FP16_FUSED.xml /home/aws_cam/Desktop/reid/FP16/person-reidentification-retail-0079.xml
    fi
fi
