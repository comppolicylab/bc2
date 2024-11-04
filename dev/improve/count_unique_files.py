import os
import re
import sys


def extract_base_filename(filename):
    # Pattern to remove specific suffix patterns: '_page_XXX', '.ocr.json', and '.labels.json'
    # This pattern matches these specific parts and will be used to remove them
    suffix_pattern = re.compile(r"_page_.+$")
    # Remove the matched patterns (if any) to get the base filename
    base_filename = re.sub(suffix_pattern, "", filename)
    return base_filename


def extract_base_pagename(filename):
    suffix_pattern = re.compile(r"pdf.*$")
    base_pagename = re.sub(suffix_pattern, "", filename)
    return base_pagename


def extract_base_department(filename):
    suffix_pattern = re.compile(r"_(pd|sheriff)_.+$")
    base_department = re.sub(suffix_pattern, "", filename)
    return base_department


def main(folder_path):
    unique_bases = set()
    unique_depts = set()
    unique_pages = set()

    # Walk through the files in the specified folder
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            base = extract_base_filename(filename)
            dept = extract_base_department(filename)
            page = extract_base_pagename(filename)
            if base:
                unique_bases.add(base)
            if dept:
                unique_depts.add(dept)
            if page:
                unique_pages.add(page)

    # Print the number of unique base filenames
    print(f"Number of departments: {len(unique_depts)}")
    print(f"Number of reports: {len(unique_bases)}")
    print(f"Number of pages: {len(unique_pages)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_unique_bases.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    main(folder_path)
