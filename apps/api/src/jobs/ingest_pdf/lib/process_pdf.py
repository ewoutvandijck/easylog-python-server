import asyncio
import os

from src.jobs.ingest_pdf.lib.extract_and_process_pdf import extract_and_process_pdf
from src.lib.prisma import prisma
from src.lib.supabase import supabase


async def process_pdf(
    file_data: bytes,
    file_name: str | None = None,
    target_bucket: str = "knowledge",
    target_path: str = "/",
) -> None:
    processed_pdf = await asyncio.to_thread(extract_and_process_pdf, file_data)

    if file_name:
        processed_pdf.file_name = file_name

    full_pdf_path = os.path.join(target_path, processed_pdf.file_name)

    supabase.storage.from_(target_bucket).upload(
        full_pdf_path,
        file_data,
        {
            "upsert": "true",
            "content-type": processed_pdf.file_type,
        },
    )

    pdf_file_object = prisma.objects.find_first_or_raise(where={"name": full_pdf_path, "bucket_id": target_bucket})

    processed_pdf_db = prisma.processed_pdfs.upsert(
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

        supabase.storage.from_(target_bucket).upload(
            image_full_path,
            image.file_data,
            {
                "upsert": "true",
                "content-type": image.file_type,
            },
        )

        image_storage_upload = prisma.objects.find_first_or_raise(
            where={"name": image_full_path, "bucket_id": target_bucket}
        )

        prisma.processed_pdf_images.upsert(
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
