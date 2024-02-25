import csv
import numpy as np

test_array = ['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'radix', 'vips']
ibench_array = ['cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw', 'none']
result_dir_path = './results/'


def conv_time(testName):
    time_array = []
    with open(result_dir_path+'parsec-'+testName+'.txt', 'r') as testtxt:
        testreader = csv.reader(testtxt)

        for row in testreader:
            time_str = row[0].split('\t')[1]
            m = time_str.split('m')[0]
            s = time_str.split('m')[1][:-1]
            time_array.append(60*float(m)+float(s))

    return time_array


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


if __name__ == '__main__':
    time_mat = []
    rate_mat = []

    for test in test_array:
        time_mat.append(conv_time(test))
    time_mat = np.array(time_mat)

    for row in time_mat:
        row = row/row[-1]
        rate_mat.append(row)
    rate_mat = np.array(rate_mat)
    show_rate(rate_mat)
    
    