from src.jobs.ingest_pdf.lib.process_pdf import process_pdf


async def ingest_from_upload_file_job(
    file_data: bytes,
    file_name: str | None = None,
    bucket: str = "knowledge",
    target_path: str = "/",
) -> None:
    await process_pdf(file_data, file_name, target_bucket=bucket, target_path=target_path)
