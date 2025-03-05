import time

from src.logger import logger


def ingest_from_upload_file_job(
    file_data: bytes,
    file_name: str | None = None,
    bucket: str = "knowledge",
    target_path: str = "/",
) -> None:
    timeout = 10 * 60  # 10 minutes
    start_time = time.time()
    log_interval = 5  # Log every 5 seconds

    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time

        # Log message every 5 seconds
        if int(elapsed_time) % log_interval == 0:
            logger.info(f"The time is {elapsed_time:.2f} seconds")

            # Small sleep to avoid multiple logs in the same second
            time.sleep(0.1)

        if elapsed_time > timeout:
            break
