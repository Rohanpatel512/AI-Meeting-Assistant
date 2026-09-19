# Imports
from google import genai
from app.core.schemas import MeetingNotes

#client = genai.Client()
def summarize(meeting_contents):
    pass 
"""
def summarize(meeting_contents):
    
    Utilizes an open-source LLM to generate meaningful meeting notes for user.

    Args:
        meeting_contents - All meeting contents extracted from transcript (str)
    
    Returns:
        meeting_summary - Important details from meeting in JSON format (MeetingNotes)
    

    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=f
        Summarize the following meeting transcript.

        Focus on:
            - The main topics discussed.
            - Identifying tasks that need to be completed and their deadlines.
            - Key decisions that were made.
     
        Only include tasks, deadlines, and decisions that are explicitly stated or clearly supported by the transcript. Do not invent or assume information.
    
        Organize the summary into these points:
            1. Overview
            2. Key Discussion Points
            3. Tasks and Deadlines
            4. Decisions

        Keep the summary concise and easy to read

        Meeting Transcript:
        {meeting_contents}
        ,

        response_format={
            'type': "text",
            "mime_type": "application/json",
            "schema": MeetingNotes.model_json_schema()
        }
    )

    meeting_summary = MeetingNotes.model_validate_json(interaction.output_text)

    return meeting_summary


"""
