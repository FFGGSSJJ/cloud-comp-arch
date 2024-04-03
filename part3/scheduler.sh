#!/bin/sh

PARSEC_CONFIG_DIR=../config/parsec-benchmarks/part3/v1
# MEMCACHE_CONFIG_DIR=../config/memcache

sche_a() {
    echo "schedule node a"

    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-a-1.yaml
    kubectl wait --for=condition=Complete job/parsec-radix --timeout=600s
}

sche_b() {
    echo "schedule node b"
    
    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-b-1.yaml
    kubectl wait --for=condition=Complete job/parsec-dedup --timeout=600s

    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-b-2.yaml
    kubectl wait --for=condition=Complete job/parsec-vips --timeout=600s &
    kubectl wait --for=condition=Complete job/parsec-radix --timeout=600s &
    wait

    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-b-3.yaml
    kubectl wait --for=condition=Complete job/parsec-canneal --timeout=600s &
    kubectl wait --for=condition=Complete job/parsec-blackscholes --timeout=600s &
    wait
}

sche_c() {
    echo "schedule node c"

    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-c-1.yaml
    kubectl wait --for=condition=Complete job/parsec-freqmine --timeout=600s

    kubectl create -f $PARSEC_CONFIG_DIR/parsec-node-c-2.yaml
    kubectl wait --for=condition=Complete job/parsec-ferret --timeout=600s
}

# sche_a &
sche_b &
sche_c &
wait

echo "done"