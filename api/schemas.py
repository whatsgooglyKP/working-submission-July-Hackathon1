from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from agents.base import JobSpecification, CandidateProfile, GapAnalysis, TailorOutput, AuditResult

class ApplicationRequest(BaseModel):
    """The request schema for launching the EasyApplier tailoring workflow."""
    job_title: str = Field(..., description="The title of the job being applied for")
    job_description: str = Field(..., description="The full description/text or LinkedIn URL of the job posting")
    resume_text: Optional[str] = Field(None, description="The user's current resume text. If omitted, the default candidate profile is loaded.")
    user_notes: Optional[str] = Field(None, description="Optional extra notes, instructions, or focus areas")

class ApplicationStrategy(BaseModel):
    """The tailored resume output schema containing only the generated optimized resume."""
    tailored_resume: str = Field(..., description="A rewritten version of the candidate resume, fully optimized in standard clean Markdown format to align with the job description keywords")

class APIOrchestratorResult(BaseModel):
    """The complete response schema returning the full multi-agent workflow results."""
    success: bool = Field(..., description="Whether the quality audit passed")
    iterations: int = Field(..., description="Number of iterative tailoring-auditing loops performed")
    job_spec: JobSpecification = Field(..., description="The parsed job specifications from the Researcher Agent")
    candidate_profile: CandidateProfile = Field(..., description="The parsed candidate profile from the Researcher Agent")
    gap_analysis: GapAnalysis = Field(..., description="The computed alignment gap analysis from the Strategist Agent")
    tailor_output: TailorOutput = Field(..., description="The final tailored application documents from the Tailor Agent")
    audit_history: List[AuditResult] = Field(..., description="The full audit history critiques across all iterations")
    final_audit: AuditResult = Field(..., description="The final Quality Assurance Audit result")
