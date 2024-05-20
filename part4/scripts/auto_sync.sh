#!/bin/sh
MEMCACHED=$(kubectl get nodes | grep -v NAME | awk 'FNR == 4 {print $1}')

# brute force sync between Mac and Google vm
# need to run gcloud compute config-ssh and add pub key manually before using
fswatch ../ | (while read; do rsync -ave ssh ../ ubuntu@$MEMCACHED.europe-west3-a.awesome-caster-415021:~/part4; done) 
