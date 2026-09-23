from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from app.services.meeting_service import summarize
from docx import Document 

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
    
    # Set up call to summarize meeting text
    summarized_meeting = summarize(meeting_text)
    
    return summarized_meeting


@meeting_router.post("/analyze")
async def analyze_meeting():
    pass 

@meeting_router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    pass 
