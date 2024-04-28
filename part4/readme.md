### Part4

#### Usage

- `mcperf-compile.sh`: compile the mcperf in VMs
- `setup_memcached.sh`: setup memcached related env in VM
- `trans_fiiles.sh`: upload/download files between local machine and VMs
  - `./trans_files.sh <up/down> <FILEs>`
- `auto_sync.sh`: MacOS only. Automatically synchronize folder between local and VM
  - for linux based machine, use `inotify`