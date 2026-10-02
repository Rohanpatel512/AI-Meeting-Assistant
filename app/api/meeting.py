from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from app.services.meeting_service import summarize
from docx import Document 
from app.services.transcript_preprocess import preprocess_text
from app.middleware.rate_limiter import run_rate_limiter

meeting_router = APIRouter(prefix="/meeting", tags=["Meeting"])

@meeting_router.post("/summarize")
async def summarize_meeting(file: UploadFile):

    # Check if no file was provided
    if not file:
        raise HTTPException(
            status_code=400, 
            detail="No file uploaded"
        )

    # Get file name 
    filename = file.filename or ""

    # Check the file type. Only .txt and .docx are supported for now
    if not filename.lower().endswith((".txt", ".docx")):
        raise HTTPException(status_code=415, detail="File type not supported")

    # Extract all the text from the file
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="File contents empty"
        )

    if filename.lower().endswith(".txt"):
        meeting_text = content.decode("utf-8")
    else:
        document = Document(file.file)
        meeting_text = " ".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        
    if not meeting_text:
        raise HTTPException(
            status_code=400,
            detail="No text found in file"
        )

    # Get the file size in MB to ensure it hasn't surpassed limit 
    size_in_mb = file.size / (1024 * 1024)

    # Run the rate limiter
    data = run_rate_limiter(size_in_mb, meeting_text) 
    if data["message"] != "":
        raise HTTPException(
            status_code=401,
            detail=data["message"]
        )

    # Preprocess the meeting text 
    meeting_text = preprocess_text(meeting_text)
    
    # Set up call to summarize meeting text
    summarized_meeting = summarize(meeting_text)
    
    return summarized_meeting

