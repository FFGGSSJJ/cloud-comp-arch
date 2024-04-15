#!/bin/sh

export AGENT=$(kubectl get nodes | grep -v NAME | awk 'FNR == 1 {print $1}')
export MEASURE=$(kubectl get nodes | grep -v NAME | awk 'FNR == 2 {print $1}')
export MEMCACHED=$(kubectl get nodes | grep -v NAME | awk 'FNR == 4 {print $1}')

DIRECTION=$1

if [ $DIRECTION = "up" ]
then
    echo "Upload files"
    gcloud compute scp --ssh-key-file $GCLOUD_SSH $2 ubuntu@$AGENT:~/ --zone europe-west3-a
    gcloud compute scp --ssh-key-file $GCLOUD_SSH $2 ubuntu@$MEASURE:~/ --zone europe-west3-a
fi

if [ $DIRECTION = "down" ]
then
    echo "Download files"
    gcloud compute scp --recurse --ssh-key-file $GCLOUD_SSH ubuntu@$MEASURE:~/results/ $2  --zone europe-west3-a
fi
