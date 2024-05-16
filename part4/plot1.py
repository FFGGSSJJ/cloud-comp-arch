import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone

def parse_time_to_timestamp(time_str):
    dt = datetime.fromisoformat(time_str)
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def process_log_file(log_path):
    events = {}
    core_updates = []
    start_time = 0
    end_time = 0

    with open(log_path, 'r') as file:
        for line in file:
            parts = line.split()
            if not parts:
                continue
            current_time_stamp = parse_time_to_timestamp(parts[0])

            if 'start' in parts[1] and 'scheduler' in parts[2]:
                start_time = current_time_stamp
                continue
            if 'end' in parts[1] and 'scheduler' in parts[2]:
                end_time = current_time_stamp
                continue
            
            command = parts[1]
            job_name = (parts[2].replace('parsec_', '')).replace('splash2x_', '')

            if command in ['start', 'unpause']:
                if job_name not in events:
                    events[job_name] = []
                job_go = current_time_stamp - start_time
                events[job_name].append(job_go)

            elif command in ['end', 'pause']:
                if job_name in events:
                    job_go = events[job_name].pop()
                    job_stop = current_time_stamp - start_time
                    duration = job_stop - job_go
                    events[job_name].append((job_go, duration))

            elif command == 'update_cores' and job_name == 'memcached':
                update_time = current_time_stamp - start_time
                cores_list = eval(parts[3])
                num_cores = len(cores_list)
                core_updates.append((update_time, num_cores))

    return events, start_time, end_time, core_updates



def create_custom_color_plot(time, latency, qps, tasks, task_intervals, colors, job_duration):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 5), 
                                   gridspec_kw={'height_ratios': [12, 1], 'hspace': 0}, 
                                   sharex=True)

    filtered_time = []
    filtered_latency = []
    filtered_qps = []
    exceeded = False
    for t, l, q in zip(time, latency, qps):
        if t <= job_duration or not exceeded:
            filtered_time.append(t)
            filtered_latency.append(l)
            filtered_qps.append(q)
        if t > job_duration:
            exceeded = True

    filtered_latency = np.array(filtered_latency) / 1000
    filtered_qps = np.array(filtered_qps) / 1000

    ax1b = ax1.twinx()
    ax1b.set_zorder(1)  
    ax1.set_zorder(2)  
    ax1.patch.set_visible(False)  

    bars = ax1b.bar(filtered_time, filtered_qps, width=10, color='lightblue', edgecolor='blue', alpha=0.6, label='QPS [K]', zorder=1)
    ax1b.set_ylabel('QPS [K]')
    ax1b.set_ylim(0, max(filtered_latency) * 110)

    line, = ax1.plot(filtered_time, filtered_latency, label='P95 Latency [ms]', color='blue', alpha=1, marker='^', zorder=2)
    ax1.set_ylabel('P95 Latency [ms]')
    ax1.set_ylim(0, max(filtered_latency) * 1.1)
    ax1.axhline(y=1, color='grey', linestyle='--', linewidth=1)

    for i, (task, color) in enumerate(zip(tasks, colors)):
        intervals = task_intervals[task]
        for start, duration in intervals:
            ax2.broken_barh([(start, duration)], (0.25, 0.5), facecolors=color, zorder=1)
            ax2.text(start, 0.5, f'{int(start)}s', ha='left', va='center', color='black', zorder=2)

    ax2.set_yticks([])
    ax2.set_yticklabels([])

    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, marker='^', label='P95 Latency', markerfacecolor='blue', markeredgewidth=0),
        plt.Rectangle((0, 0), 1, 1, color='lightblue', edgecolor='blue', label='QPS')
    ] + [plt.Line2D([0], [0], color=color, lw=4, label=task) for task, color in zip(tasks, colors)]

    legend_elements = legend_elements[:2] + legend_elements[2:][::-1]

    legend = ax1.legend(handles=legend_elements, loc='upper right', framealpha=1, frameon=True)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')

    ax1.tick_params(axis='x', which='both', direction='in', length=4, bottom=True, top=False, labelbottom=False)
    ax2.set_xlabel('Time [s]')
    ax2.xaxis.set_tick_params(which='both', labelbottom=True)
    plt.xlim(left=0, right=job_duration*1.15)
    plt.tight_layout()
    plt.show()


def create_custom_color_plot2(time, coresa, coresb, qps, tasks, task_intervals, colors, job_duration):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 5), 
                                   gridspec_kw={'height_ratios': [12, 1], 'hspace': 0}, 
                                   sharex=True)

    filtered_time = []
    filtered_qps = []
    exceeded = False
    for t, q in zip(time, qps):
        if t <= job_duration or not exceeded:
            filtered_time.append(t)
            filtered_qps.append(q)
        if t > job_duration:
            exceeded = True

    filtered_qps = np.array(filtered_qps) / 1000

    ax1b = ax1.twinx()
    ax1b.set_zorder(1)  
    ax1.set_zorder(2)  
    ax1.patch.set_visible(False)  

    bars = ax1b.bar(filtered_time, filtered_qps, width=10, color='lightblue', edgecolor='blue', alpha=0.6, label='QPS [K]', zorder=1)
    ax1b.set_ylabel('QPS [K]')
    ax1b.set_ylim(0, 110)

    line, = ax1.step(coresa, coresb, label='# CPU Cores', color='blue', alpha=1, where='post', zorder=2)
    ax1.set_ylabel('# CPU Cores')
    ax1.set_ylim(0, 5.5)
    ax1.axhline(y=2, color='grey', linestyle='--', linewidth=1)
    ax1.axhline(y=4, color='grey', linestyle='--', linewidth=1)

    for i, (task, color) in enumerate(zip(tasks, colors)):
        intervals = task_intervals[task]
        for start, duration in intervals:
            ax2.broken_barh([(start, duration)], (0.25, 0.5), facecolors=color, zorder=1)
            ax2.text(start, 0.5, f'{int(start)}s', ha='left', va='center', color='black', zorder=2)

    ax2.set_yticks([])
    ax2.set_yticklabels([])

    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, marker='^', label='# CPU Cores', markerfacecolor='blue', markeredgewidth=0),
        plt.Rectangle((0, 0), 1, 1, color='lightblue', edgecolor='blue', label='QPS')
    ] + [plt.Line2D([0], [0], color=color, lw=4, label=task) for task, color in zip(tasks, colors)]

    legend_elements = legend_elements[:2] + legend_elements[2:][::-1]

    legend = ax1.legend(handles=legend_elements, loc='upper right', framealpha=1, frameon=True)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')

    ax1.tick_params(axis='x', which='both', direction='in', length=4, bottom=True, top=False, labelbottom=False)
    ax2.set_xlabel('Time [s]')
    ax2.xaxis.set_tick_params(which='both', labelbottom=True)
    plt.xlim(left=0, right=job_duration*1.15)
    plt.tight_layout()
    plt.show()



output_path = 'results/results_part4_3/'
log_path = output_path + 'logs/job_2.txt'
results_path = output_path + 'results/result_2.txt'

p95 = []
qps = []
with open(results_path, 'r') as file:
    for line in file:
        if line.startswith('read'):
            parts = line.split()
            if len(parts) >= 17:
                p95.append(float(parts[12]))
                qps.append(float(parts[16]))

        elif line.startswith("Timestamp start:"):
            parts = line.split()
            if len(parts) > 2:
                start = float(parts[2])/1000

        elif line.startswith("Timestamp end:"):
            parts = line.split()
            if len(parts) > 2:
                duration_time = float(parts[2])/1000 - start

p95 = np.array(p95)
qps = np.array(qps)

task_intervals, start_time, end_time, cores = process_log_file(log_path)
coresa = []
coresb = []
for i in cores:
    coresa.append(i[0])
    coresb.append(i[1])

time = np.linspace(start - start_time, start - start_time + (len(p95) - 1) * 10, len(p95))
tasks = np.array(['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'radix', 'vips'])[::-1]
colors = np.array(['#CCA000', '#CCCCAA', '#CCACCA', '#AACCCA', '#0CCA00', '#00CCA0', '#CC0A00'])[::-1]


create_custom_color_plot(time, p95, qps, tasks, task_intervals, colors, end_time - start_time)
create_custom_color_plot2(time, coresa, coresb, qps, tasks, task_intervals, colors, end_time - start_time)
