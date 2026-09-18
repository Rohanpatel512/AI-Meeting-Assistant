from pydantic import BaseModel, Field
from typing import List, Optional 

class MeetingNotes(BaseModel):
    overview: str = Field(description="Overview")
    discussion_points: List = Field(description="Key Discussion Points")
    tasks_and_deadlines: List = Field(description="Tasks & Deadlines")
    decisions: List = Field(description="Important Descisions Made")
    