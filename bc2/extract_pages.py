import os

import click
from pypdf import PdfReader, PdfWriter


def extract_pages(pdf_path: str, output_dir: str, page_numbers: set[int] | None = None):
    """Explode a PDF into single pages.

    Args:
        pdf_path: The path to the PDF file to explode.
        output_dir: Directory to write the exploded pages to.
        page_numbers: The page numbers to extract. If None, all pages are extracted.
    """
    pdf = PdfReader(pdf_path)

    if page_numbers is None:
        page_numbers = set(range(len(pdf.pages)))

    for page_number in page_numbers:
        page = pdf.pages[page_number]

        # Get the filename of the input file (without the directory)
        base_name = os.path.basename(pdf_path)
        new_base_name = base_name.replace(".pdf", f"_page_{page_number}.pdf")
        output_path = os.path.join(output_dir, new_base_name)

        # Write the page to a new PDF
        writer = PdfWriter()
        writer.add_page(page)
        writer.write(output_path)


@click.command()
@click.argument("pdf_path")
@click.argument("output_path")
@click.option(
    "--page-numbers",
    type=click.STRING,
    help="The page numbers to extract. If not specified, all pages are extracted.",
    default=None
    )
def main(pdf_path: str, output_path: str, page_numbers: str | None = None):
    """Explode a PDF into single pages.

    Args:
        pdf_path: The path to the PDF file to explode.
        output_path: Directory to write the exploded pages to.
        page_numbers: The page numbers to extract. If None, all pages are extracted.
    """
    if page_numbers is not None:
        page_numbers = set(int(x) for x in page_numbers.split(","))

    extract_pages(pdf_path, output_path, page_numbers)


if __name__ == "__main__":
    main()
