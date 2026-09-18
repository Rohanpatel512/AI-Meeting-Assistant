from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from services.meeting_service import summarize

meeting_router = APIRouter(prefix="/meeting", tags=["Meeting"])

@meeting_router.post("/summarize")
async def summarize_meeting(file: UploadFile):

    # Check if no file was provided
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Check the file type. Only .txt and .docx are supported for now
    if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".docx")):
        raise HTTPException(status_code=415, detail="File type not supported")

    # Extract all the text from the file
    meeting_text = await file.read().decode("utf-8")

    if meeting_text == "":
        raise HTTPException(status_code=401, detail="File contents empty")

    # TODO: Set up call to summarize meeting text
    summarize(meeting_text)


@meeting_router.post("/analyze")
async def analyze_meeting():
    pass 

@meeting_router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    pass 
