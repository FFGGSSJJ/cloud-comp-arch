def calculate_percentage(file_path):
    count_p95_above_1000 = 0
    total_count = 0
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('read'):
                data = line.split()
                p95_value = float(data[12])  # p95 is located at the 13th position (index 12)
                total_count += 1
                if p95_value > 1000:
                    count_p95_above_1000 += 1
                    
    # Calculate the percentage if there are any records
    if total_count > 0:
        percentage = (count_p95_above_1000 / total_count) * 100
    else:
        percentage = 0
        
    return percentage

# Paths to the files (you should replace these with the actual paths of your files)
file_paths = ["./results/results_part4_3/results/result_0.txt", "./results/results_part4_3/results/result_1.txt", "./results/results_part4_3/results/result_2.txt"]

# Calculate the percentage for each file
results = [calculate_percentage(path) for path in file_paths]

# Calculate the average percentage of all three experiments
average_percentage = sum(results) / len(results) if results else 0

print("Percentages of p95 > 1000:", results)
print("Average percentage:", average_percentage)
