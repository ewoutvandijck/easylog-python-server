import uuid

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Response, UploadFile

from src.jobs.ingest_pdf.ingest_from_upload_file_job import ingest_from_upload_file_job
from src.lib.prisma import prisma
from src.lib.supabase import create_supabase
from src.lib.weaviate import weaviate_client

router = APIRouter()


@router.post(
    "/documents",
    name="upload_document",
    tags=["knowledge"],
    description="Upload a PDF document to be processed and stored in the knowledge base",
)
async def upload_pdf_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    subject: str = Body(..., embed=True),
) -> Response:
    if not file.content_type == "application/pdf" or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are allowed")

    background_tasks.add_task(
        ingest_from_upload_file_job,
        file_data=await file.read(),
        file_name=file.filename or f"{str(uuid.uuid4())}.pdf",
        bucket="documents",
        subject=subject,
    )

    return Response(status_code=200)


@router.delete(
    "/documents/{document_id}",
    name="delete_document",
    tags=["knowledge"],
    description="Delete a document from the knowledge base",
)
async def delete_document(document_id: str) -> Response:
    document = await prisma.documents.find_first(where={"id": document_id})

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await prisma.documents.delete(where={"id": document_id})

    document_collection = weaviate_client.collections.get("documents")
    if document.weaviate_id and document_collection:
        await document_collection.data.delete_by_id(document.weaviate_id)

    supabase = await create_supabase()
    await supabase.storage.from_("documents").remove([document.path.split("/")[:-1]])

    return Response(status_code=200)
