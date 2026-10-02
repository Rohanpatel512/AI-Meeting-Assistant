from app.core.config import (
    MAX_FILE_SIZE_MB, 
    TOTAL_FILE_SIZE_MB,
    DAILY_SUMMARY_LIMIT,
    MAX_TRANSCRIPT_CHARS,
    RATE_LIMIT_PER_MINUTE
)

limit_reached = False

def _file_size_uploaded(file_size_uploaded):

    if file_size_uploaded > MAX_FILE_SIZE_MB:
        return True

    return False

def _total_file_size():

    # TODO: From the database fetch the total file size uploaded
    total_uploaded_size = 0

    if total_uploaded_size > TOTAL_FILE_SIZE_MB:
        limit_reached = True

def _daily_summary_check():

    # TODO: From the database fetch the number of times user has summarized
    times_summarized = 0

    if times_summarized > DAILY_SUMMARY_LIMIT:
        limit_reached = True


def _check_transcript_size(meeting_text):

    if len(meeting_text) > MAX_TRANSCRIPT_CHARS:
        return True 

    return False 


def run_rate_limiter(file_size, meeting_text):
    
    _daily_summary_check()
    _total_file_size()

    if limit_reached:
        return {"message": "Maximum usage limit reached"}

    if _file_size_uploaded(file_size):
        return {"message": "File size too large. Maximum size can only be 0.2 MB"}

    if _check_transcript_size(meeting_text):
        return {"message": "Transcript too large."}

    return {"message": ""}
        

