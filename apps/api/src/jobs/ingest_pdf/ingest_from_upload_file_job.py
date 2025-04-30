import base64
import datetime
import re
import uuid
from io import BytesIO

from prisma import Json

from src.jobs.ingest_pdf.models import DocumentEntity, DocumentPageEntity
from src.lib.mistral import mistralai_client
from src.lib.openai import openai_client
from src.lib.prisma import prisma
from src.lib.supabase import create_supabase
from src.logger import logger


async def ingest_from_upload_file_job(
    file_data: bytes,
    file_name: str,
    bucket: str = "knowledge",
) -> None:
    base_path = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"

    try:
        supabase = await create_supabase()

        upload_response = await supabase.storage.from_(bucket).upload(
            f"{base_path}/{file_name}",
            file_data,
            {
                "upsert": "true",
                "content-type": "application/pdf",
            },
        )

        logger.info(f"Uploaded file to {upload_response.path}")

        document_public_url = await supabase.storage.from_(bucket).get_public_url(upload_response.path)

        ocr_response = await mistralai_client.ocr.process_async(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": document_public_url,
            },
            include_image_base64=True,
        )

        logger.info(f"OCR response: {ocr_response.usage_info}")

        document_result = DocumentEntity(
            file_name=file_name,
            document_url=document_public_url,
            pages=[],
        )

        for page_index, page in enumerate(ocr_response.pages):
            document_page = DocumentPageEntity(
                page_number=page_index + 1,
                markdown=page.markdown,
            )

            for image in page.images:
                if not isinstance(image.image_base64, str):
                    logger.warning("Image base64 is not a string")
                    continue

                content_type_match = re.search(r"data:image/([^;]+);base64,", image.image_base64)
                if not content_type_match:
                    logger.warning("Could not extract image type from base64 data")
                    continue

                content_type = content_type_match.group(1)
                logger.info(f"Image type: image/{content_type}")

                image_data = base64.b64decode(image.image_base64.split(",")[1])
                image_data = BytesIO(image_data)
                image_data.seek(0)

                image_upload_response = await supabase.storage.from_(bucket).upload(
                    f"{base_path}/images/page_{str(page_index + 1).zfill(3)}/{image.id}",
                    image_data.getvalue(),
                    {
                        "content-type": f"image/{content_type}",
                    },
                )

                image_public_url = await supabase.storage.from_(bucket).get_public_url(image_upload_response.path)

                document_page.markdown = document_page.markdown.replace(image.id, image_public_url)

                logger.info(f"Added document image: {image_public_url}")

            document_result.pages.append(document_page)

        document = await prisma.documents.create(
            data={
                "file_name": file_name,
                "content": Json(document_result.model_dump(mode="json")),
            },
        )

        logger.info(f"Created document: {document.id}")

        full_text = f"{file_name}\n\n"
        for page in document_result.pages:
            full_text += f"Page {page.page_number}/{len(document_result.pages)}:\n\n{page.markdown}\n\n"

        response = await openai_client.chat.completions.create(
            model="openai/gpt-4.1",
            messages=[
                {
                    "role": "developer",
                    "content": """
Act as a professional summarizer. Create a concise and summary of the text below, while adhering to the guidelines enclosed in [ ] below. 
Guidelines:
[
- Ensure that the summary includes relevant details, while avoiding any unnecessary information or repetition. 
- Rely strictly on the provided text, without including external information.
- The length of the summary must be within 1500 characters.
- You must start with "<filename> (<document_id>) describes <summary>"
]""",
                },
                {
                    "role": "user",
                    "content": full_text,
                },
            ],
            stream=False,
        )

        summary = response.choices[0].message.content or ""

        logger.info(f"Summary: {summary}")

    except Exception as e:
        logger.error(f"Error ingesting from upload file job: {str(e)}")
        raise e
