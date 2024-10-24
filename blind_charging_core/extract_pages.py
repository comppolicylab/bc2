import os
import click
from pypdf import PdfReader, PdfWriter

def extract_pages(full_path: str, relative_path: str, output_dir: str, 
                  page_numbers: set[int] | None = None):
    """Explode a PDF into single pages, with filenames reflecting their
    relative path and page number.
    
    Args:
        full_path: The path to the PDF file to explode.
        relative_path: The relative path of the file within the base directory.
        output_dir: Directory to write the exploded pages to.
        page_numbers: The page numbers to extract. If None, all pages are extracted.
    """
    pdf = PdfReader(full_path)
    print(relative_path)

    if page_numbers is None:
        page_numbers = set(range(len(pdf.pages)))

    for page_number in page_numbers:
        page = pdf.pages[page_number]

        # Format the output filename to include the relative path
        new_base_name = f"{relative_path.replace('/', '_').replace('.pdf', '')}_page_{page_number + 1}.pdf"
        output_path = os.path.join(output_dir, new_base_name)

        # Write the page to a new PDF
        writer = PdfWriter()
        writer.add_page(page)
        writer.write(output_path)

def find_pdfs(base_dir: str):
    """Recursively find all PDF files within a base directory.
    
    Args:
        base_dir: The base directory to search in.
        
    Returns:
        A list of tuples containing the full path and the relative path of each PDF found.
    """
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=base_dir)
                yield full_path, relative_path

@click.command()
@click.argument("base_dir")
@click.argument("output_dir")
@click.option(
    "--page-numbers",
    type=click.STRING,
    help="The page numbers to extract. If not specified, all pages are extracted.",
    default=None,
)
def main(base_dir: str, output_dir: str, page_numbers: str | None = None):
    """Explode PDFs found in a base directory into single pages.
    
    Args:
        base_dir: The base directory containing the PDF files to explode.
        output_dir: Directory to write the exploded pages to.
        page_numbers: The page numbers to extract. If None, all pages are extracted.
    """
    pages: set[int] | None = None
    if page_numbers is not None:
        pages = {int(x) for x in page_numbers.split(",")}

    for full_path, relative_path in find_pdfs(base_dir):
        extract_pages(full_path, relative_path, output_dir, pages)

if __name__ == "__main__":
    main()
