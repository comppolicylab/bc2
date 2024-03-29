import os
import argparse
import pandas as pd
from pypdf import PdfReader, PdfWriter

def process_pdf(case_id, filename, rows, source_folder, dest_folder):
    pdf_path = os.path.join(source_folder, str(case_id), str(filename))

    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        total_pages = len(pdf_reader.pages)

        claimed_pages = set()

        for _, row in rows.iterrows():
            doc_start = row['Document_Start']
            doc_end = row['Document_End']
            doc_type = row['Document_Type'].lower()
            doc_id = row['Document_ID']
            doc_num = row['Document_Num']

            output_filename = f"{doc_type}_{case_id}_{doc_id}_{doc_num}.pdf"
            output_path = os.path.join(dest_folder, output_filename)

            pdf_writer = PdfWriter()

            for page in range(int(doc_start) - 1, int(doc_end)):
                pdf_writer.add_page(pdf_reader.pages[page])
                claimed_pages.add(page)

            with open(output_path, 'wb') as output:
                print(f"Writing {output_filename}")
                pdf_writer.write(output)

        remaining_pages = set(range(total_pages)) - claimed_pages
        if remaining_pages:
            output_filename = f"unlabeled_{case_id}.pdf"
            output_path = os.path.join(dest_folder, output_filename)

            pdf_writer = PdfWriter()

            for page in remaining_pages:
                pdf_writer.add_page(pdf_reader.pages[page])

            with open(output_path, 'wb') as output:
                print(f"Writing {output_filename}")
                pdf_writer.write(output)

def main(directory_path, groups, source_folder, dest_folder):
    df = pd.read_excel(directory_path)
    filtered_df = df[df['Group'].str.contains(groups, regex=True)]

    for (case_id, filename), group_df in filtered_df.groupby(['Case_ID', 'Filename']):
        process_pdf(case_id, filename, group_df, source_folder, dest_folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process PDF files based on Excel data.')
    parser.add_argument('directory_path', type=str, help='Path to the Excel file')
    parser.add_argument('groups', type=str, help='Regex string for filtering the Groups column')
    parser.add_argument('source_folder', type=str, help='Path to the source folder')
    parser.add_argument('dest_folder', type=str, help='Path to the destination folder')

    args = parser.parse_args()

    main(args.directory_path, args.groups, args.source_folder, args.dest_folder)