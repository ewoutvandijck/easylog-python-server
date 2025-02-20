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


def process_pdf_process(file_data: bytes) -> ProcessedPDF:
    logger.info("Starting PDF processing")

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

    df = pd.DataFrame(json_data["elements"])

    # Set alternate text to NA for all rows
    df["alternate_text"] = None

    # Initialize table data processing
    df["table_data"] = None

    # Process figures and generate alternative text
    logger.info("Processing figures and generating alternative text")
    figures_mask = df["Path"].str.extract(CONTENT_TYPE_EXTRACTOR)[0] == "Figure"
    figures = df[figures_mask]
    logger.debug(f"Found {len(figures)} figures in the document")

    images: list[ProcessedPDFImage] = []

    # Process each figure and generate alt text using Gemini
    for idx, (row_hash, figure) in enumerate(figures.iterrows()):
        if not isinstance(figure["filePaths"], list) or len(figure["filePaths"]) == 0:
            logger.warning(f"Figure at index {idx} has no file paths, skipping")
            continue

        if pd.notna(figure["alternate_text"]):
            logger.debug(f"Figure at index {idx} already has alt text, skipping")
            continue

        # Extract and process image
        image_path = figure["filePaths"][0]
        logger.debug(f"Processing figure {idx + 1}/{len(figures)}: {image_path}")

        # Generate alt text using Gemini
        with zf.open(image_path) as image_file:
            image_data = image_file.read()
            logger.debug(f"Generating alt text for figure {image_path}")
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

            progress = f"{float(idx + 1.0) / len(figures) * 100:.1f}%"
            logger.info(f"Progress: {progress} - Generated alt text for figure {image_path}")
            print(f"{progress}: {response.text.strip() if response.text else ''}")

            df.at[row_hash, "alternate_text"] = response.text

            images.append(
                ProcessedPDFImage(
                    file_name=image_path.split("/")[-1],
                    file_type="image/png",
                    file_data=image_data,
                    summary=response.text or "",
                    page=figure["Page"],
                )
            )
    # Process tables
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

    tables_df.sample()

    # Clean up the dataframe
    logger.debug("Cleaning up extracted data")
    columns_to_remove = ["ObjectID", "attributes", "Font", "HasClip", "Lang", "TextSize", "ClipBounds"]
    elements_df = df.drop(columns=columns_to_remove, errors="ignore").sort_values("Page")

    # Generate document summary
    logger.info("Generating document summary using Gemini")
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            system_instruction="Generate a short summary of the goal of the procedure in the following document in dutch."
        ),
        contents=[
            Content(
                parts=[
                    Part.from_text(text=json.dumps(elements_df.to_dict(orient="records"), indent=2)),
                ],
            )
        ],
    )

    logger.info("PDF processing completed successfully")
    return ProcessedPDF(
        summary=response.text or "",
        file_type="application/pdf",
        images=images,
    )
