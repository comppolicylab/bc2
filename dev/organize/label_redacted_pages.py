import fitz  # PyMuPDF
from openai import OpenAI
import os
import base64
import sys
import shutil
import tempfile
import argparse

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def convert_pdf_to_image(pdf_path, output_image_path, dpi=72):
    document = fitz.open(pdf_path)
    page = document.load_page(0)  # Assumes a one-page PDF
    pix = page.get_pixmap(dpi=dpi)
    pix.save(output_image_path)

def main():
    parser = argparse.ArgumentParser(description="Process PDF and send to GPT-4o.")
    parser.add_argument('--api_key', required=True, help="OpenAI API key")
    parser.add_argument('--input_pdf', required=True, help="Path to the input PDF file")
    parser.add_argument('--output_folder', required=True, help="Path to the output folder")
    parser.add_argument('--copy_pdf', action='store_true', help="Flag to copy the input PDF to the output folder")
    
    args = parser.parse_args()

    api_key = args.api_key
    pdf_path = args.input_pdf
    output_folder = args.output_folder
    copy_pdf = args.copy_pdf

    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create a temporary directory for the image
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_image_path = os.path.join(tmpdirname, "output_image.png")

        # Convert PDF to image
        convert_pdf_to_image(pdf_path, output_image_path)

        # Encode the image
        base64_image = encode_image(output_image_path)

        # Set up OpenAI client
        client = OpenAI(api_key=api_key)

        # Send the image to GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant in a police department. Your job is to examine narratives in crime reports that are being prepared for public release to see if they have been redacted yet. You should specifically check to see if the narratives or other freely written text on the page contain redactions. You should ignore other parts of the document. Redactions often appear as black boxes on the page, sometimes digitally generated, othertimes drawn with a marker. These black-box redactions may also include placeholder text, e.g., the legal statute that justifies the redaction. But sometimes instead of black boxes, they just appear as blank white space in the middle of a sentence where a word would be. Respond with 'yes' if the page has any redactions, and 'no' if it has no visible redactions. Do not provide any other commentary."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Does this page contain any redactions?"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"}
                    }
                ]}
            ],
            temperature=0.0,
        )

        # Define output response filename
        input_filename = os.path.basename(pdf_path)
        output_response_filename = os.path.splitext(input_filename)[0] + ".txt"
        output_response_path = os.path.join(output_folder, output_response_filename)

        # Save the response to the output folder
        with open(output_response_path, "w") as response_file:
            response_file.write(response.choices[0].message.content)

        # Optionally copy the source PDF to the output folder
        if copy_pdf:
            shutil.copy(pdf_path, os.path.join(output_folder, input_filename))

if __name__ == "__main__":
    main()