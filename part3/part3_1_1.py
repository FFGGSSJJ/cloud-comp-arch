import re
from statistics import mean, stdev, pstdev

# Define the list of file paths
file_paths = [
    'results_batch_jobs_txt/pods_1.txt',
    'results_batch_jobs_txt/pods_2.txt',
    'results_batch_jobs_txt/pods_3.txt'
]

# Dictionary to store job times for each job type
job_times = {}

# Function to convert time in "HH:MM:SS" format to seconds
def time_to_seconds(t):
    h, m, s = map(int, t.split(':'))
    return h * 3600 + m * 60 + s

# Loop through each file to extract data
for path in file_paths:
    with open(path, 'r') as file:
        data = file.read()
    
    # Use regular expression to match both "Job time" and "Total time"
    pattern = r"Job: +(\w+[\w-]*)\s+(?:Job time|Total time): +(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, data)
    
    # Store each match in the dictionary
    for job, time in matches:
        seconds = time_to_seconds(time)
        if job not in job_times:
            job_times[job] = []
        job_times[job].append(seconds)

# Calculate the average time and standard deviation for each job type
for job, times in job_times.items():
    avg_time = mean(times)

    # Population Standard Deviation
    pop_std_dev = pstdev(times)  
    print(f"Job: {job}, Average Time: {avg_time:.2f} seconds, Standard Deviation: {pop_std_dev:.2f} seconds")

    # # Sample Standard Deviation
    # std_dev = stdev(times)
    # print(f"Job: {job}, Average Time: {avg_time:.2f} seconds, Standard Deviation: {std_dev:.2f} seconds")
