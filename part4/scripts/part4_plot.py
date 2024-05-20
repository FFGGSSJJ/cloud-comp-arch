import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone


text_size = 16
ticklabelsize = 16
plt.rcParams['xtick.labelsize'] = ticklabelsize
plt.rcParams['ytick.labelsize'] = ticklabelsize


def parse_time_to_timestamp(time_str):
    dt = datetime.fromisoformat(time_str)
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def process_log_file(log_path):
    events = {}
    core_updates = []
    start_time = 0
    end_time = 0
    lastcore = 0

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
                lastcore = num_cores
                if len(core_updates) == 1:
                    core_updates.insert(0, (0, 4))
    core_updates.append((830,lastcore))

    return events, start_time, end_time, core_updates


def create_custom_color_plot(time, latency, qps, tasks, task_intervals, colors, job_duration, text_size, path, barinterval, changelist, save):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 5),
                                   gridspec_kw={'height_ratios': [9, 2], 'hspace': 0},
                                   sharex=True)

    filtered_time = []
    filtered_latency = []
    filtered_qps = []
    exceeded = False
    for t, l, q in zip(time, latency, qps):
        if t <= 820 or not exceeded:
            filtered_time.append(t)
            filtered_latency.append(l)
            filtered_qps.append(q)
        if t > 820:
            exceeded = True

    filtered_latency = np.array(filtered_latency) / 1000
    filtered_qps = np.array(filtered_qps) / 1000

    ax1b = ax1.twinx()
    ax1b.set_zorder(1)
    ax1.set_zorder(2)
    ax1.patch.set_visible(False)

    bars = ax1b.bar(filtered_time, filtered_qps, width=barinterval, color='lightblue', alpha=0.6, label='QPS [K]', zorder=1)
    ax1b.set_ylabel('QPS [K]', fontsize=text_size)
    if barinterval == 2:
        ax1b.set_ylim(0, 110)
    elif barinterval == 10:
        ax1b.set_ylim(0, 110)

    line, = ax1.plot(filtered_time, filtered_latency, label='P95 Latency [ms]', color='blue', alpha=1, marker='^', zorder=2, linewidth=0.5, markersize=1.5)
    ax1.set_ylabel('P95 Latency [ms]', fontsize=text_size)
    if barinterval == 2:
        ax1.set_ylim(0, max(latency)*1.05/1000)
    elif barinterval == 10:
        ax1.set_ylim(0, 1.1)
    ax1.axhline(y=1, color='grey', linestyle='--', linewidth=1)

    task_order_1 = ['dedup', 'ferret', 'freqmine']
    task_order_2 = ['canneal', 'blackscholes', 'vips', 'radix']

    y_positions = {task: 0.15 if task in task_order_1 else 0.5 for task in tasks}
    bar_height = 0.3

    timelist1 = []
    timelist2 = []
    for task in task_intervals:
        for i in task_intervals[task]:
            if task in task_order_1:
                timelist1.append(i[0])
            else:
                timelist2.append(i[0])
    timelist1.sort()
    timelist2.sort()
    min_interval = 35
    i = 0
    textup1 = []
    textdown1 = []
    textup2 = []
    textdown2 = []
    while (i < len(timelist1)):
        if i < len(timelist1) - 1 and timelist1[i+1] - timelist1[i] < min_interval:
            textup1.append(timelist1[i])
            textdown1.append(timelist1[i+1])
            i += 2
        elif i > 0 and timelist1[i-1] in textdown1 and timelist1[i] - timelist1[i-1] < min_interval:
            textup1.append(timelist1[i])
            i += 1
        elif i > 0 and timelist1[i-1] in textup1 and timelist1[i] - timelist1[i-1] < min_interval:
            textdown1.append(timelist1[i])
            i += 1
        else:
            i += 1
    i = 0
    while (i < len(timelist2)):
        if i < len(timelist2) - 1 and timelist2[i+1] - timelist2[i] < min_interval:
            textup2.append(timelist2[i])
            textdown2.append(timelist2[i+1])
            i += 2
        elif i > 0 and timelist2[i-1] in textdown2 and timelist2[i] - timelist2[i-1] < min_interval:
            textup2.append(timelist2[i])
            i += 1
        elif i > 0 and timelist2[i-1] in textup2 and timelist2[i] - timelist2[i-1] < min_interval:
            textdown2.append(timelist2[i])
            i += 1
        else:
            i += 1
            
    for i, (task, color) in enumerate(zip(tasks, colors)):
        intervals = task_intervals[task]
        y_position = y_positions[task]
        for start, duration in intervals:
            ax2.broken_barh([(start, duration)], (y_position, bar_height), facecolors=color, zorder=1)
            if int(start) in changelist:
                ax2.text(start+2, y_position + (2.8 * bar_height / 4), f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
                pass
            elif start in (textup1 + textup2):
                ax2.text(start, y_position + (2.8 * bar_height / 4), f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
            elif start in (textdown1 + textdown2):
                ax2.text(start, y_position + bar_height / 5, f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
            else:
                ax2.text(start, y_position + bar_height / 2, f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)

    ax2.set_yticks([])
    ax2.set_yticklabels([])
    
    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, marker='^', label='P95 Latency', markerfacecolor='blue', markeredgewidth=0),
        plt.Rectangle((0, 0), 1, 1, color='lightblue', edgecolor='blue', label='QPS')
    ] + [plt.Line2D([0], [0], color=color, lw=4, label=task) for task, color in zip(tasks, colors)]

    legend_elements = legend_elements[:2] + legend_elements[2:][::-1]

    legend = ax1.legend(handles=legend_elements, loc='upper right', framealpha=1, frameon=True, fontsize=text_size)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')

    ax1.tick_params(axis='x', which='both', direction='in', length=4, bottom=True, top=False, labelbottom=False)
    ax2.set_xlabel('Time [s]', fontsize=text_size)
    ax2.xaxis.set_tick_params(which='both', labelbottom=True)
    plt.xlim(left=0, right=1030)
    plt.tight_layout()
    if save == 1:
        plt.savefig(path, dpi=1200)
    else:
        plt.show()
    


def create_custom_color_plot2(time, coresa, coresb, qps, tasks, task_intervals, colors, job_duration, text_size, path, barinterval, changelist, save):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 5),  # Adjusted figure size for better layout
                                   gridspec_kw={'height_ratios': [9, 2], 'hspace': 0},  # Adjusted height ratios for the task bars
                                   sharex=True)

    filtered_time = []
    filtered_qps = []
    exceeded = False
    for t, q in zip(time, qps):
        if t <= 820 or not exceeded:
            filtered_time.append(t)
            filtered_qps.append(q)
        if t > 820:
            exceeded = True

    filtered_qps = np.array(filtered_qps) / 1000

    ax1b = ax1.twinx()
    ax1b.set_zorder(1)  
    ax1.set_zorder(2)  
    ax1.patch.set_visible(False)  

    bars = ax1b.bar(filtered_time, filtered_qps, width=barinterval, color='lightblue',  alpha=0.6, label='QPS [K]', zorder=1)
    ax1b.set_ylabel('QPS [K]', fontsize=text_size)
    ax1b.set_ylim(0, 110)

    line, = ax1.step(coresa, coresb, label='# CPU Cores', color='blue', alpha=1, where='post', zorder=2, linewidth=0.5)
    ax1.set_ylabel('# CPU Cores', fontsize=text_size)
    ax1.set_ylim(0, 5.5)
    # ax1.axhline(y=2, color='grey', linestyle='--', linewidth=1)
    # ax1.axhline(y=4, color='grey', linestyle='--', linewidth=1)

    task_order_1 = ['dedup', 'ferret', 'freqmine']
    task_order_2 = ['canneal', 'blackscholes', 'vips', 'radix']

    y_positions = {task: 0.15 if task in task_order_1 else 0.5 for task in tasks}
    bar_height = 0.3

    timelist1 = []
    timelist2 = []
    for task in task_intervals:
        for i in task_intervals[task]:
            if task in task_order_1:
                timelist1.append(i[0])
            else:
                timelist2.append(i[0])
    timelist1.sort()
    timelist2.sort()
    min_interval = 35
    i = 0
    textup1 = []
    textdown1 = []
    textup2 = []
    textdown2 = []
    while (i < len(timelist1)):
        if i < len(timelist1) - 1 and timelist1[i+1] - timelist1[i] < min_interval:
            textup1.append(timelist1[i])
            textdown1.append(timelist1[i+1])
            i += 2
        elif i > 0 and timelist1[i-1] in textdown1 and timelist1[i] - timelist1[i-1] < min_interval:
            textup1.append(timelist1[i])
            i += 1
        elif i > 0 and timelist1[i-1] in textup1 and timelist1[i] - timelist1[i-1] < min_interval:
            textdown1.append(timelist1[i])
            i += 1
        else:
            i += 1
    i = 0
    while (i < len(timelist2)):
        if i < len(timelist2) - 1 and timelist2[i+1] - timelist2[i] < min_interval:
            textup2.append(timelist2[i])
            textdown2.append(timelist2[i+1])
            i += 2
        elif i > 0 and timelist2[i-1] in textdown2 and timelist2[i] - timelist2[i-1] < min_interval:
            textup2.append(timelist2[i])
            i += 1
        elif i > 0 and timelist2[i-1] in textup2 and timelist2[i] - timelist2[i-1] < min_interval:
            textdown2.append(timelist2[i])
            i += 1
        else:
            i += 1
            
    for i, (task, color) in enumerate(zip(tasks, colors)):
        intervals = task_intervals[task]
        y_position = y_positions[task]
        for start, duration in intervals:
            ax2.broken_barh([(start, duration)], (y_position, bar_height), facecolors=color, zorder=1)
            if int(start) in changelist:
                ax2.text(start+2, y_position + (2.8 * bar_height / 4), f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
                pass
            elif start in (textup1 + textup2):
                ax2.text(start, y_position + (2.8 * bar_height / 4), f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
            elif start in (textdown1 + textdown2):
                ax2.text(start, y_position + bar_height / 5, f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)
            else:
                ax2.text(start, y_position + bar_height / 2, f'{int(start)}s', ha='left', va='center', color='black', zorder=2, fontsize=text_size-4)

    ax2.set_yticks([])
    ax2.set_yticklabels([])

    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, marker='^', label='# CPU Cores', markerfacecolor='blue', markeredgewidth=0),
        plt.Rectangle((0, 0), 1, 1, color='lightblue', edgecolor='blue', label='QPS')
    ] + [plt.Line2D([0], [0], color=color, lw=4, label=task) for task, color in zip(tasks, colors)]

    legend_elements = legend_elements[:2] + legend_elements[2:][::-1]

    legend = ax1.legend(handles=legend_elements, loc='upper right', framealpha=1, frameon=True, fontsize=text_size)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')

    ax1.tick_params(axis='x', which='both', direction='in', length=4, bottom=True, top=False, labelbottom=False)
    ax2.set_xlabel('Time [s]', fontsize=text_size)
    ax2.xaxis.set_tick_params(which='both', labelbottom=True)
    plt.xlim(left=0, right=1030)
    plt.tight_layout()
    if save == 1:
        plt.savefig(path, dpi=1200)
    else:
        plt.show()



# changelist = [214,237,252,255,238,476,447]
changelist = [209]
save = 1

for part in [4]:
    for pathstr3 in [2]:
        if part == 3:
            output_path = 'results/results_part4_3/v3/'
            pathstr2 = ''
        elif part == 4:
            output_path = 'results/results_part4_4/interval_2/'
            pathstr2 = ''

        log_path = output_path + 'logs/job_' + str(pathstr3) + '.txt'
        results_path = output_path + 'results/result' + pathstr2 + '_' + str(pathstr3) + '.txt'

        plot_path1 = 'plots/' + str(3 * part - 8 + pathstr3) + '0.png'
        plot_path2 = 'plots/' + str(3 * part - 8 + pathstr3) + '1.png'

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
        if part == 3:
            interval = 10
        elif part == 4:
            interval = 2
        time = np.linspace(start - start_time, start - start_time + (len(p95) - 1) * interval, len(p95))
        tasks = np.array(['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'radix', 'vips'])[::-1]
        colors = np.array(['#CCA000', '#CCCCAA', '#CCACCA', '#AACCCA', '#0CCA00', '#00CCA0', '#CC0A00'])[::-1]

        create_custom_color_plot(time, p95, qps, tasks, task_intervals, colors, end_time - start_time, text_size, plot_path1, interval, changelist, save)
        create_custom_color_plot2(time, coresa, coresb, qps, tasks, task_intervals, colors, end_time - start_time, text_size, plot_path2, interval, changelist, save)

