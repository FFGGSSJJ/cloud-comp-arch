## scripts-part1

#### **Usage:**

- `mcperf-compile.sh`: script for compiling `mcperf` on ***agent*** and ***measure*** VM machines

  - it is copied from part1 instructions, follow the instructions first

- `mctest-0.sh`: script for automatically running tests and collecting datasets in ***measure*** VM machine

  - before using:
    - set up `MEMCACHED_IP` and `INTERNAL_AGENT_IP` env variables correctly
  - after deploying corresponding ibench pod:
    - `./mctest-0.sh <test name>`
    - i.e.: `./mctest-0.sh cpu` for ibench-cpu

- `local.sh`: script for local machine that will automatically download data sets from ***measure*** node machine

  - before using:
    - set up `GCLOUD_SSH` env variable as your SSH key path
    - modify the corresponding ***measure*** machine name
  - after all measurements finish: 
    - `./local.sh`

  