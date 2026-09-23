# Imports
from app.core.schemas import MeetingNotes
from app.core.config import LLM_API_KEY
from groq import Groq
import instructor 

client = instructor.from_groq(Groq(api_key=LLM_API_KEY), mode=instructor.Mode.JSON)

prompt = """
Summarize the following meeting transcript and output structured JSON.
You MUST adhere strictly to the JSON schema. Ensure you use the exact key names required by the fields (e.g., use 'task' and 'text' as keys where specified).

Focus on:
    - The main topics discussed.
    - Identifying tasks that need to be completed and their deadlines.
    - Key decisions that were made.
     
Only include tasks, deadlines, and decisions that are explicitly stated or clearly supported by the transcript. Do not invent or assume information.
"""


def summarize(meeting_contents):
    """
    Utilizes an open-source LLM to generate meaningful meeting notes for user.

    Args:
        meeting_contents - All meeting contents extracted from transcript (str)
    
    Returns:
        meeting_summary - Important details from meeting in JSON format (MeetingNotes)
    """

    schema_dict = MeetingNotes.model_json_schema()
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Extract:\n{meeting_contents}"}
        ],
        response_model=MeetingNotes
    )

    return response



