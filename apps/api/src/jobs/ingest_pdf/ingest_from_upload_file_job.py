from src.lib.mistral import mistralai_client
from src.lib.supabase import create_supabase
from src.logger import logger


async def ingest_from_upload_file_job(
    file_data: bytes,
    file_name: str,
    bucket: str = "knowledge",
) -> None:
    try:
        supabase = await create_supabase()

        upload_response = await supabase.storage.from_(bucket).upload(
            file_name,
            file_data,
            {
                "upsert": "true",
                "content-type": "application/pdf",
            },
        )

        logger.info(f"Uploaded file to {upload_response.path}")

        ocr_response = await mistralai_client.ocr.process_async(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": await supabase.storage.from_(bucket).get_public_url(upload_response.path),
            },
            include_image_base64=True,
        )

        logger.info(f"OCR response: {ocr_response.usage_info}")

    except Exception as e:
        logger.error(f"Error ingesting from upload file job: {str(e)}")
        raise e
