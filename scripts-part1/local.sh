#!/bin/sh
# scripts for local machine to perform data analysis

# download latests measure results from node
gcloud compute scp --recurse --ssh-key-file $GCLOUD_SSH ubuntu@client-measure-rxgw:/home/ubuntu/results ./results --zone europe-west3-a

