import csv
import numpy as np
import matplotlib.pyplot as plt

result_dir_path = './results/'

# turn txt file into csv file
def txt2csv(test_dir: str, test_array: list[str]):
    for test in test_array:
        for i in range(1, 4):
            fields_row = []
            data_rows = []
            with open(result_dir_path+test_dir+test+'_'+str(i)+'.txt', 'r') as testtxt:
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
                fileName = result_dir_path+test_dir+test+'_'+str(i)+'.csv'
                with open(fileName, 'w', newline = '') as out_file:
                    writer = csv.writer(out_file)
                    writer.writerow(fields_row)
                    writer.writerows(data_rows)
                    out_file.close()
                testtxt.close()

# calculate avg value from 3 tests
def calculate_avg(test_dir: str, test: str):
    testAvg = np.zeros((25,19))

    for i in range(1,4):
        with open(result_dir_path+test_dir+test+'_'+str(i)+'.csv', 'r') as testcsv:
            # create reader obj
            csvreader = csv.reader(testcsv)

            field = next(csvreader)
            testCurr = []
            for row in csvreader:
                rowFloat = [float(k) for k in row[1:20]]
                testCurr.append(rowFloat)
 
            testAvg += np.array(testCurr)
            testcsv.close()
    # print(testAvg)
    return testAvg/3

def plot_qps_p95(testAvgDataSets, testErrSets, test_array):
    p95_id = 11
    qps_id = 16

    # set axis limit
    plt.xlim(0, 125000)
    # plt.xticks(np.linspace(0, 55000, 12), np.array(['0k', '5k', '10k', '15k', '20k', '25k', '30k', '35k', '40k', '45k', '50k', '55k']))
    # plt.ylim(0, 9)

    # set axis labels
    plt.xlabel("QPS")
    plt.ylabel("P95 in ms")

    # plot lines and err bars
    for i in range(len(test_array)):
        xaxis = [testDataRow[qps_id] for testDataRow in testAvgDataSets[i]]
        yaxis = [testDataRow[p95_id]/1000 for testDataRow in testAvgDataSets[i]]

        # xerrs = [testErrRow[qps_id] for testErrRow in testErrSets[i]]
        # yerrs = [testErrRow[p95_id]/1000 for testErrRow in testErrSets[i]]

        print(yaxis)

        plt.plot(xaxis, yaxis, label=test_array[i], linestyle='-')
        # linestyle = {"linestyle":"--", "linewidth":1.5, "markeredgewidth":2, "elinewidth":0.4, "capsize":1}
        # plt.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])
    
    plt.grid(ls='-.', lw = 0.5, color = "#4E616C")
    plt.legend()
    plt.savefig('./part4_1-fig.png', dpi=1200)
    plt.show()
    return


if __name__=="__main__":
    test1_dir = 'results_part4_1/'
    test1_array = ["t1c1", "t1c2", "t2c1", "t2c2"]
    txt2csv(test1_dir, test1_array)
    calculate_avg(test1_dir, test1_array[0])

    test1AvgSets = []
    for test in test1_array:
        testAvg = calculate_avg(test1_dir, test)
        test1AvgSets.append(testAvg)
    test1AvgSets = np.array(test1AvgSets)


    plot_qps_p95(test1AvgSets, None, test1_array)