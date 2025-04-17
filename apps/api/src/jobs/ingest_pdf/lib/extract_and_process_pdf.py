from src.jobs.ingest_pdf.models import ProcessedPDF
from src.lib.mistral import mistralai_client


async def extract_and_process_pdf(file_data: bytes) -> ProcessedPDF:
    response = await mistralai_client.ocr.process_async(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": "https://arxiv.org/pdf/2201.04234",
        },
        include_image_base64=True,
    )

    markdown_content = "\n\n".join([page.markdown for page in response.pages])

    return ProcessedPDF(
        short_summary="",
        long_summary="",
        markdown_content=markdown_content,
        file_type="application/pdf",
        images=[],
    )
