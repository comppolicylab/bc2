import argparse
import os
import random
import re
from collections import defaultdict

import pandas as pd
from pypdf import PdfReader, PdfWriter


def format_filename(text):
    text = re.sub(r"[\s,]", "_", text.lower())
    text = re.sub(r"[^a-z0-9_]", "", text)
    return text


def process_pdf( # noqa: C901
    state_agency,
    folder_name,
    filename,
    case_id,
    rows,
    source_folder,
    dest_folder,
    extract_mode,
    exclude_foreign_pages,
):
    print(f"Processing {state_agency} - {folder_name} - {filename} - {case_id}")
    pdf_path = os.path.join(
        source_folder, state_agency, "raw", folder_name, str(filename)
    )

    with open(pdf_path, "rb") as file:
        pdf_reader = PdfReader(file)

        for _, row in rows.iterrows():
            doc_excluded_pages = []
            doc_foreign_pages_value = row["foreign_pages"]
            if not pd.isnull(doc_foreign_pages_value) and exclude_foreign_pages:
                if "," in str(doc_foreign_pages_value):
                    attached_ranges = doc_foreign_pages_value.split(",")
                    for item in attached_ranges:
                        if "-" in item:
                            start, end = item.split("-")
                            doc_excluded_pages.extend(range(int(start), int(end) + 1))
                        else:
                            doc_excluded_pages.append(int(item))
                else:
                    doc_excluded_pages = [doc_foreign_pages_value]

            doc_start = row["document_start"]
            doc_end = row["document_end"]
            doc_type = row["document_type"].lower().strip()

            if extract_mode == "document":
                output_filename = (
                    "__".join(
                        [
                            state_agency,
                            folder_name,
                            str(filename),
                            f"doc_{doc_start}_{doc_end}",
                        ]
                    )
                    + ".pdf"
                )
                output_path = os.path.join(dest_folder, doc_type, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                pdf_writer = PdfWriter()
                for page in range(int(doc_start) - 1, int(doc_end)):
                    if page + 1 in doc_excluded_pages:
                        continue
                    pdf_writer.add_page(pdf_reader.pages[page])

                with open(output_path, "wb") as output:
                    print(f"Writing {output_filename}")
                    pdf_writer.write(output)
            else:
                for page in range(int(doc_start) - 1, int(doc_end)):
                    if page + 1 in doc_excluded_pages:
                        continue
                    output_filename = (
                        "__".join(
                            [
                                state_agency,
                                folder_name,
                                str(filename),
                                f"pg{page + 1:03}",
                            ]
                        )
                        + ".pdf"
                    )
                    output_path = os.path.join(dest_folder, doc_type, output_filename)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    pdf_writer = PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page])

                    with open(output_path, "wb") as output:
                        print(f"Writing {output_filename}")
                        pdf_writer.write(output)
    print("")


def main(
    inventory_path,
    doc_type,
    source_folder,
    dest_folder,
    num_samples,
    sample_by_agency,
    extract_mode,
    exclude_foreign_pages,
):
    df = pd.read_excel(inventory_path)
    filtered_df = df[
        df["document_type"].str.contains(doc_type, regex=True, na=False)
        & (df["duplicate_notes"] != "Ignore")
    ]

    print(len(df))

    grouped_df = filtered_df.groupby(
        [
            "referring_agency_state",
            "referring_agency",
            "folder_name",
            "file_name",
            "document_id",
        ]
    )

    groups = list(grouped_df)

    if num_samples:
        if sample_by_agency:
            agency_counts = filtered_df["referring_agency"].value_counts()
            agency_weights = defaultdict(lambda: 1.0)

            for agency, count in agency_counts.items():
                agency_weights[agency] = count + 1

            weighted_groups = []
            for (
                state,
                agency,
                folder_name,
                file_name,
                document_id,
            ), group_df in groups:
                weighted_groups.append(
                    (
                        (state, agency, folder_name, file_name, document_id),
                        group_df,
                        agency_weights[agency],
                    )
                )

            weighted_groups = sorted(
                weighted_groups, key=lambda x: random.random() ** x[2], reverse=True
            )
            print(weighted_groups)
            selected_groups = weighted_groups[:num_samples]
        else:
            selected_groups = random.sample(groups, min(num_samples, len(groups)))
    else:
        selected_groups = groups

    for (
        state,
        agency,
        folder_name,
        file_name,
        document_id,
    ), group_df in selected_groups:
        state_agency = format_filename(f"{state}_{agency}")
        process_pdf(
            state_agency,
            folder_name,
            file_name,
            document_id,
            group_df,
            source_folder,
            dest_folder,
            extract_mode,
            exclude_foreign_pages,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process PDF files based on report inventory."
    )
    parser.add_argument("inventory_path", type=str, help="Path to the Excel inventory")
    parser.add_argument(
        "doc_type", type=str, help="Regex string for filtering the Groups column"
    )
    parser.add_argument("source_folder", type=str, help="Path to the source folder")
    parser.add_argument("dest_folder", type=str, help="Path to the destination folder")
    parser.add_argument(
        "--num_samples",
        type=int,
        help="Number of documents to randomly sample",
        default=None,
    )
    parser.add_argument(
        "--sample_by_agency",
        action="store_true",
        help="Whether to overweight small agencies in sample",
    )
    parser.add_argument(
        "--extract_mode",
        type=str,
        choices=["page", "document"],
        default="page",
        help='"page" for page-by-page, "document" for entire document',
    )
    parser.add_argument(
        "--exclude_foreign_pages",
        action="store_true",
        help="Whether to exclude foreign pages from exports",
    )

    args = parser.parse_args()

    main(
        args.inventory_path,
        args.doc_type,
        args.source_folder,
        args.dest_folder,
        args.num_samples,
        args.sample_by_agency,
        args.extract_mode,
        args.exclude_foreign_pages,
    )
