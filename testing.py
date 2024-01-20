from pathlib import Path
import os
import csv
import re


if __name__ == "__main__":
    files = [os.path.join(os.getcwd(),"data","output.csv")]
    fw = open(os.path.join(os.getcwd(),"res.csv"), 'a',encoding="utf-8",errors="ignore",newline="")
    csv_writer = csv.writer(fw)

    count = 0
    for file in files:
        with open(file,encoding="utf-8") as fo:
            csv_reader = csv.reader(fo)
            for line in csv_reader:
                if(len(line) == 3 and line[2] != "" ):
                    if "@yahoo.com" in line[2].lower():
                        csv_writer.writerow(line)
                        count += 1
    print(count)
    fw.close()
