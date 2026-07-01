import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.oauth2.credentials import Credentials

# Locate prompts directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

def get_fresh_gcloud_token() -> Optional[str]:
    """Helper to dynamically print fresh gcloud credentials."""
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            shell=True,
            stderr=subprocess.DEVNULL
        ).strip()
        if token:
            return token
    except Exception:
        pass
    return None

def get_gemini_client() -> genai.Client:
    """Helper to initialize the Google GenAI Client with auto-refreshing OAuth support."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    project_id = os.getenv("GCP_PROJECT_ID", "ringed-land-397222")
    
    if api_key and (api_key.startswith("ya29.") or api_key.startswith("AQ.")):
        fresh_token = get_fresh_gcloud_token()
        if fresh_token:
            api_key = fresh_token
            
    if not api_key:
        print("[WARNING] GEMINI_API_KEY is empty. Falling back to default SDK initialization.")
        return genai.Client()
        
    if api_key.startswith("ya29.") or api_key.startswith("AQ."):
        # Prevent env variables from overriding Vertex AI OAuth setup
        orig_gemini_key = os.environ.pop("GEMINI_API_KEY", None)
        orig_google_key = os.environ.pop("GOOGLE_API_KEY", None)
        creds = Credentials(token=api_key)
        try:
            return genai.Client(
                vertexai=True,
                project=project_id,
                location="us-east1",
                credentials=creds
            )
        finally:
            if orig_gemini_key is not None:
                os.environ["GEMINI_API_KEY"] = orig_gemini_key
            if orig_google_key is not None:
                os.environ["GOOGLE_API_KEY"] = orig_google_key
    else:
        return genai.Client(api_key=api_key)

def load_prompt(filename: str, default_content: str = "") -> str:
    """Load a system prompt from the prompts/ directory, creating it if it doesn't exist."""
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    filepath = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(default_content.strip())
        return default_content.strip()
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

# ==========================================
# 📊 SHARED STRUCTURED HANDOFF SCHEMAS
# ==========================================

class JobSpecification(BaseModel):
    """The structured output of the Job Recon / Researcher Agent."""
    title: str = Field(..., description="The official title of the job")
    company: str = Field(..., description="The name of the company posting the job")
    location: str = Field(..., description="The job location (e.g., hybrid, remote, city)")
    basic_qualifications: List[str] = Field(..., description="Minimum/required qualifications like experience years, degree, core skills")
    preferred_qualifications: List[str] = Field(..., description="Preferred, nice-to-have qualifications like specific libraries, stack or certs")
    tech_stack: List[str] = Field(..., description="Core technologies, frameworks and databases mentioned in the description")
    vibe: str = Field(..., description="The tone/culture of the posting (e.g., fast-paced startup, formal enterprise, research-focused)")

class CandidateProfile(BaseModel):
    """The structured output of the Resume parser inside Researcher Agent."""
    name: str = Field(..., description="Candidate's full name")
    email: str = Field(..., description="Candidate's email address")
    phone: str = Field(..., description="Candidate's phone number")
    skills: List[str] = Field(..., description="Core technical skills listed or inferred")
    experience: List[Dict[str, Any]] = Field(..., description="List of past jobs, each with role, company, dates and descriptions")
    projects: List[Dict[str, Any]] = Field(..., description="List of projects, each with title, description, and technologies used")

class GapAnalysis(BaseModel):
    """The structured output of the Alignment / Strategist Agent."""
    match_score: int = Field(..., description="Overall match score from 1 to 100 based on qualifications")
    fit_summary: str = Field(..., description="3-4 sentences outlining why the candidate is a strong fit or what adjacent skills compensate")
    direct_matches: List[str] = Field(..., description="Explicit qualifications from job spec that candidate fully meets")
    gap_areas: List[str] = Field(..., description="Required/Preferred qualifications candidate is missing or weak in")
    tailoring_instructions: str = Field(..., description="Strategic blueprint instructions on how the resume/cover letter should highlight matches and bridge gaps")

class TailorOutput(BaseModel):
    """The structured output of the Tailor Agent."""
    tailored_resume: str = Field(..., description="The optimized resume in high-quality Markdown format, meticulously incorporating tailoring instructions")
    cover_letter: str = Field(..., description="A professional, bespoke cover letter in Markdown format aligning skills to job specs")
    interview_prep: List[str] = Field(..., description="Top 3 highly probable interview questions based on candidate projects/role, with talking points")

class AuditResult(BaseModel):
    """The structured output of the Quality Assurance Auditor."""
    approved: bool = Field(..., description="True if documents have no placeholders, read perfectly, and meet tailoring instructions")
    feedback_notes: List[str] = Field(..., description="Explicit correction requests or notes explaining gaps to fix")
    placeholder_check_passed: bool = Field(..., description="True if no placeholders like [Insert Date], [Phone], kevin.pinard@email.com are present")

# ==========================================
# 🧠 BASE AGENT CONTRACT
# ==========================================

class BaseAgent(ABC):
    """Abstract base class for all EasyApplier specialized agents."""
    def __init__(self, name: str, system_prompt_file: str, default_prompt_content: str):
        self.name = name
        self.system_prompt = load_prompt(system_prompt_file, default_prompt_content)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
    def get_client(self) -> genai.Client:
        """Retrieves a freshly authenticated client instance."""
        return get_gemini_client()
