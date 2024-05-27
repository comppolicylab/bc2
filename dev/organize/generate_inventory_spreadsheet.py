import os
import csv
import sys

def generate_csv(root_folder):
    data = []

    for subdir, _, files in os.walk(root_folder):
        for file in files:
            file_path = os.path.join(subdir, file)
            relative_path = os.path.relpath(file_path, root_folder)
            parts = relative_path.split(os.sep)
            
            if len(parts) < 4:
                continue

            agency_fullname, _, folder_name, _ = parts[:4]
            referring_agency = ' '.join(agency_fullname.split('_')[1:]).title()
            referring_agency = referring_agency.replace(' Pd', ' PD')
            referring_agency_state = agency_fullname.split('_')[0].upper()
            file_type = os.path.splitext(file)[1][1:]

            data.append({
                "folder_name": folder_name,
                "file_name": file,
                "referring_agency": referring_agency,
                "referring_agency_state": referring_agency_state,
                "file_type": file_type
            })

    with open('draft_inventory.csv', 'w', newline='') as csvfile:
        fieldnames = ["folder_name", "file_name", "referring_agency", "referring_agency_state", "file_type"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <root_folder>")
        sys.exit(1)

    root_folder = sys.argv[1]
    generate_csv(root_folder)
    print("CSV file 'draft_inventory.csv' generated successfully.")
