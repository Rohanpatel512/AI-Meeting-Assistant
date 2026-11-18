from app.database.database import SessionLocal
from sqlalchemy import select 
from app.database import models  

from app.core.config import (
    MAX_FILE_SIZE_MB, 
    TOTAL_FILE_SIZE_MB,
    TOTAL_SUMMARY_LIMIT,
)


def _file_size_uploaded(file_size_uploaded: float) -> bool:
    """
    Checks if the file uploaded has a size that exceeds the maximum allowed size.

    args:
        file_size_uploaded (float): The size of the uploaded file in MB.
    
    returns:
        True if the file size exceeds the maximum allowed size, False otherwise.
    """

    if file_size_uploaded > float(MAX_FILE_SIZE_MB):
        return True

    return False


def _total_file_size(user_id: str, file_size_uploaded: float) -> None:
    """
    Checks if the total file size uploaded by the user has exceeded the maximum allowed size.

    args:
        file_size_uploaded (float): The size of the uploaded file in MB.
        user_id (str): The ID of the user uploading the file.
    
    returns:
        None: Updates the total file size in the database if it hasn't exceeded the limit.
    
    """

    # From the database fetch the total file size uploaded
    db = SessionLocal()

    try:
        stmt = select(models.Usage).where(models.Usage.user_id == int(user_id))
        usage_record = db.scalar(stmt)

        if usage_record.total_file_size >= float(TOTAL_FILE_SIZE_MB):
            return True
        else:
            usage_record.total_file_size += file_size_uploaded
            db.commit()
    finally:
        db.close()

    return False 


def _total_summary_check(user_id: str) -> None:
    """
    Checks if the user has reached their total summary limit.

    args:
        user_id (str): The ID of the user.
    
    returns:
        None: Updates the summary amount in the database if it hasn't exceeded the limit.
    """

    # From the database fetch the number of times user has summarized
    db = SessionLocal()

    try:
        stmt = select(models.Usage).where(models.Usage.user_id == int(user_id))
        usage_record = db.scalar(stmt)

        print(f"Usage Summary Amount: {usage_record.summary_amount}")
        print(f"Total summary limit: {TOTAL_SUMMARY_LIMIT}")

        if usage_record.summary_amount >= int(TOTAL_SUMMARY_LIMIT):
            return True 
        else:
            usage_record.summary_amount += 1

            db.commit()
    finally:
        db.close()

    return False 
        


def run_rate_limiter(file_size: float, user_id: str) -> dict:

    if _file_size_uploaded(file_size):
        return {"message": "File size too large. Maximum size can only be 0.2 MB."}

    meets_total_file_size = _total_file_size(user_id, file_size)

    if meets_total_file_size:
        return {"message": "Maximum file size storable reached."}
    
    meets_total_summary = _total_summary_check(user_id)

    if meets_total_summary:
        return {"message": "Maximum summary limit reached."}
    

    return {"message": ""}
        

