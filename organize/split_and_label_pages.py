import os
import argparse
import pandas as pd
from pypdf import PdfReader, PdfWriter

def process_pdf(case_id, filename, agency, state,
                rows, source_folder, dest_folder):
    
    redacted_filename = filename.replace(".pdf", "_r.pdf")

    agency_folder = f"{state.lower()}_{agency.lower()}"
    agency_folder = agency_folder.replace(" ", "_")
    pdf_path = os.path.join(source_folder, agency_folder,
                            str(case_id), str(redacted_filename))

    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)

        for _, row in rows.iterrows():
            doc_attached_pages = []
            doc_attached_pages_value = row['Attached_Pages']
            if not pd.isnull(doc_attached_pages_value):
                print(doc_attached_pages_value)
                print()
                attached_ranges = doc_attached_pages_value.split(',')
                for item in attached_ranges:
                    if '-' in item:
                        start, end = item.split('-')
                        doc_attached_pages.extend(range(int(start), int(end) + 1))
                    else:
                        doc_attached_pages.append(int(item))

            doc_start = row['Document_Start']
            doc_end = row['Document_End']
            doc_type = row['Document_Type'].lower()
            doc_id = row['Document_ID']
            doc_num = row['Document_Num']
            group = row['Group']

            for page in range(int(doc_start) - 1, int(doc_end)):
                if page + 1 in doc_attached_pages:
                    continue
                output_filename = f"{case_id}_{doc_id}_{doc_num}_pg{page + 1:03}.pdf"
                group_lowercase = group.lower()
                output_path = os.path.join(dest_folder, agency_folder,
                                           group_lowercase, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page])

                with open(output_path, 'wb') as output:
                    print(f"Writing {output_filename}")
                    pdf_writer.write(output)

def main(directory_path, groups, source_agency, source_folder, dest_folder):
    df = pd.read_excel(directory_path)
    filtered_df = df[df['Group'].str.contains(groups, regex=True) & 
                     df['Referring_Agency'].str.contains(source_agency, 
                                                         regex=True) &
                     df['Authoring_Agency'].str.contains(source_agency, 
                                                         regex=True)]
    grouped_df = filtered_df.groupby(['Case_ID', 'Filename', 
                                      'Referring_Agency', 
                                      'Referring_Agency_State'])

    for (case_id, filename, agency, state), group_df in grouped_df:
        process_pdf(case_id, filename, agency, state, 
                    group_df, source_folder, dest_folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process PDF files based on Excel data.')
    parser.add_argument('directory_path', type=str, help='Path to the Excel file')
    parser.add_argument('groups', type=str, help='Regex string for filtering the Groups column')
    parser.add_argument('source_agency', type=str, help='Regex string for filtering the agency columns')
    parser.add_argument('source_folder', type=str, help='Path to the source folder')
    parser.add_argument('dest_folder', type=str, help='Path to the destination folder')

    args = parser.parse_args()

    main(args.directory_path, args.groups, args.source_agency, 
         args.source_folder, args.dest_folder)