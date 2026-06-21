import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from job_scraper import search_linkedin_jobs

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="EasyApplier AI Agent API",
    description="Backend API for the EasyApplier Job Application Agent, powered by Google Gemini",
    version="1.0.0"
)

# Configure CORS (useful for front-end integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ringed-land-397222")
APPHUB_APPLICATION = os.getenv("APPHUB_APPLICATION", "easyapplier")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize Gemini Client
# The SDK automatically uses GEMINI_API_KEY environment variable if not passed explicitly,
# but we pass it or check for it to provide helpful error messages.
if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY is not set. Please configure it in your environment or .env file.")
    client = None
else:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Define Input Pydantic Schemas
class ApplicationRequest(BaseModel):
    job_title: str = Field(..., description="The title of the job being applied for")
    job_description: str = Field(..., description="The full description/text of the job posting")
    resume_text: str = Field(None, description="The user's current resume text")
    user_notes: str = Field(None, description="Optional extra notes, instructions, or focus areas")

# Define Structured Output Pydantic Schemas for Gemini response
class ApplicationStrategy(BaseModel):
    match_score: int = Field(..., description="Overall fit score from 1 to 100")
    fit_summary: str = Field(..., description="A 3-4 sentence summary of why the candidate fits this role")
    cover_letter: str = Field(..., description="A professional, tailored cover letter based on the job and resume")
    tailored_resume: str = Field(..., description="A rewritten version of the candidate resume, fully optimized to align with the job description keywords")
    resume_suggestions: list[str] = Field(..., description="Bullet points suggesting specific updates to the resume to align with keywords")
    interview_prep: list[str] = Field(..., description="Top 3 likely interview questions with suggested talking points")

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Renders the dashboard UI from index.html."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error loading index.html: {str(e)}</h3>", status_code=500)

@app.get("/aligned_labs_logo.jpg")
async def get_logo():
    """Serves the generated Aligned Labs logo image."""
    logo_path = "aligned_labs_logo.jpg"
    if not os.path.exists(logo_path):
        logo_path = "C:/Users/pinar/.gemini/antigravity-cli/brain/5ab6de28-73cb-4611-8a6d-8d4c0c72d395/aligned_labs_logo_1781851225345.jpg"
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")

@app.get("/api/jobs")
async def get_linkedin_jobs(title: str, limit: int = 35):
    """Fetches recently posted job listings on LinkedIn guest search."""
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job title query parameter 'title' is required."
        )
    try:
        jobs = search_linkedin_jobs(title, limit=limit)
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping LinkedIn jobs: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Liveness probe used by Cloud Run/App Hub."""
    status_info = "healthy"
    if client is None:
        status_info = "warning_missing_api_key"
    return {
        "status": status_info,
        "service": "easyapplier-agent",
        "model_configured": GEMINI_MODEL
    }

@app.get("/api/info")
async def info():
    """Metadata about the GCP registration."""
    return {
        "gcp_project_id": GCP_PROJECT_ID,
        "apphub_application": APPHUB_APPLICATION,
        "region": "us-east1"
    }

@app.post("/api/apply", response_model=ApplicationStrategy)
async def analyze_application(request: ApplicationRequest):
    """
    Analyzes job description and resume, generating a custom strategy, 
    cover letter, and recommendations using Gemini structured outputs.
    """
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gemini Client is not configured. GEMINI_API_KEY is missing."
        )

    # Resolve resume text from local file if not supplied in payload
    resume_text_to_use = request.resume_text
    if not resume_text_to_use:
        try:
            import docx
            doc_path = "C:/Users/pinar/Google Kaggle 5DAYAI Vibe Coding Project/RESUME.Google.Day3.docx"
            if os.path.exists(doc_path):
                doc = docx.Document(doc_path)
                resume_text_to_use = "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            pass
    if not resume_text_to_use:
        resume_text_to_use = "Kevin Pinard - MS in AI Student. Proficient in Python. Set up Google Antigravity IDE and developed local test scripts. Experience with Gemini API."

    # Build prompt
    prompt = f"""
    You are an expert career advisor and job application optimization agent. 
    Analyze the job details and candidate resume below, then return a structured ApplicationStrategy.
    Specifically, rewrite the candidate's resume/profile to create a tailored, optimized resume that aligns with the job keywords, and place it in the `tailored_resume` field.

    Job Title: {request.job_title}
    
    Job Description:
    {request.job_description}
    
    Candidate Resume:
    {resume_text_to_use}
    """

    if request.user_notes:
        prompt += f"\nAdditional User Instructions/Focus Areas:\n{request.user_notes}"

    try:
        # Call Gemini utilizing Pydantic structured output constraints
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ApplicationStrategy,
                temperature=0.35,
            ),
        )
        
        # The SDK automatically parses the JSON response into our Pydantic model
        # when response_schema is passed. Let's return it directly.
        # Note: response.parsed contains the schema-validated object.
        if response.parsed:
            return response.parsed
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini response could not be parsed into the required schema."
            )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google GenAI API Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error processing request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    # Read port from environment (Cloud Run injects PORT environment variable)
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
