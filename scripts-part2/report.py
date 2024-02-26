import csv
import sys
import matplotlib.pyplot as plt
import numpy as np

test_array = ['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'radix', 'vips']
ibench_array = ['none', 'cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw']
result_dir_path = './results'

# calculate the real time
def conv_time(part, testName):
    time_array = []
    with open(result_dir_path+'-'+part+'/parsec-'+testName+'.txt', 'r') as testtxt:
        testreader = csv.reader(testtxt)

        for row in testreader:
            time_str = row[0].split('\t')[1]
            m = time_str.split('m')[0]
            s = time_str.split('m')[1][:-1]
            time_array.append(60*float(m)+float(s))

    return time_array

# format print the result
def show_rate(rateMat):
    print('\t\t', end="")
    for ibench in ibench_array:
        print(ibench, end='\t')
    print('')
    for i in range(len(test_array)):
        if test_array[i] == 'blackscholes' or test_array[i] == 'freqmine':
            print(test_array[i], end="\t")
        else:
            print(test_array[i], end="\t\t")
        for rate in rateMat[i]:
            print(round(rate, 3), end='\t')
        print('')

# plot normalized time vs threads
def plot_time_thread(rateMat):
    threads = np.array(['1','2','4','8'])

    for i in range(len(test_array)):
        linestyle = {"linestyle":"--", "linewidth":0.7, "marker":"o"}
        plt.plot(threads, rateMat[i], label=test_array[i], **linestyle)
    
    # set axis labels
    plt.xlabel("Threads Number")
    plt.ylabel("Normalized Time")
    plt.xticks(threads)
    plt.yticks(np.linspace(0, 1, 9))

    plt.legend()
    plt.savefig('./part2b.png')
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        exit
    
    time_mat = []
    rate_mat = []
    part = sys.argv[1]

    for test in test_array:
        time_mat.append(conv_time(part, test))
    time_mat = np.array(time_mat)

    # normalize
    for row in time_mat:
        row = row/row[0]
        rate_mat.append(row)
    rate_mat = np.array(rate_mat)

    if part == 'a':
        show_rate(rate_mat)
    else:
        plot_time_thread(rate_mat)
    
    