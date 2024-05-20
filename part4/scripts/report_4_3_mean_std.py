import datetime
import numpy as np
import os

def parse_time(log_line):
    # Parse the datetime from log entry
    timestamp_str = log_line.split()[0]
    return datetime.datetime.fromisoformat(timestamp_str)

def process_file(filename):
    start_times = {}
    end_times = {}
    with open(filename, 'r') as file:
        for line in file:
            if 'start' in line:
                job_name = line.split()[2]
                start_times[job_name] = parse_time(line)
            elif 'end' in line:
                job_name = line.split()[2]
                end_times[job_name] = parse_time(line)
    
    # Calculate execution times and makespan
    execution_times = {}
    for job, start_time in start_times.items():
        if job in end_times:
            execution_times[job] = (end_times[job] - start_time).total_seconds()

    if start_times and end_times:
        overall_start = min(start_times.values())
        overall_end = max(end_times.values())
        makespan = (overall_end - overall_start).total_seconds()
    else:
        makespan = None
    
    return execution_times, makespan

# Directory containing results
results_dir = './results/results_part4_3/v2/logs'
files = ['job_0.txt', 'job_1.txt', 'job_2.txt']

all_execution_times = []
all_makespans = []

# Process each file
for filename in files:
    file_path = os.path.join(results_dir, filename)
    execution_times, makespan = process_file(file_path)
    all_execution_times.append(execution_times)
    all_makespans.append(makespan)

# Calculate averages and standard deviations for execution times
job_names = all_execution_times[0].keys()
average_times = {}
std_dev_times = {}

for job in job_names:
    times = [execution_times[job] for execution_times in all_execution_times if job in execution_times]
    average_times[job] = np.mean(times)
    std_dev_times[job] = np.std(times)

# Calculate average and standard deviation for makespan
average_makespan = np.mean(all_makespans)
std_dev_makespan = np.std(all_makespans)

print("Average Execution Times:", average_times)
print("Standard Deviation of Execution Times:", std_dev_times)
print("Average Makespan:", average_makespan)
print("Standard Deviation of Makespan:", std_dev_makespan)
