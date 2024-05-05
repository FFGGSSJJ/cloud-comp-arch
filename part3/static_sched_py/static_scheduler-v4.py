import subprocess
import json
import time


# Delete the parsec jobs one each time
def delete_jobs_all():
    command = "kubectl delete jobs --all"
    subprocess.run(command.split(" "))

# Delete all the parsec jobs
def delete_jobs():
    jobs = ["parsec-dedup", "parsec-vips", "parsec-radix", "parsec-canneal", "parsec-blackscholes", 
            "parsec-freqmine", "parsec-ferret"]

    if len(jobs) == 0:
        print("All previous jobs have been deleted")
        return

    deleteJobsStatement = "kubectl delete job {}"
    for job in jobs:
        print(f"Deleting job {job}")
        subprocess.run(deleteJobsStatement.format(job).split(" "))

'''
The code below statically schedules the 7 parsec benchmarks dedup, blackscholes,vips, radix, 
canneal, ferret, and freqmine in VM2, VM4, and VM8 while ensuring the SLO for memcached of less 
than 1 ms 95th percentile latency at 30K QPS.
'''

# Delete any parsec jobs before starting next execution
delete_jobs_all()

# Schedule jobs
location = "../config/parsec-benchmarks/part3/v4/" # Change this variable to proper location if necessary

# vm2jobs = ["parsec-blackscholes.yaml"]
# vm4jobs = ["parsec-dedup.yaml", "parsec-vips.yaml", "parsec-radix.yaml", "parsec-freqmine.yaml"]
# vm8jobs = ["parsec-canneal.yaml", "parsec-ferret.yaml"]

# vm2jobs = ["parsec-blackscholes.yaml"]
# vm4jobs = ["parsec-dedup.yaml", "parsec-vips.yaml", "parsec-freqmine.yaml"]
# vm8jobs = ["parsec-canneal.yaml", "parsec-radix.yaml", "parsec-ferret.yaml"]

vm2jobs = ["parsec-blackscholes.yaml"]
vm4jobs = ["parsec-vips.yaml", "parsec-freqmine.yaml"]
vm8jobs = ["parsec-dedup.yaml", "parsec-canneal.yaml", "parsec-radix.yaml", "parsec-ferret.yaml"]
command = "kubectl create -f {}{}"

print("Started scheduling jobs")

# Schedule VM2
for job in vm2jobs:
    subprocess.run(command.format(location, job).split(" "))

# Freqmine is a CPU intensive task too, so, it cannot be collocated with Ferret.
# Blackscholes and FFT do not intere with each other considerably, so, they are collocated and share equal amounts
# of CPU. FFT is a memory intensive task and VM B has limited RAM. In order to prevent job from crashing, we limit
# the amount of RAM FFT job can use.
# Schedule VM4
for job in vm4jobs:
    subprocess.run(command.format(location, job).split(" "))

# Ferret is a CPU intensive job, so, we allocate 6 CPUs to it.
# Canneal doesn't scale very well, so, we only allocate 2 CPUs to it.
# Canneal and Ferret end around the same time and Dedup scales well up to 4 threads, so, we allocate 4 CPUs to it.
# Schedule VM8
for job in vm8jobs:
    subprocess.run(command.format(location, job).split(" "))

print("Completed scheduling jobs")

command = "kubectl get pods"
subprocess.run(command.split(" "))
