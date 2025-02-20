from src.jobs.ingest_pdf.models import ProcessedPDF, ProcessedPDFImage
from src.lib.prisma import prisma
from src.lib.supabase import supabase


async def process_pdf(file_data: bytes, file_name: str | None = None, target_bucket: str = "storage"):
    processed_pdf = ProcessedPDF(
        # Annoying bullshit because of Pydantic
        **{k: v for k, v in {"file_name": file_name}.items() if v is not None},
        subject="Hele mooie PDF",
        summary="Een pdf met super veel mooie afbeeldingen",
        file_type="application/pdf",
        images=[
            ProcessedPDFImage(
                file_type="image/png",
                file_name="image.png",
                summary="Een mooie afbeelding",
                page=1,
                file_data=b"",
            ),
        ],
    )

    supabase.storage.from_(target_bucket).upload(
        processed_pdf.file_name,
        file_data,
        {
            "upsert": "true",
            "content-type": processed_pdf.file_type,
        },
    )

    pdf_file_upload = prisma.objects.find_first_or_raise(
        where={"name": processed_pdf.file_name, "bucket_id": target_bucket}
    )

    prisma.processed_pdfs.upsert(
        where={
            "object_id": pdf_file_upload.id,
        },
        data={
            "create": {
                "object_id": pdf_file_upload.id,
                "subject": processed_pdf.subject,
                "summary": processed_pdf.summary,
                "file_type": processed_pdf.file_type,
            },
            "update": {
                "subject": processed_pdf.subject,
                "summary": processed_pdf.summary,
                "file_type": processed_pdf.file_type,
            },
        },
    )

    for image in processed_pdf.images:
        image_file_upload = supabase.storage.from_(target_bucket).upload(
            image.file_name,
            image.file_data,
            {
                "upsert": "true",
                "content-type": image.file_type,
            },
        )
