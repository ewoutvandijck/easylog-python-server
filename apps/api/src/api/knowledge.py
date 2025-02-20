import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from src.jobs.ingest_pdf.ingest_from_upload_file_job import ingest_from_upload_file_job

router = APIRouter()


@router.post(
    "/upload",
    name="upload_document",
    tags=["knowledge"],
    description="Upload a PDF document to be processed and stored in the knowledge base",
)
async def create_upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.content_type == "application/pdf" or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # TODO: generate an import job id
    file_id = str(uuid.uuid4())

    background_tasks.add_task(
        ingest_from_upload_file_job,
        file_data=file.file.read(),
        file_name=file.filename,
        bucket="knowledge",
        target_path=file_id,
    )

    return {"id": file_id}
