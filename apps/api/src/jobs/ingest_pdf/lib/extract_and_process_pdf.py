import gc  # Add garbage collection
import io
import json
import zipfile

import pandas as pd
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import (
    ExtractRenditionsElementType,
)
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import TableStructureType
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
from google.genai.types import (
    Content,
    GenerateContentConfig,
    Part,
)

from src.jobs.ingest_pdf.models import ProcessedPDF, ProcessedPDFImage
from src.lib.adobe import adobe_client
from src.lib.gemini import gemini_client
from src.logger import logger

CONTENT_TYPE_EXTRACTOR = r"/([^/]+?)(?:\[\d+\])?$"


def extract_and_process_pdf(file_data: bytes) -> ProcessedPDF:
    logger.info("Starting PDF processing")

    # Extract the PDF content using Adobe service
    json_data, zf = extract_pdf_content(file_data)

    # Process the extracted data
    elements_df, images = process_extracted_data(json_data, zf)

    # Generate summaries and markdown content
    short_summary = generate_summary(elements_df, is_short=True)
    long_summary = generate_summary(elements_df, is_short=False)
    markdown_content = generate_markdown(elements_df)

    logger.info("PDF processing completed successfully")

    return ProcessedPDF(
        short_summary=short_summary,
        long_summary=long_summary,
        markdown_content=markdown_content,
        file_type="application/pdf",
        images=images,
    )


def extract_pdf_content(file_data: bytes) -> tuple[dict, zipfile.ZipFile]:
    """Extract PDF content using Adobe service and return structured data and zip file."""
    # Upload the source file as an asset
    logger.debug("Uploading PDF to Adobe service")
    input_asset = adobe_client.upload(input_stream=file_data, mime_type=PDFServicesMediaType.PDF)

    # Set the parameters for extraction
    logger.debug("Configuring PDF extraction parameters")
    extract_pdf_params = ExtractPDFParams(
        table_structure_type=TableStructureType.XLSX,
        elements_to_extract=[
            ExtractElementType.TEXT,
            ExtractElementType.TABLES,
        ],
        elements_to_extract_renditions=[ExtractRenditionsElementType.FIGURES],
    )

    # Create and submit the extraction job
    logger.info("Submitting PDF extraction job to Adobe")
    extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
    location = adobe_client.submit(extract_pdf_job)
    pdf_services_response = adobe_client.get_job_result(location, ExtractPDFResult)

    logger.debug("Retrieving extracted content from Adobe")
    result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
    stream_asset: StreamAsset = adobe_client.get_content(result_asset)

    # Process the ZIP archive containing extracted content
    logger.info("Processing extracted ZIP content")
    zip_content = stream_asset.get_input_stream()
    zf = zipfile.ZipFile(io.BytesIO(zip_content))

    # Parse the structured JSON data
    logger.debug("Parsing structured JSON data")
    json_data = json.loads(zf.read("structuredData.json"))

    return json_data, zf


def process_extracted_data(json_data: dict, zf: zipfile.ZipFile) -> tuple[pd.DataFrame, list[ProcessedPDFImage]]:
    """Process the extracted data, including figures and tables."""
    df = pd.DataFrame(json_data["elements"])

    # Set alternate text to NA for all rows
    df["alternate_text"] = None

    # Initialize table data processing
    df["table_data"] = None

    # Process figures and generate alternative text
    images = process_figures(df, zf)

    # Process tables
    process_tables(df, zf)

    # Clean up the dataframe
    logger.debug("Cleaning up extracted data")
    columns_to_remove = ["ObjectID", "attributes", "Font", "HasClip", "Lang", "TextSize", "ClipBounds"]
    elements_df = df.drop(columns=columns_to_remove, errors="ignore")

    return elements_df, images


def process_figures(df: pd.DataFrame, zf: zipfile.ZipFile) -> list[ProcessedPDFImage]:
    """Process figures and generate alternative text."""
    logger.info("Processing figures and generating alternative text")
    figures_mask = df["Path"].str.extract(CONTENT_TYPE_EXTRACTOR)[0] == "Figure"
    figures = df[figures_mask]
    logger.debug(f"Found {len(figures)} figures in the document")

    images: list[ProcessedPDFImage] = []

    # Get total memory usage for monitoring
    import psutil

    process = psutil.Process()

    # Process each figure and generate alt text using Gemini
    for idx, (row_hash, figure) in enumerate(figures.iterrows()):
        # Log memory usage periodically
        if idx % 5 == 0:
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"Memory usage: {memory_mb:.2f} MB after processing {idx} images")

        if not isinstance(figure["filePaths"], list) or len(figure["filePaths"]) == 0:
            logger.warning(f"Figure at index {idx} has no file paths, skipping")
            continue

        if pd.notna(figure["alternate_text"]):
            logger.debug(f"Figure at index {idx} already has alt text, skipping")
            continue

        # Extract and process image
        image_path = figure["filePaths"][0]
        logger.debug(f"Processing figure {idx + 1}/{len(figures)}: {image_path}")

        try:
            # Generate alt text using Gemini
            with zf.open(image_path) as image_file:
                # Read image data in a controlled way
                image_data = image_file.read()

                # Check image size
                image_size_mb = len(image_data) / 1024 / 1024
                logger.debug(f"Image size: {image_size_mb:.2f} MB")

                logger.debug(f"Generating alt text for figure {image_path}")
                alt_text = generate_alt_text(image_data)

                progress = f"{float(idx + 1.0) / len(figures) * 100:.1f}%"
                logger.info(f"Progress: {progress} - Generated alt text for figure {image_path}")
                print(f"{progress}: {alt_text}")

                df.at[row_hash, "alternate_text"] = alt_text

                # Create a more memory-efficient representation
                # Option 1: Store full image data (original approach)
                images.append(
                    ProcessedPDFImage(
                        file_name=image_path,
                        file_type="image/png",
                        file_data=image_data,  # This stores the full image in memory
                        summary=alt_text,
                        page=figure["Page"],
                    )
                )

                # Force garbage collection after each image
                image_data = None  # Help garbage collector
                gc.collect()

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            # Continue processing other images instead of failing completely

    return images


def process_tables(df: pd.DataFrame, zf: zipfile.ZipFile) -> None:
    """Process tables from the document."""
    logger.info("Processing tables from the document")
    table_mask = df["Path"].str.extract(CONTENT_TYPE_EXTRACTOR)[0] == "Table"
    tables_df = df[table_mask]
    logger.debug(f"Found {len(tables_df)} tables in the document")

    # Process each table
    for row_hash, row in tables_df.iterrows():
        excel_path = row["filePaths"][0]
        logger.debug(f"Processing table from {excel_path}")

        with zf.open(excel_path) as excel_file:
            table_df = pd.read_excel(excel_file)
            df.at[row_hash, "table_data"] = table_df.to_dict()


def generate_alt_text(image_data: bytes) -> str:
    """Generate alternative text for an image using Gemini."""
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction="""Generate the alternative text for this figure for accessibility purposes. Describe the meaning of the figure and the key components or elements shown.
            The text should be in Dutch. Be concise and to the point. Just the description of the figure, no introduction or other text.
            """,
        ),
        contents=[
            Content(
                parts=[
                    Part.from_text(text="Here is the figure:"),
                    Part.from_bytes(data=image_data, mime_type="image/png"),
                ],
            )
        ],
    )

    return response.text or ""


def generate_summary(elements_df: pd.DataFrame, is_short: bool = True) -> str:
    """Generate a summary of the document using Gemini."""
    summary_type = "short" if is_short else "long"
    max_words = "10" if is_short else "100"

    logger.info(f"Generating {summary_type} summary using Gemini")

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction=f"Generate a {summary_type} summary of the goal of the procedure in the following document in dutch. Maximum {max_words} words."
        ),
        contents=[
            Content(
                parts=[
                    Part.from_text(text=json.dumps(elements_df.to_dict(orient="records"), indent=2)),
                ],
            )
        ],
    )

    logger.info(f"{summary_type.capitalize()} summary: {response.text}")
    return response.text or ""


def generate_markdown(elements_df: pd.DataFrame) -> str:
    """Generate markdown content from the document data using Gemini."""
    logger.info("Generating markdown content using Gemini")

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction="Generate markdown from the following data. Render each row in this data as a markdown item. I don't want a single table. I want a nicely formatted markdown document. So headings should be headings, and images should be images. etc. For images use the alt text to describe the image."
        ),
        contents=[
            Content(
                parts=[
                    Part.from_text(text=json.dumps(elements_df.to_dict(orient="records"), indent=2)),
                ],
            )
        ],
    )

    logger.info(f"Markdown content: {response.text}")
    return response.text or ""
