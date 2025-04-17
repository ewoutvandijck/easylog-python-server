import os

from src.jobs.ingest_pdf.lib.extract_and_process_pdf import extract_and_process_pdf
from src.lib.prisma import prisma
from src.lib.supabase import supabase
from src.logger import logger


async def ingest_from_upload_file_job(
    file_data: bytes,
    file_name: str | None = None,
    bucket: str = "knowledge",
    target_path: str = "/",
) -> None:
    try:
        processed_pdf = await extract_and_process_pdf(file_data)

        if file_name:
            processed_pdf.file_name = file_name

        full_pdf_path = os.path.join(target_path, processed_pdf.file_name)

        supabase.storage.from_(bucket).upload(
            full_pdf_path,
            file_data,
            {
                "upsert": "true",
                "content-type": processed_pdf.file_type,
            },
        )

        pdf_file_object = await prisma.objects.find_first_or_raise(where={"name": full_pdf_path, "bucket_id": bucket})

        processed_pdf_db = await prisma.processed_pdfs.upsert(
            where={
                "object_id": pdf_file_object.id,
            },
            data={
                "create": {
                    "object_id": pdf_file_object.id,
                    "short_summary": processed_pdf.short_summary,
                    "long_summary": processed_pdf.long_summary,
                    "markdown_content": processed_pdf.markdown_content,
                    "file_type": processed_pdf.file_type,
                },
                "update": {
                    "short_summary": processed_pdf.short_summary,
                    "long_summary": processed_pdf.long_summary,
                    "markdown_content": processed_pdf.markdown_content,
                    "file_type": processed_pdf.file_type,
                },
            },
        )

        for image in processed_pdf.images:
            image_full_path = os.path.join(target_path, image.file_name)

            supabase.storage.from_(bucket).upload(
                image_full_path,
                image.file_data,
                {
                    "upsert": "true",
                    "content-type": image.file_type,
                },
            )

            image_storage_upload = await prisma.objects.find_first_or_raise(
                where={"name": image_full_path, "bucket_id": bucket}
            )

            await prisma.processed_pdf_images.upsert(
                where={"object_id": image_storage_upload.id},
                data={
                    "create": {
                        "processed_pdf_id": processed_pdf_db.id,
                        "object_id": image_storage_upload.id,
                        "original_file_name": image.file_name,
                        "page": image.page,
                        "summary": image.summary,
                    },
                    "update": {
                        "summary": image.summary,
                        "page": image.page,
                    },
                },
            )

    except Exception as e:
        logger.error(f"Error ingesting from upload file job: {str(e)}")
        raise e
