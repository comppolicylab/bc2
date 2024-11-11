import sys
from pathlib import Path

import fitz  # PyMuPDF


def convert_pdf_to_images(input_dir, output_dir, dpi=300):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(
            f"Error: Input directory {input_dir} does not exist or is not a directory."
        )
        return

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in the input directory {input_dir}.")
        return

    for pdf_file in pdf_files:
        try:
            pdf_document = fitz.open(pdf_file)
            print(f"Processing {pdf_file}")
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                zoom = dpi / 72  # 72 is the default DPI for PyMuPDF
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                image_filename = (
                    output_path / f"{pdf_file.stem}_page_{page_num + 1}.jpeg"
                )
                pix.save(image_filename)
                print(f"Saved: {image_filename}")
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_dir> <output_dir>")
    else:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
        convert_pdf_to_images(input_dir, output_dir)
