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

##### result

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

