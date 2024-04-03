## part3

For part3, we are supposed to design an static interference-aware scheduling policy to run latency-critical and batch applications. 



### Scheme v1

- `node-a-2core`: 
  - memcached only
  - high cpu node with 2 cores. Deploy  `memcached` and an application that can be safely colocated to guarantee SLO
- `node-b-4core`:
  - dedup --> vips + radix --> blackscholes + canneal (2 cores each)
- `node-c-8core`:
  - freqmine (130s on node-c w/ all resources) --> feret

##### result v1

```
schedule node b
schedule node c
job.batch/parsec-freqmine created
job.batch/parsec-dedup created
job.batch/parsec-dedup condition met
job.batch/parsec-vips created
job.batch/parsec-radix created
job.batch/parsec-radix condition met
job.batch/parsec-vips condition met
job.batch/parsec-canneal created
job.batch/parsec-blackscholes created
job.batch/parsec-blackscholes condition met
job.batch/parsec-freqmine condition met
job.batch/parsec-ferret created
job.batch/parsec-canneal condition met
job.batch/parsec-ferret condition met
done
./scheduler.sh  0.99s user 0.32s system 0% cpu 3:37.32 total
```

```
Job:  parsec-blackscholes
Job time:  0:00:46
Job:  parsec-canneal
Job time:  0:01:34
Job:  parsec-dedup
Job time:  0:00:18
Job:  parsec-ferret
Job time:  0:01:21
Job:  parsec-freqmine
Job time:  0:02:08
Job:  parsec-radix
Job time:  0:00:18
Job:  parsec-vips
Job time:  0:00:37
Job:  memcached
Total time: 0:03:33
```

