#!/bin/sh

ibench='cpu l1d l1i l2 llc membw'
parsec='blackscholes canneal dedup ferret freqmine radix vips'
RESULT_DIR='./results'

if [ ! -d $RESULT_DIR ] 
then
	mkdir $RESULT_DIR
else
    rm $RESULT_DIR/*.txt
fi

echo '----[info]: perform none interference test'
for j in $parsec
do
    # launch parsec job
    echo '[info]: create parsec pod'
    kubectl create -f '../../cloud-comp-arch-project/parsec-benchmarks/part2a/parsec-'$j'.yaml'
    kubectl wait --for=condition=Complete job/parsec-$j --timeout=600s

    # log
    kubectl logs $(kubectl get pods --selector=job-name='parsec-'$j --output=jsonpath='{.items[*].metadata.name}') | grep 'real' >> $RESULT_DIR'/parsec-'$j'.txt'

    # delete parsec job
    kubectl delete job 'parsec-'$j
    echo '[info]: job parsec-'$j' now deleted'
    sleep 5
done

echo '----[info]: perform interference test'
for i in $ibench
do
    # launch ibench pod
    echo '[info]: create ibench pod'
    kubectl create -f '../../cloud-comp-arch-project/interference/ibench-'$i'.yaml'
    kubectl wait --for=condition=Ready pod/ibench-$i --timeout=60s

    # make sure interference take effect
    sleep 5

    for j in $parsec
    do
        # launch parsec job
        echo '[info]: create parsec pod'
        kubectl create -f '../../cloud-comp-arch-project/parsec-benchmarks/part2a/parsec-'$j'.yaml'
        kubectl wait --for=condition=Complete job/parsec-$j --timeout=600s

        # log
        kubectl logs $(kubectl get pods --selector=job-name='parsec-'$j --output=jsonpath='{.items[*].metadata.name}') | grep 'real' >> $RESULT_DIR'/parsec-'$j'.txt'

        # delete parsec job
        kubectl delete job 'parsec-'$j
        echo '[info]: job parsec-'$j' now deleted'
        sleep 5
    done

    # delete current ibench pod
    kubectl delete pods 'ibench-'$i
    echo '[info]: pod ibench-'$i' now deleted'

    # make sure resources are recycled
    sleep 5
done

echo '----[info]: all tests finished'
python3 report.py
