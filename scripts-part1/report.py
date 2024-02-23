import csv
import numpy as np
import matplotlib.pyplot as plt

test_array = ['memcache', 'cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw']
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
                with open(fileName, 'w') as out_file:
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
    plt.ylim(0, 8)

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
        linestyle = {"linestyle":"--", "linewidth":0.7, "markeredgewidth":0.7, "elinewidth":0.8, "capsize":1}
        plt.errorbar(xaxis, yaxis, xerr=xerrs,yerr=yerrs, **linestyle, label=test_array[i])
    
    plt.legend()
    plt.savefig('./part1-fig.png')
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
        print(errAvg)
    testErrSets = np.array(testErrSets)
    
    # make plot
    plot_qps_p95(testAvgSets, testErrSets)
    


