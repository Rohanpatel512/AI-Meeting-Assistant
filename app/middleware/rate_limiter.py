from app.database.database import SessionLocal
from app.database.database import SessionLocal
from sqlalchemy import select 
from app.database import models  

from app.core.config import (
    MAX_FILE_SIZE_MB, 
    TOTAL_FILE_SIZE_MB,
    DAILY_SUMMARY_LIMIT,
    MAX_TRANSCRIPT_CHARS,
    RATE_LIMIT_PER_MINUTE
)

limit_reached = False

def _file_size_uploaded(file_size_uploaded: float) -> bool:
    """
    Checks if the file uploaded has a size that exceeds the maximum allowed size.

    args:
        file_size_uploaded (float): The size of the uploaded file in MB.
    
    returns:
        bool: True if the file size exceeds the maximum allowed size, False otherwise.
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
            limit_reached = True
        else:
            usage_record.total_file_size += file_size_uploaded
            db.commit()
    finally:
        db.close()

def _daily_summary_check(user_id: str) -> None:
    """
    Checks if the user has reached their daily summary limit.

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
        print(f"Total summary limit: {DAILY_SUMMARY_LIMIT}")

        if usage_record.summary_amount >= int(DAILY_SUMMARY_LIMIT):
            limit_reached = True
        else:
            usage_record.summary_amount += 1

            db.commit()
    finally:
        db.close()
        


def _check_transcript_size(meeting_text: str) -> bool:
    """
    Checks if the transcript size is too large.

    args:
        meeting_text (str): The text of the meeting transcript.
    
    returns:
        bool: True if the transcript size exceeds the maximum allowed characters, False otherwise.
    """

    if len(meeting_text) > int(MAX_TRANSCRIPT_CHARS):
        return True 

    return False 


def run_rate_limiter(file_size: float, meeting_text: str, user_id: str) -> dict:
    
    _daily_summary_check(user_id)
    _total_file_size(user_id, file_size)

    if limit_reached:
        return {"message": "Maximum usage limit reached"}

    if _file_size_uploaded(file_size):
        return {"message": "File size too large. Maximum size can only be 0.2 MB"}

    if _check_transcript_size(meeting_text):
        return {"message": "Transcript too large."}

    return {"message": ""}
        

