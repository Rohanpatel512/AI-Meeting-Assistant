from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional 

class DiscussionPoint(BaseModel):
    text: str = Field(description="A breif description of what was said regarding topic discussed.")

class Task(BaseModel):
    task: str = Field(description="The explicit action that needs to be taken")
    assignee: Optional[str] = Field(None, description="The name of the person responsible. Use `Unassigned` if unknown")
    deadline: Optional[str] = Field(None, description="The deadline mentioned, formatted as YYYY-MM-DD if possible, otherwise use descriptive phrases like `End of Q3`.")

class Decision(BaseModel):
    text: str = Field(description="Final decision or conclusion reached by the team.")
    rationale: Optional[str] = Field(None, description="The brief reason or context behind why this decision was made")

class MeetingNotes(BaseModel):
    overview: str = Field(description="Overview")
    discussion_points: List[DiscussionPoint] = Field(description="Key Discussion Points")
    tasks_and_deadlines: List[Task] = Field(description="Tasks & Deadlines")
    decisions: List[Decision] = Field(description="Important Descisions Made")
    