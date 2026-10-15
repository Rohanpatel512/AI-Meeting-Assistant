# AI Meeting Assistant

An AI-powered web application that transforms meeting transcripts into structured, actionable meeting notes. Upload a `.txt` or `.docx` transcript to extract key discussion points, decisions, and action items with deadlines.

The application combines a FastAPI backend with an LLM-powered summarization pipeline and an interactive web interface, making meeting outcomes easier to review and act on.

## Features

### AI-Powered Meeting Summarization
- **Structured meeting notes:** Generates meeting overviews, discussion points, tasks and deadlines, and decisions.
- **Schema-validated output:** Uses Pydantic models to structure and validate LLM responses.
- **Actionable insights:** Organizes meeting information into readable sections instead of returning an unstructured block of text.
- **LLM integration:** Uses Groq's API with the `openai/gpt-oss-20b` model.

### Document Processing
- **Multiple file formats:** Accepts `.txt` and `.docx` meeting transcripts.
- **Transcript extraction:** Extracts text from uploaded documents before processing.
- **Input validation:** Checks supported file formats and handles empty or invalid transcript content.
- **Transcript preprocessing:** Cleans transcript text before summarization, with additional preprocessing improvements under development.

### Interactive Web Interface
- **Dynamic results rendering:** Renders structured meeting notes from the API response.
- **Typewriter effect:** Animates the presentation of generated content.
- **PDF export:** Exports generated meeting notes for offline access.
- **Clipboard support:** Allows users to copy meeting notes.
- **Authentication interface:** Includes login and signup pages.

### Backend Engineering and Safeguards
- **REST API:** Exposes FastAPI endpoints for meeting summarization and user operations.
- **Request validation and error handling:** Handles unsupported uploads, invalid input, and unsuccessful API responses.
- **Usage safeguards:** Includes configurable limits for request frequency, transcript length, file size, and generated output.
- **Database layer:** Uses SQLAlchemy ORM models for user and usage data.
- **Database migrations:** Uses Alembic to manage database schema changes.
- **Modular architecture:** Separates API routes, authentication utilities, configuration, database models, and application services.

## Tech Stack

| Component | Technologies |
|---|---|
| Backend | Python, FastAPI |
| LLM integration | Groq API, `openai/gpt-oss-20b` |
| Data validation | Pydantic |
| Document processing | Python, `python-docx` |
| Database access | SQLAlchemy |
| Database migrations | Alembic |
| Authentication foundations | Password hashing with bcrypt, signup/login endpoints |
| Frontend | HTML, CSS, JavaScript |
| Version control | Git, GitHub |

## Architecture

The application separates HTTP request handling from document processing, LLM integration, and database operations.

```text
                 Web Frontend
                      |
                      v
                FastAPI Backend
                      |
             +--------+--------+
             |                 |
             v                 v
       User Endpoints    Meeting Endpoint
                               |
                               v
                     File Validation
                               |
                               v
                     Text Extraction
                               |
                               v
                    Transcript Cleanup
                               |
                               v
                     Groq LLM Request
                               |
                               v
                    Pydantic Validation
                               |
                               v
                     Structured Response
                               |
                               v
                         Web Frontend
```

The frontend presents the generated notes and provides options to copy or export the results.

## Project Structure

```text
AI-Meeting-Assistant/
├── app/
│   ├── api/
│   │   ├── meeting.py
│   │   └── user.py
│   ├── auth/
│   │   ├── security.py
│   │   └── validator.py
│   ├── core/
│   │   ├── config.py
│   │   └── schemas.py
│   ├── database/
│   │   ├── database.py
│   │   └── models.py
│   └── middleware/
│       └── rate_limiter.py
├── alembic/
├── frontend/
│   ├── css/
│   ├── js/
│   │   ├── authentication.js
│   │   ├── script.js
│   │   └── runtime-config.js
│   ├── index.html
│   └── ...
├── alembic.ini
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The tree highlights the main architectural components; individual frontend files may vary as the interface evolves.*

## API Overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/meeting/summarize` | POST | Upload and summarize a meeting transcript |
| `/user/signup` | POST | Register a user |
| `/user/login` | POST | Authenticate a user |

The summarization endpoint accepts a transcript file and returns structured meeting notes. Authentication endpoints handle user registration and login.

## Structured Output

The generated notes are organized into four main sections:

- **Overview:** A concise summary of the meeting.
- **Discussion Points:** The main topics discussed.
- **Tasks and Deadlines:** Action items and associated deadlines.
- **Decisions:** Outcomes and decisions reached during the meeting.

Pydantic schemas provide a consistent response structure, allowing the frontend to render each section according to its content.

## Engineering Considerations

### Token Efficiency and Long Transcripts

Long meeting transcripts can increase input token consumption and exceed model context limits. The current development direction is to introduce token-aware processing and intelligent transcript chunking.

Planned improvements include:

- Estimating transcript token counts before making LLM requests.
- Splitting large transcripts at sensible textual boundaries.
- Summarizing or extracting relevant information from individual chunks before generating the final notes.
- Tracking per-user token consumption alongside summary usage.

### Transcript Preprocessing

Transcript exports can contain formatting artifacts, timestamps, filler words, and repeated statements. Preprocessing improvements are being explored to reduce unnecessary input while preserving the meaning and context of the original discussion.

Semantic similarity using SentenceTransformers and cosine similarity is being investigated for detecting redundant sentences.

### Usage Controls

The application is designed with configurable safeguards to help control resource consumption, including file-size limits, transcript-length limits, request-rate limits, and output-token constraints. Daily summary limits are also part of the usage-control design.

## Future Improvements

- Implement token-aware hierarchical summarization for long transcripts.
- Evaluate semantic deduplication while preserving decisions, deadlines, and speaker attribution.

## Development Status

This project is being developed incrementally, with a focus on modular backend design, structured LLM responses, transcript processing, and responsible resource usage.

## Author

**Rohan Patel**

Computer Science graduate interested in AI/ML engineering, backend development, and building practical AI-powered applications.

- GitHub: [Rohanpatel512](https://github.com/Rohanpatel512)
- Project: [AI Meeting Assistant](https://github.com/Rohanpatel512/AI-Meeting-Assistant)
