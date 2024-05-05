import os
import shutil
import click

@click.command()
@click.argument('source_dir')
@click.argument('destination_dir')
def copy_files(source_dir, destination_dir):
    """
    Copies PDF files and their corresponding OCR and label JSON files from SOURCE_DIR to DESTINATION_DIR,
    only if all three files exist for a given PDF.
    """
    # Ensure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Loop through all files in the source directory
    for file in os.listdir(source_dir):
        # Check if it's the fields.json file and copy that over if so
        if file == "fields.json":
            shutil.copy(os.path.join(source_dir, file), os.path.join(destination_dir, file))
            print(f"Copied {file}.")
            continue

        if file.endswith(".pdf"):
            # Construct the base name and expected file names
            base_name = os.path.splitext(file)[0]
            ocr_file = f"{base_name}.pdf.ocr.json"
            label_file = f"{base_name}.pdf.labels.json"

            # Check if both the OCR and label files exist
            if os.path.exists(os.path.join(source_dir, ocr_file)) and os.path.exists(os.path.join(source_dir, label_file)):
                # Copy the PDF, OCR, and label files to the destination directory
                shutil.copy(os.path.join(source_dir, file), os.path.join(destination_dir, file))
                shutil.copy(os.path.join(source_dir, ocr_file), os.path.join(destination_dir, ocr_file))
                shutil.copy(os.path.join(source_dir, label_file), os.path.join(destination_dir, label_file))
                print(f"Copied {file} and its corresponding OCR and label files.")

if __name__ == "__main__":
    copy_files()
