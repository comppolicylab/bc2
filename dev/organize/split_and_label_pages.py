import os
import re
import argparse
import pandas as pd
import random
from pypdf import PdfReader, PdfWriter

def format_filename(text):
    text = re.sub(r'[\s,]', '_', text.lower())
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text

def process_pdf(folder_name, filename, case_id, agency, state,
                rows, source_folder, dest_folder, extract_mode):
    
    print(f"Processing {agency} - {state} - {folder_name} - {filename} - {case_id}")
    agency_filename = format_filename(agency)
    agency_folder = f"{state.lower()}_{agency_filename}"
    pdf_path = os.path.join(source_folder, agency_folder,
                            "raw", folder_name, str(filename))

    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)

        for _, row in rows.iterrows():
            doc_attached_pages = []
            doc_attached_pages_value = row['foreign_pages']
            if not pd.isnull(doc_attached_pages_value):
                print(doc_attached_pages_value)
                print()
                attached_ranges = doc_attached_pages_value.split(',')
                for item in attached_ranges:
                    if '-' in item:
                        start, end = item.split('-')
                        doc_attached_pages.extend(range(int(start), 
                                                        int(end) + 1))
                    else:
                        doc_attached_pages.append(int(item))

            doc_start = row['document_start']
            doc_end   = row['document_end']
            doc_type  = row['document_type'].lower().strip()

            if extract_mode == "document":
                output_filename = "__".join([agency_folder, folder_name, 
                                             str(filename), 
                                             f"doc_{doc_start}_{doc_end}"]) + ".pdf"
                output_path = os.path.join(dest_folder, doc_type, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                pdf_writer = PdfWriter()
                for page in range(int(doc_start) - 1, int(doc_end)):
                    if page + 1 in doc_attached_pages:
                        continue
                    pdf_writer.add_page(pdf_reader.pages[page])

                with open(output_path, 'wb') as output:
                    print(f"Writing {output_filename}")
                    pdf_writer.write(output)
            else:
                for page in range(int(doc_start) - 1, int(doc_end)):
                    if page + 1 in doc_attached_pages:
                        continue
                    output_filename = "__".join([agency_folder, folder_name, 
                                                 str(filename), 
                                                 f"pg{page + 1:03}"]) + ".pdf"
                    output_path = os.path.join(dest_folder, doc_type, output_filename)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    pdf_writer = PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page])

                    with open(output_path, 'wb') as output:
                        print(f"Writing {output_filename}")
                        pdf_writer.write(output)
    print("")

def main(directory_path, doc_type, source_folder, dest_folder, num_samples, extract_mode):
    df = pd.read_excel(directory_path)
    filtered_df = df[df['document_type'].str.contains(doc_type, regex=True, na=False) & 
                     (df['duplicate_notes'] != "Ignore")]

    print(len(df))

    grouped_df = filtered_df.groupby(['folder_name', 'file_name', 'document_id', 
                                      'referring_agency', 
                                      'referring_agency_state'])

    groups = list(grouped_df)
    if num_samples:
        groups = random.sample(groups, min(num_samples, len(groups)))

    for (folder_name, file_name, document_id, agency, state), group_df in groups:
        process_pdf(folder_name, file_name, document_id, agency, state, 
                    group_df, source_folder, dest_folder, extract_mode)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process PDF files based on Excel data.')
    parser.add_argument('directory_path', type=str, help='Path to the Excel file')
    parser.add_argument('doc_type', type=str, help='Regex string for filtering the Groups column')
    parser.add_argument('source_folder', type=str, help='Path to the source folder')
    parser.add_argument('dest_folder', type=str, help='Path to the destination folder')
    parser.add_argument('--num_samples', type=int, help='Number of documents to randomly sample', default=None)
    parser.add_argument('--extract_mode', type=str, choices=['page', 'document'], default='page', 
                        help='Mode of extraction: "page" for page-by-page, "document" for entire document')

    args = parser.parse_args()

    main(args.directory_path, args.doc_type, args.source_folder, args.dest_folder, args.num_samples, args.extract_mode)