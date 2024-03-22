import csv
import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
from matplotlib.patches import ConnectionPatch

test_array = ['nointerference', 'cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw']
color_array= ['#BB9727', '#F87970', '#32B897', '#05B9E2', '#8983BF', '#FF9646', '#C76DA2']
result_dir_path = './results/'

# turn txt file into csv file
def txt2csv():
    for test in test_array:
        for i in range(1, 4):
            fields_row = []
            data_rows = []
            with open(result_dir_path+test+'-'+str(i)+'.txt', 'r') as testtxt:
                # create reader obj
                csvreader = csv.reader(testtxt)

                # get the fields using first row
                fields_str = next(csvreader)
                fields_row = fields_str[0].split()

                # get data
                for row_str in csvreader:
                    row = row_str[0].split()
                    data_rows.append(row)

                # turn into csv
                fileName = result_dir_path+test+'-'+str(i)+'.csv'
                with open(fileName, 'w', newline = '') as out_file:
                    writer = csv.writer(out_file)
                    writer.writerow(fields_row)
                    writer.writerows(data_rows)
                    out_file.close()
                testtxt.close()

# calculate avg value from 3 tests
def calculate_avg(test):
    testAvg = np.zeros((11,17))

    for i in range(1,4):
        with open(result_dir_path+test+'-'+str(i)+'.csv', 'r') as testcsv:
            # create reader obj
            csvreader = csv.reader(testcsv)

            field = next(csvreader)
            testCurr = []
            for row in csvreader:
                rowFloat = [float(k) for k in row[1:]]
                testCurr.append(rowFloat)
 
            testAvg += np.array(testCurr)
            testcsv.close()
    return testAvg/3

# calculate err by standard deviation
def calculate_err(test):
    errStd = []

    for i in range(1,4):
        with open(result_dir_path+test+'-'+str(i)+'.csv', 'r') as testcsv:
            # create reader obj
            csvreader = csv.reader(testcsv)

            field = next(csvreader)
            testCurr = []
            for row in csvreader:
                rowFloat = [float(k) for k in row[1:]]
                testCurr.append(rowFloat)
            
            errStd.append(testCurr)
            testcsv.close()
    return np.array(errStd).std(axis=0)

# plot required figure
def plot_qps_p95(testAvgDataSets, testErrSets):
    p95_id = 11
    qps_id = 15

    # set axis limit
    plt.xlim(0, 55000)
    plt.xticks(np.linspace(0, 55000, 12), np.array(['0k', '5k', '10k', '15k', '20k', '25k', '30k', '35k', '40k', '45k', '50k', '55k']))
    plt.ylim(0, 9)

    # set axis labels
    plt.xlabel("QPS")
    plt.ylabel("P95 in ms")

    # plot lines and err bars
    for i in range(len(test_array)):
        xaxis = [testDataRow[qps_id] for testDataRow in testAvgDataSets[i]]
        yaxis = [testDataRow[p95_id]/1000 for testDataRow in testAvgDataSets[i]]

        xerrs = [testErrRow[qps_id] for testErrRow in testErrSets[i]]
        yerrs = [testErrRow[p95_id]/1000 for testErrRow in testErrSets[i]]

        # plt.plot(xaxis, yaxis, label=test_array[i], linestyle='-')
        linestyle = {"linestyle":"--", "linewidth":1.5, "markeredgewidth":2, "elinewidth":0.4, "capsize":1}
        plt.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])
    
    plt.grid(ls='-.', lw = 0.5, color = "#4E616C")
    plt.legend()
    plt.savefig('./part1-fig.png', dpi=1200)
    plt.show()

def plot_qps_p95_local_zoom(testAvgDataSets, testErrSets):
    p95_id = 11
    qps_id = 15

    # set axis limit
    fig, ax = plt.subplots(1, 1)

    ax.set_xlim(0, 55e3)
    ax.set_ylim(0, 9)

    ax.set_xticks([0, 5e3, 10e3, 15e3, 20e3, 25e3, 30e3, 35e3, 40e3, 45e3, 50e3, 55e3])
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    ax.set_xticklabels(['0k', '5k', '10k', '15k', '20k', '25k', '30k', '35k', '40k', '45k', '50k', '55k'])
    ax.set_yticklabels(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

    # set legend and axis labels
    ax.set_xlabel("QPS", fontweight='heavy', fontsize=14, fontname='Times New Roman')
    ax.set_ylabel("P95 in ms", fontweight='heavy', fontsize=14, fontname='Times New Roman')

    ax.tick_params(axis='x', labelsize=12)  # adjust x-axis font size
    ax.tick_params(axis='y', labelsize=12)  # adjust y-axis font size
    for label in ax.get_xticklabels():
        label.set_fontname('Times New Roman')
        label.set_fontweight('heavy')
    for label in ax.get_yticklabels():
        label.set_fontname('Times New Roman')
        label.set_fontweight('heavy')

    ax.spines['top'].set_linewidth(2)    # 上边框
    ax.spines['bottom'].set_linewidth(2) # 下边框
    ax.spines['left'].set_linewidth(2)   # 左边框
    ax.spines['right'].set_linewidth(2)  # 右边框

    # plot lines and err bars
    for i in range(len(test_array)):
        xaxis = [testDataRow[qps_id] for testDataRow in testAvgDataSets[i]]
        yaxis = [testDataRow[p95_id]/1000 for testDataRow in testAvgDataSets[i]]

        xerrs = [testErrRow[qps_id] for testErrRow in testErrSets[i]]
        yerrs = [testErrRow[p95_id]/1000 for testErrRow in testErrSets[i]]

        # plt.plot(xaxis, yaxis, label=test_array[i], linestyle='-')
        linestyle = {"linestyle":"--", "linewidth":3, "markeredgewidth":2, "elinewidth":0.8, "capsize":1, "color": color_array[i]}
        ax.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])

    # plot local zoom_1
    axins_1 = ax.inset_axes((0.1, 0.55, 0.3, 0.4))
    axins_1.spines['top'].set_linewidth(1)    # 上边框
    axins_1.spines['bottom'].set_linewidth(1) # 下边框
    axins_1.spines['left'].set_linewidth(1)   # 左边框
    axins_1.spines['right'].set_linewidth(1)  # 右边框

    for i in range(len(test_array)):
        if (test_array[i] == 'cpu' or test_array[i] == 'l1i'):
            xaxis = [testDataRow[qps_id] for testDataRow in testAvgDataSets[i]]
            yaxis = [testDataRow[p95_id]/1000 for testDataRow in testAvgDataSets[i]]

            xerrs = [testErrRow[qps_id] for testErrRow in testErrSets[i]]
            yerrs = [testErrRow[p95_id]/1000 for testErrRow in testErrSets[i]]

            # plt.plot(xaxis, yaxis, label=test_array[i], linestyle='-')
            # linestyle = {"linestyle":"--", "linewidth":3, "markeredgewidth":2, "elinewidth":0.8, "capsize":1, "color": color_array[i]}
            # axins.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])
            linestyle = {"linestyle":"--", "linewidth":3, "markeredgewidth":2, "color": color_array[i]}
            axins_1.plot(xaxis, yaxis, **linestyle, label=test_array[i])

    # X-axis display range
    xlim0 = 27e3
    xlim1 = 29e3

    # Y-axis display range
    ylim0 = 5.5
    ylim1 = 7.1

    # adjust child axis display range
    axins_1.set_xlim(27e3, 29e3)
    axins_1.set_ylim(5.5, 7.1)

    axins_1.set_xlim(xlim0, xlim1)
    axins_1.set_ylim(ylim0, ylim1)

    axins_1.tick_params(axis='x', labelsize=10)  # adjust x-axis font size
    axins_1.tick_params(axis='y', labelsize=10)  # adjust y-axis font size
    for label in axins_1.get_xticklabels():
        label.set_fontweight('heavy')
        label.set_fontname('Times New Roman')
    for label in axins_1.get_yticklabels():
        label.set_fontweight('heavy')
        label.set_fontname('Times New Roman')

    axins_1.set_xticks([27e3, 27.5e3, 28e3, 28.5e3, 29e3])
    axins_1.set_xticklabels(['27k', '27.5k', '28k', '28.5k', '29k'])

    patch_list_1 = mark_inset(ax, axins_1, loc1=4, loc2=1, fc="none", ec='k', lw=0.6)
    for patch in patch_list_1:
        patch.set_linestyle('--')  # 设置边框为虚线

    # plot local zoom_2
    axins_2 = ax.inset_axes((0.61, 0.3, 0.15, 0.2))
    axins_2.spines['top'].set_linewidth(1)    # 上边框
    axins_2.spines['bottom'].set_linewidth(1) # 下边框
    axins_2.spines['left'].set_linewidth(1)   # 左边框
    axins_2.spines['right'].set_linewidth(1)  # 右边框

    for i in range(len(test_array)):
        if (test_array[i] == 'nointerference' or test_array[i] == 'l2' or test_array[i] == 'l1d'):
            xaxis = [testDataRow[qps_id] for testDataRow in testAvgDataSets[i]]
            yaxis = [testDataRow[p95_id]/1000 for testDataRow in testAvgDataSets[i]]

            xerrs = [testErrRow[qps_id] for testErrRow in testErrSets[i]]
            yerrs = [testErrRow[p95_id]/1000 for testErrRow in testErrSets[i]]

            # plt.plot(xaxis, yaxis, label=test_array[i], linestyle='-')
            # linestyle = {"linestyle":"--", "linewidth":3, "markeredgewidth":2, "elinewidth":0.8, "capsize":1, "color": color_array[i]}
            # axins.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])
            linestyle = {"linestyle":"--", "linewidth":3, "markeredgewidth":2, "color": color_array[i]}
            axins_2.plot(xaxis, yaxis, **linestyle, label=test_array[i])

    # X-axis display range
    xlim0 = 49e3
    xlim1 = 54e3

    # Y-axis display range
    ylim0 = 1
    ylim1 = 2

    # adjust child axis display range
    axins_2.set_xlim(49e3, 54e3)
    axins_2.set_ylim(1, 2)

    axins_2.set_xlim(xlim0, xlim1)
    axins_2.set_ylim(ylim0, ylim1)

    axins_2.tick_params(axis='x', labelsize=10)  # adjust x-axis font size
    axins_2.tick_params(axis='y', labelsize=10)  # adjust y-axis font size
    for label in axins_2.get_xticklabels():
        label.set_fontname('Times New Roman')
        label.set_fontweight('heavy')
    for label in axins_2.get_yticklabels():
        label.set_fontname('Times New Roman')
        label.set_fontweight('heavy')

    axins_2.set_xticks([50e3, 52e3, 54e3])
    axins_2.set_xticklabels(['50k', '52k', '54k'])

    patch_list_2 = mark_inset(ax, axins_2, loc1=4, loc2=1, fc="none", ec='k', lw=0.6)
    for patch in patch_list_2:
        patch.set_linestyle('--')  # 设置边框为虚线

    ax.grid(ls='-.', lw = 0.5, color = "#4E616C")
    plt.legend()
    plt.savefig('./part1-fig.png', dpi=1200)
    plt.show()

if __name__ == "__main__":
    # convert txt file into csv, this step is not necessary, however it might facilitate further usage
    txt2csv()

    # collect all avg tets data
    testAvgSets = []
    for test in test_array:
        testAvg = calculate_avg(test)
        testAvgSets.append(testAvg)
    testAvgSets = np.array(testAvgSets)

    # calculate err for all tests
    testErrSets = []
    for i in range(len(test_array)):
        errAvg = calculate_err(test_array[i])
        testErrSets.append(errAvg)
    testErrSets = np.array(testErrSets)
    
    # make plot
    plot_qps_p95_local_zoom(testAvgSets, testErrSets)
    


