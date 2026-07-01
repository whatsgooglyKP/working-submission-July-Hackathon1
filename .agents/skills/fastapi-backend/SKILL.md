---
name: fastapi-backend
description: Expert guidelines, endpoints structure, and development patterns for building the EasyApplier FastAPI backend REST API.
---

# FastAPI Backend API Development Skill

Use this skill when developing, refactoring, or extending the FastAPI-based backend REST API for EasyApplier located in `main.py`.

## Core Guidelines & Principles

1. **Structured Request & Response Models**:
   - Every input payload must be typed and validated using Pydantic `BaseModel`.
   - Fields should specify descriptions to enforce clean API contracts and self-documenting endpoints.
   - Match schemas between Streamlit state and FastAPI response structures to guarantee full compliance.

2. **CORS & Middleware Safety**:
   - Correctly configure `CORSMiddleware` to allow external front-end integrations.
   - Secure and load environment variables safely with `dotenv`.

3. **Fallback Robustness**:
   - Handle environment defaults and physical file pathways elegantly (such as local resumes and backup logo assets).
   - Return appropriate HTTP error status codes (e.g., `404` for missing files, `400` for bad payloads, `502` for third-party API issues, and `500` for overall system exceptions).

4. **Integration Hooks**:
   - Connect endpoints smoothly to backend scrapers (`job_scraper.py`) and GenAI models (`google-genai` SDK).
   - Leverage Pydantic models as response schemas inside GenAI configurations for automatic end-to-end schema validation.

---

## Code Patterns

### Standard Application Bootstrapping
```python
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="EasyApplier AI Agent API",
    description="Backend API for the EasyApplier Job Application Agent, powered by Google Gemini",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Endpoint Definition Pattern
Define clear paths, HTTP methods, response models, and descriptions:
```python
class ApplicationRequest(BaseModel):
    job_title: str = Field(..., description="The title of the job being applied for")
    job_description: str = Field(..., description="The full description/text of the job posting")
    resume_text: str = Field(None, description="The user's current resume text")
    user_notes: str = Field(None, description="Optional extra notes, instructions, or focus areas")

@app.post("/api/apply", response_model=ApplicationStrategy)
async def analyze_application(request: ApplicationRequest):
    # Perform logic here...
    pass
```

### Static Asset serving & File fallbacks
```python
from fastapi.responses import FileResponse

@app.get("/aligned_labs_logo.jpg")
async def get_logo():
    """Serves the generated logo image with absolute and relative fallbacks."""
    logo_path = "aligned_labs_logo.jpg"
    if not os.path.exists(logo_path):
        logo_path = "C:/Users/pinar/.gemini/antigravity-cli/brain/.../aligned_labs_logo.jpg"
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")
```

### Service Health Checks (Cloud Run & App Hub Compatible)
```python
@app.get("/health")
async def health_check():
    """Liveness probe used by container runners/App Hub."""
    status_info = "healthy"
    if client is None:
        status_info = "warning_missing_api_key"
    return {
        "status": status_info,
        "service": "easyapplier-agent"
    }
```
