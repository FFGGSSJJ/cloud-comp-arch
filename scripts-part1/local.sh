#!/bin/sh
# scripts for local machine to perform data analysis

# download latests measure results from node machine
gcloud compute scp --recurse --ssh-key-file $GCLOUD_SSH ubuntu@client-measure-xsgq:/home/ubuntu/results ./ --zone europe-west3-a

# make sure csv, numpy, matplotlib modules are installed, i wont check
python3 report.py

