# Imports
from app.core.schemas import MeetingNotes
from app.core.config import LLM_API_KEY
from groq import AsyncGroq
import instructor 
import asyncio
import random


client = instructor.from_groq(AsyncGroq(api_key=LLM_API_KEY), mode=instructor.Mode.JSON)

prompt = """
Summarize the following meeting transcript segment and output structured JSON.
You MUST adhere strictly to the JSON schema. Ensure you use the exact key names required by the fields (e.g., use 'task' and 'text' as keys where specified).

Strict Formatting Rules:
    - overview: Write ONLY ONE concise sentence (maximum 15–20 words) capturing the core topic of this segment. Do not write multiple sentences or paragraphs.
    - key_discussions: Extract ONLY 1-2 most important points. Return an empty list if the segment is small talk, scheduling banter, or repetition.
    - tasks: Include ONLY explicit action items, owners, and deadlines.
    - decisions: Include ONLY concrete agreements or resolutions made.

Only include tasks, deadlines, and decisions that are explicitly stated or clearly supported by the transcript. Do not invent or assume information.
"""

combine_prompt = """
Consolidate these chunk-level meeting notes into one cohesive, deduplicated summary matching the JSON schema.

Strict Rules:
    - overview: Write ONE 2–3 sentence paragraph summarizing the entire meeting. Do not list sentences chunk-by-chunk.
    - key_discussions: Merge overlapping points, remove repetition, and keep ONLY the top 5–7 most important takeaways.
    - tasks: Deduplicate action items, keeping only explicit tasks, owners, and deadlines.
    - decisions: Deduplicate and keep only concrete final agreements.
"""


async def extract_chunk_notes(chunk_texts: list, semaphore: asyncio.Semaphore):
    """
    Extracts each chunk note and sends it to LLM for summarization.

    Args:
        chunk_texts (list) - Preprocessed transcript split into chunks semantically  
        semaphore (asyncio.Semaphore) - Limits the number of concurrent API requests to the LLM.

    """

    contents = " ".join(text.replace("[SEP]", ":") for text in chunk_texts)

    print(f"Number of Chunks {len(chunk_texts)}")

    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Extract:\n{contents}"}
                ],
                response_model=MeetingNotes
            )
        
            await asyncio.sleep(25 + random.uniform(0.5, 1.5))
            return response
        except Exception as e:
            error = str(e)
            if "429" in error or "rate_limit_exceeded" in error: 
                await asyncio.sleep(25 + random.uniform(0.5, 1.5))
            else:
                raise  

async def combine_notes(merged_notes: MeetingNotes) -> str:
    """
    Deduplicates and synthesizes raw chunk-level notes into a concise final summary.

    Args:
        merged_notes - Merged summarized chunks (MeetingNotes)
    
    Returns:
        final_notes - The final summary to be displayed to user (str)
    """

    return await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages = [
            {"role": "system", "content": combine_prompt},
            {"role": "user", "content": merged_notes.model_dump_json()}
        ],
        response_model=MeetingNotes
    )

async def summarize(chunked_data: list, max_concurrency: int = 1) -> str:
    """
    Utilizes an open-source LLM to generate meaningful meeting notes for user.

    Args:
        chunked_data - Meeting transcript that has been semantically chunked for summarization (list)
    
    Returns:
        meeting_summary - Important details from meeting in JSON format (MeetingNotes)
    """

    semaphore = asyncio.Semaphore(max_concurrency)

    result = await asyncio.gather(*[
        extract_chunk_notes(chunk, semaphore) for chunk in chunked_data
    ])

    data_merged = {}

    for field_name, field_info in MeetingNotes.model_fields.items():
        combined = []
        for notes in result:
            value = getattr(notes, field_name, None)
            if isinstance(value, list):
                combined.extend(value)
            elif isinstance(value, str):
                combined.append(value.strip())

        if field_info.annotation is str:
            data_merged[field_name] = "\n".join(combined)
        else:
            data_merged[field_name] = combined 
        
    merged_notes = MeetingNotes(**data_merged)
    final_summary = await combine_notes(merged_notes)

    return final_summary, prompt 