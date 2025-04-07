#!/usr/bin/env python3
"""
Rename files to a consistent, sortable structure. Nest in yearly directories
"""
from glob import glob
from tqdm import tqdm
import os
import shutil




def main():
    data_dir = "valtiopaivat-records-pdf/data"
    data = glob(f"{data_dir}/*.pdf")
    for pdf in tqdm(data, total=len(data)):
        doctype, year, chamber, num = None, None, None, None
        path = pdf.split('/')
        filename = path[-1][:-4]
        file_constituents = filename.split('_')
        chamber = file_constituents[0].lower()
        year = file_constituents[-2]
        print(year)
        num = file_constituents[-1]
        if len(file_constituents) == 3:
            doctype = "prot"
        else:
            doctype = file_constituents[1].lower()

        if not os.path.isdir(f"{data_dir}/{year}"):
            os.mkdir(f"{data_dir}/{year}")
        shutil.move(pdf, f"{data_dir}/{year}/{'_'.join([doctype, year, chamber, num])}.pdf")




if __name__ == '__main__':
    main()
