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
        python src/script.py -f intel_mo_IR -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s AWSCAM -n deploy_ssd_mobilenet_512
    elif [ "${2,,}" = "local-disk-test" ]; then
        python src/script.py -f intel_mo_IR -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s /home/aws_cam/Desktop/traffic.mp4
    elif [ "${2,,}" = "backward-test" ]; then
        python src/script_local.py -st $3 -d $4 -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s AWSCAM
    fi
fi
