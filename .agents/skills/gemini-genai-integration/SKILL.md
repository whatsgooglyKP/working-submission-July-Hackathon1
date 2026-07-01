---
name: gemini-genai-integration
description: Guidelines and patterns for integrating the new google-genai SDK for structured JSON responses mapped to Pydantic models.
---

# Google Gemini GenAI Integration Skill

Use this skill when developing, refactoring, or extending the integration with Google's Gemini models using the modern `google-genai` python library.

## Core Guidelines & Principles

1. **Modern Client Initialisation**:
   - Always import from `google` instead of legacy libraries:
     ```python
     from google import genai
     from google.genai import types
     from google.genai.errors import APIError
     ```
   - Initialize client using `client = genai.Client(api_key=...)`. If `api_key` isn't supplied, the SDK will automatically read `GEMINI_API_KEY` from the system environment variables.

2. **Strict Structured Output Mapping**:
   - Utilize standard Pydantic models as schema constraints to guarantee JSON outputs conform to precise typing.
   - Set `response_mime_type="application/json"` and `response_schema=YourPydanticModel` in the `GenerateContentConfig` object.
   - Access the typed response directly through `response.parsed`. Never perform manual string cleaning or `json.loads(response.text)` unless a parsing failure occurs.

3. **Optimised Parameter Selection**:
   - Maintain a lower temperature (e.g., `0.35`) for analytical or structured tasks to enforce factual correctness and lower hallucinations.
   - Use default model parameters such as `gemini-2.5-flash` or `gemini-2.5-pro` for balanced cost and speed vs deep comprehension.

4. **Robust Error Resilience**:
   - Wrap all API queries inside a try-except structure catching both `APIError` (SDK-specific exception class) and generic python `Exception`.
   - Provide clear, user-friendly warnings or exit gracefully rather than throwing raw trace logs.

---

## Code Patterns

### Structured Output Configuration and Model Call
```python
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field

# 1. Define target Schema
class ApplicationStrategy(BaseModel):
    match_score: int = Field(..., description="Overall fit score from 1 to 100")
    fit_summary: str = Field(..., description="A 3-4 sentence summary of why the candidate fits this role")
    cover_letter: str = Field(..., description="A professional, tailored cover letter based on the job and resume")
    tailored_resume: str = Field(..., description="A rewritten version of the candidate resume, fully optimized")
    resume_suggestions: list[str] = Field(..., description="Bullet points suggesting specific updates")
    interview_prep: list[str] = Field(..., description="Top likely interview questions")

# 2. Setup Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 3. Request generation with schema constraints
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Some prompt referencing the job description and candidate resume...",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ApplicationStrategy,
            temperature=0.35,
        ),
    )
    
    # 4. Access the parsed object safely
    if response.parsed:
        strategy: ApplicationStrategy = response.parsed
        print(f"Match Score: {strategy.match_score}%")
    else:
        print("[ERROR] Response failed schema constraints parsing.")
        
except APIError as e:
    print(f"[ERROR] Google GenAI API Connection failed: {e}")
except Exception as e:
    print(f"[ERROR] General exception during model execution: {e}")
```
