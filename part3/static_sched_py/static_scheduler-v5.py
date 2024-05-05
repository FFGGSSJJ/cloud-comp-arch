import subprocess
import json

'''
Delete the parsec jobs.
'''
def delete_jobs_all():
    command = "kubectl delete jobs --all"
    subprocess.run(command.split(" "))

def delete_jobs():
    jobs = ["parsec-dedup", "parsec-vips", "parsec-radix", "parsec-canneal", "parsec-blackscholes", 
            "parsec-freqmine", "parsec-ferret"] #get_jobs()

    if len(jobs) == 0:
        print("No previous jobs to delete")
        return

    deleteJobsStatement = "kubectl delete job {}"
    for job in jobs:
        print(f"Deleting job {job}")
        subprocess.run(deleteJobsStatement.format(job).split(" "))

'''
This code statically schedules the 6 parsec benchmarks dedup, blackscholes,
ferret, freqmine, canneal and fft while ensuring the memcached SLAs of 2ms < response times
at 30k QPS for 95% of all requests.

This code should be run in the top most folder of the project or the location variable for the parsec benchmarks
should be updated appropriately.
'''
# Clean up - Delete any parsec jobs before starting execution
# delete_jobs()
delete_jobs_all()

# Schedule jobs
location = "../config/parsec-benchmarks/part3/v5/" # Change this variable to proper location if necessary.
 
# vm2jobs = ["parsec-blackscholes.yaml"]
# vm4jobs = ["parsec-dedup.yaml", "parsec-vips.yaml", "parsec-radix.yaml", "parsec-freqmine.yaml"]
# vm8jobs = ["parsec-canneal.yaml", "parsec-ferret.yaml"]

# vm2jobs = ["parsec-blackscholes.yaml"]
# vm4jobs = ["parsec-dedup.yaml", "parsec-vips.yaml", "parsec-freqmine.yaml"]
# vm8jobs = ["parsec-canneal.yaml", "parsec-radix.yaml", "parsec-ferret.yaml"]

vm2jobs = ["parsec-vips.yaml"]
vm4jobs = ["parsec-blackscholes.yaml", "parsec-freqmine.yaml"]
vm8jobs = ["parsec-dedup.yaml", "parsec-canneal.yaml", "parsec-radix.yaml", "parsec-ferret.yaml"]
command = "kubectl create -f {}{}"

print("Started scheduling jobs")

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