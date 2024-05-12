#!/bin/sh

export AGENT_A=$(kubectl get nodes | grep -v NAME | awk 'FNR == 1 {print $1}')
export AGENT_B=$(kubectl get nodes | grep -v NAME | awk 'FNR == 2 {print $1}')
export MEASURE=$(kubectl get nodes | grep -v NAME | awk 'FNR == 3 {print $1}')

gcloud compute scp --ssh-key-file $GCLOUD_SSH mcperf-compile.sh ubuntu@$AGENT_A:~/ --zone europe-west3-a
gcloud compute scp --ssh-key-file $GCLOUD_SSH mcperf-compile.sh ubuntu@$AGENT_B:~/ --zone europe-west3-a
gcloud compute scp --ssh-key-file $GCLOUD_SSH mcperf-compile.sh ubuntu@$MEASURE:~/ --zone europe-west3-a