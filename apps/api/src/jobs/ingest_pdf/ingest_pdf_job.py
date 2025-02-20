from src.jobs.ingest_pdf.process_pdf import process_pdf


async def ingest_from_file_system(
    file_name: str,
) -> None:
    with open(file_name, "rb") as file:
        file_data = file.read()

    await process_pdf(file_data, file_name)
