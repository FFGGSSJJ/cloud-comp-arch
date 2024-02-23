#!/bin/sh
echo 'MEMCACHED_IP: ' $MEMCACHED_IP
echo 'INTERNAL_AGENT_IP:' $INTERNAL_AGENT_IP

RESULT_DIR='/home/ubuntu/results/'
if [ ! -d $RESULT_DIR ]
	mkdir $RESULT_DIR
fi

for i in 1 2 3
do
	echo 'test-'$i
	RESULT_NAME='results/'$1'-'$i'.txt'
	TMP_NAME='results/tmp.txt'
	./memcache-perf/mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $RESULT_NAME
	head -n -2 $RESULT_NAME > $TMP_NAME; mv $TMP_NAME $RESULT_NAME;
	sleep 5
done
#./memcache-perf/mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee test.txt
