#!/bin/sh

ibench='cpu l1d l1i l2 llc membw'
parsec='blackscholes canneal dedup ferret freqmine radix vips'

for i in $ibench
do
    # launch ibench pod
    kubectl create -f 'interference/ibench-'$i'.yaml'
    while [ $(kubectl get pods 'ibench-'$i -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]; do echo "[info]: waiting for pod" && sleep 1; done

    for j in $parsec
    do
        # launch parsec job
        kubectl create -f 'parsec-benchmarks/part2a/parsec-'$j'.yaml'
        sleep 5

        # log
        kubectl logs $(kubectl get pods --selector=job-name='parsec-'$j --output=jsonpath='{.items[*].metadata.name}')

        # delete parsec job
        kubectl delete job 'parsec-'$j
        echo '[info]: job parsec-'$j' deleted'
        sleep 5
    done

    # delete current ibench pod
    kubectl delete pods 'ibench-'$i
    echo '[info]: pod ibench-'$i' deleted'
    sleep 5
done

echo '[info]: all tests finished'