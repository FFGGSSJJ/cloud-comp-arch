import json
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from datetime import datetime

def timestamp_to_seconds(timestamp):
    # Convert full timestamp in the format 'YYYY-MM-DDTHH:MM:SSZ' to seconds past midnight
    time_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    return total_seconds

# Define the list of file paths
json_file_paths = [
    'part_3_results_group_088/last_results/pods_1.json',
    'part_3_results_group_088/last_results/pods_2.json',
    'part_3_results_group_088/last_results/pods_3.json'
]

txt_file_paths = [
    'part_3_results_group_088/mcperf_1.txt',
    'part_3_results_group_088/mcperf_2.txt',
    'part_3_results_group_088/mcperf_3.txt'
]

colors = {
    'blackscholes': '#CCA000',
    'canneal': '#CCCCAA',
    'dedup': '#CCACCA',
    'ferret': '#AACCCA',
    'freqmine': '#0CCA00',
    'radix': '#00CCA0',
    'vips': '#CC0A00'
}

for i in range(3):
    with open(json_file_paths[i], 'r') as file:
        pods_json = json.load(file)

    pods = {}
    j = 0 
    for item in pods_json['items']:
        if j < 7:
            job_name = item['metadata']['labels']['job-name']
            job_name = job_name.split('-')[-1]

            for containerstatus in item['status']['containerStatuses']:
                startedAt = containerstatus['state']['terminated']['startedAt']
                startedAt = timestamp_to_seconds(startedAt)
                finishedAt = containerstatus['state']['terminated']['finishedAt']
                finishedAt = timestamp_to_seconds(finishedAt)

            node = item['spec']['nodeName'].split('-')[-2]
            node = 'VM-' + node

            pods[job_name] = {'startedAt': startedAt, 'finishedAt': finishedAt, 'node': node}

            if j ==0:
                startedAt_min = startedAt
                finishedAt_max = finishedAt
            else: 
                if startedAt < startedAt_min:
                    startedAt_min = startedAt
                if finishedAt > finishedAt_max:
                    finishedAt_max = finishedAt

            j = j + 1
    
    for job, times in pods.items():
        times['startedAt'] = times['startedAt'] - startedAt_min
        times['finishedAt'] = times['finishedAt'] - startedAt_min
        # print(f"{job}: Starts at {times['startedAt']}, Finishes at {times['finishedAt']}")
    print(pods)

    keys_order = ['blackscholes', 'vips', 'freqmine', 'dedup', 'radix', 'ferret', 'canneal']
    keys_order = ['blackscholes', 'vips', 'freqmine', 'radix', 'ferret', 'dedup', 'canneal']
    ordered_pods = {}
    for ordered_job in keys_order:
        ordered_pods[ordered_job] = pods[ordered_job]
    pods = ordered_pods

    mcperf = pd.read_csv(txt_file_paths[i], sep='\s+')
    selected_columns = mcperf[['p95', 'ts_start', 'ts_end']]
    selected_columns = selected_columns.head(20)

    first_ts_start = selected_columns['ts_start'].iloc[0]

    selected_columns['p95'] = selected_columns['p95'] / 1000 # Convert us to ms
    selected_columns['ts_start'] = selected_columns['ts_start'] - first_ts_start
    selected_columns['ts_start'] = selected_columns['ts_start'] / 1000 # Convert millisecond to second
    selected_columns['ts_end'] = selected_columns['ts_end'] - first_ts_start
    selected_columns['ts_end'] = selected_columns['ts_end'] / 1000 # Convert millisecond to second

    last_ts_end = selected_columns['ts_end'].iloc[19]
    print(selected_columns)

    # Set the general font of plots to Times New Roman
    # Set the general font of plots to Times New Roman
    mpl.rcParams['font.family'] = 'Times New Roman'
    mpl.rcParams['font.weight'] = 'bold'

    # Plot the Latency figure
    bar_centers = (selected_columns['ts_start'] + selected_columns['ts_end']) / 2
    bar_widths = selected_columns['ts_end'] - selected_columns['ts_start']

    plt.figure(figsize=(10, 2))
    plt.bar(bar_centers, selected_columns['p95'], width=bar_widths, color='#FF8884', edgecolor='none')

    plt.xlabel('Time (s)', fontweight='bold', fontsize=12, fontname='Times New Roman')
    plt.ylabel('p95 Latency (ms)', fontweight='bold', fontsize=12, fontname='Times New Roman')
    # plt.title('p95 Latency Over Time_Run{}'.format(i+1), fontweight='bold', fontsize=16, fontname='Times New Roman')

    # Adjust tick labels to be bold and Times New Roman
    plt.xticks(fontweight='bold', fontsize=12, fontname='Times New Roman')
    plt.yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], fontweight='bold', fontsize=12, fontname='Times New Roman')

    plt.xlim(0, 220)
    plt.grid(False)

    plt.tight_layout()
    plt.savefig('./part3_1_figures/LatencyOverTime_Run{}.png'.format(i+1), dpi=1200)
    plt.show()

    # Plot the batch jobs figure
    job_names = list(pods.keys())
    starts = [job['startedAt'] for job in pods.values()]
    ends = [job['finishedAt'] for job in pods.values()]
    durations = [end - start for start, end in zip(starts, ends)]
    nodes = [job['node'] for job in pods.values()]

    fig, ax = plt.subplots(figsize=(10, 2))

    for job_name, duration, start, node in zip(job_names, durations, starts, nodes):
        ax.barh(job_name, duration, left=start, color=colors[job_name], edgecolor='none')
        ax.text(start + duration + 4, job_name, node, va='center', fontweight='bold', fontsize=12, fontname='Times New Roman')  

    ax.set_xlabel('Time (s)', fontweight='bold', fontsize=12, fontname='Times New Roman')
    ax.set_ylabel('Job Name', fontweight='bold', fontsize=12, fontname='Times New Roman')
    # ax.set_title('Batch Job Execution Timeline_Run{}'.format(i+1), fontweight='bold', fontsize=16, fontname='Times New Roman')

    ax.tick_params(axis='both', labelsize=12, labelfontfamily='Times New Roman', labelcolor='black')
    ax.set_xlim(0, 220)  

    plt.tight_layout()
    plt.savefig('./part3_1_figures/Batch Job Execution Timeline_Run{}.png'.format(i+1), dpi=1200)
    plt.show()

    # mpl.rcParams['font.family'] = 'Times New Roman'
    # mpl.rcParams['font.weight'] = 'bold'

    # # Plot the Latency figure
    # bar_centers = (selected_columns['ts_start'] + selected_columns['ts_end']) / 2
    # bar_widths = selected_columns['ts_end'] - selected_columns['ts_start']

    # plt.figure(figsize=(10, 2))
    # plt.bar(bar_centers, selected_columns['p95'], width=bar_widths, color='#FF8884', edgecolor='none')

    # plt.xlabel('Time (s)', fontweight='bold', fontsize=14, fontname='Times New Roman')
    # plt.ylabel('p95 Latency (ms)', fontweight='bold', fontsize=14, fontname='Times New Roman')
    # # plt.title('p95 Latency Over Time_Run{}'.format(i+1), fontweight='bold', fontsize=16, fontname='Times New Roman')

    # # Adjust tick labels to be bold and Times New Roman
    # plt.xticks(fontweight='bold', fontsize=12, fontname='Times New Roman')
    # plt.yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], fontweight='bold', fontsize=12, fontname='Times New Roman')

    # plt.xlim(0, 220)
    # plt.grid(False)

    # plt.savefig('./part3_1_figures/LatencyOverTime_Run{}.png'.format(i+1), dpi=1200)
    # plt.show()

    # # Plot the batch jobs figure
    # job_names = list(pods.keys())
    # starts = [job['startedAt'] for job in pods.values()]
    # ends = [job['finishedAt'] for job in pods.values()]
    # durations = [end - start for start, end in zip(starts, ends)]
    # nodes = [job['node'] for job in pods.values()]

    # fig, ax = plt.subplots(figsize=(10, 2))

    # for job_name, duration, start, node in zip(job_names, durations, starts, nodes):
    #     ax.barh(job_name, duration, left=start, color=colors[job_name], edgecolor='none')
    #     ax.text(start + duration + 4, job_name, node, va='center', fontweight='bold', fontsize=12, fontname='Times New Roman')  

    # ax.set_xlabel('Time (s)', fontweight='bold', fontsize=14, fontname='Times New Roman')
    # ax.set_ylabel('Job Name', fontweight='bold', fontsize=14, fontname='Times New Roman')
    # # ax.set_title('Batch Job Execution Timeline_Run{}'.format(i+1), fontweight='bold', fontsize=16, fontname='Times New Roman')

    # ax.tick_params(axis='both', labelsize=12, labelfontfamily='Times New Roman', labelcolor='black')
    # ax.set_xlim(0, 220)  

    # plt.savefig('./part3_1_figures/Batch Job Execution Timeline_Run{}.png'.format(i+1), dpi=1200)
    # plt.show()
