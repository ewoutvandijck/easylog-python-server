import os
import sys

sys.path.append(os.getcwd())

from prefect.task_worker import serve

from src.jobs.ingest_pdf.ingest_from_upload_file_job import ingest_from_upload_file_job

if __name__ == "__main__":
    serve(ingest_from_upload_file_job)
