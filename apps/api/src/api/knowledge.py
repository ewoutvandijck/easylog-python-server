import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, UploadFile

from src.jobs.ingest_pdf.ingest_from_upload_file_job import ingest_from_upload_file_job

router = APIRouter()


@router.post(
    "/upload",
    name="upload_document",
    tags=["knowledge"],
    description="Upload a PDF document to be processed and stored in the knowledge base",
)
async def upload_pdf_document(file: UploadFile, background_tasks: BackgroundTasks) -> Response:
    if not file.content_type == "application/pdf" or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are allowed")

    background_tasks.add_task(
        ingest_from_upload_file_job,
        file_data=await file.read(),
        file_name=file.filename or f"{str(uuid.uuid4())}.pdf",
        bucket="knowledge",
    )

    return Response(status_code=200)
