## part3

For part3, we are supposed to design an static interference-aware scheduling policy to run latency-critical and batch applications. 



#### Work plan (2024.04.01 - 2024.04.17)

- [ ] fork your own branch for test

- [ ] problems for reference:

  - [ ] Which machine to deploy `memcached`

  - [ ] What batch applications can be colocated with `memcached` 

  - [ ] What batch applications can be colocated together in the same machine
    - [ ] Which order to execute batch applications
    - [ ] How to allocate resources in different machines for different applications