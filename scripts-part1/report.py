import csv
import numpy as np

testArray = ['memcache', 'cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw']

# turn txt file into csv file
def txt2csv():
    for test in testArray[0:1]:
        for i in range(1, 4):
            fields_row = []
            data_rows = []
            with open('results/'+test+'-'+str(i)+'.txt', 'r') as testtxt:
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
                fileName = 'results/'+test+'-'+str(i)+'.csv'
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
        with open('results/'+test+'-'+str(i)+'.csv', 'r') as testcsv:
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


def plot_qps():
    return



if __name__ == "__main__":

    # convert txt file into csv, this step is not necessary, however it might facilitate further usage
    txt2csv()

    # 
    testSets = np.array([])
    for test in testArray:
        testAvg = calculate_avg(test)
        np.append(testSets, testAvg)
    
    print(testSets)
    


