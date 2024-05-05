import os
import re
import shutil
import argparse
import pandas as pd

def format_filename(text):
    text = re.sub(r'[\s,]', '_', text.lower())
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text

def process_file(row, source_folder, dest_folder):
    case_id = row['Case_ID']
    filename = row['Filename']
    referring_agency_state = row['Referring_Agency_State'].lower()
    referring_agency = format_filename(row['Referring_Agency'])

    base_folder = f"{referring_agency_state}_{referring_agency}"

    source_path = os.path.join(source_folder, str(case_id), str(filename))
    dest_subdir = os.path.join(dest_folder, base_folder, str(case_id))
    dest_path = os.path.join(dest_subdir, str(filename))

    os.makedirs(dest_subdir, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    print(f"Copied {filename} to {dest_path}")

def main(directory_path, source_folder, dest_folder):
    df = pd.read_excel(directory_path)

    for _, row in df.iterrows():
        process_file(row, source_folder, dest_folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files based on Excel data.')
    parser.add_argument('directory_path', type=str, help='Path to the Excel file')
    parser.add_argument('source_folder', type=str, help='Path to the source folder')
    parser.add_argument('dest_folder', type=str, help='Path to the destination folder')

    args = parser.parse_args()

    main(args.directory_path, args.source_folder, args.dest_folder)