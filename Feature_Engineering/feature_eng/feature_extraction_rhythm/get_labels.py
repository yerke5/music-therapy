import os
import csv

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def get_labels(input_path, output_file):
    classes = get_immediate_subdirectories(input_path)
    header = "songname label"
    file = open(output_file, 'w', newline='')
    writer = csv.writer(file, delimiter=",")
    writer.writerow(header.split())
    
    for c in classes:
        for filename in os.listdir(f'{input_path}\\{c}'):
            writer.writerow(f'{filename} {c}'.split())

if __name__ == "__main__":
    get_labels("../../dataset/d2/rp_test", "../../2class/csv/test_labels.csv")
