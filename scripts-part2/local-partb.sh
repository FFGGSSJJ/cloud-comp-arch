#!/bin/sh

parsec='blackscholes canneal dedup ferret freqmine radix vips'
RESULT_DIR='./results-b'

if [ ! -d $RESULT_DIR ] 
then
	mkdir $RESULT_DIR
else
    rm $RESULT_DIR/*.txt
fi

echo '----[info]: perform parallel test'
for j in $parsec
do
    # launch parsec job
    echo '[info]: create parsec pod'
    kubectl create -f '../../cloud-comp-arch-project/parsec-benchmarks/part2b/parsec-'$j'.yaml'
    kubectl wait --for=condition=Complete job/parsec-$j --timeout=6000s

    # log
    kubectl logs $(kubectl get pods --selector=job-name='parsec-'$j --output=jsonpath='{.items[*].metadata.name}') | grep 'real' >> $RESULT_DIR'/parsec-'$j'.txt'

    # delete parsec job
    kubectl delete job 'parsec-'$j
    echo '[info]: job parsec-'$j' now deleted'
    sleep 5
done

echo '----[info]: all tests finished'