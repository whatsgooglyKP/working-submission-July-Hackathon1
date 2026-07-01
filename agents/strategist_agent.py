import os
from typing import Optional, List
from google.genai import types
from agents.base import BaseAgent, JobSpecification, CandidateProfile, GapAnalysis, AuditResult

DEFAULT_GAP_PROMPT = """
You are a Senior Career Strategist and Talent Alignment Specialist.
Your task is to perform an exhaustive, section-by-section comparison between a Job Specification and a Candidate Profile.

Analyze:
1. Skills vs Tech Stack & Qualifications
2. Experience vs Basic & Preferred Qualifications
3. Candidate projects vs job responsibilities

Based on this analysis, you must output a structured GapAnalysis including:
- Match score (1-100)
- fit_summary (3-4 sentences outlining why the candidate is a strong fit or what adjacent/transferable skills compensate)
- direct_matches (explicit matches of technical skills or experience)
- gap_areas (areas where the candidate is missing or weak relative to job requirements)
- tailoring_instructions (strategic instructions/blueprint on how the resume/cover letter should highlight matches, reframe experience, and bridge gaps)
"""

DEFAULT_AUDIT_PROMPT = """
You are a strict, production-grade Quality Assurance Auditor for professional resume and cover letter tailoring.
Your task is to critique draft application documents (resume and cover letter) against the Job Specification, Candidate Profile, and Gap Analysis blueprint.

CRITICAL CHECKS:
1. PLACEHOLDER TEST: Verify there are absolutely NO placeholder tags, template marks, or incomplete sections like "[Insert Date]", "[Phone]", "[Your Name]", "your.email@example.com", or incorrect credentials.
2. FIDELITY TEST: Verify that all details are accurate to the candidate profile (Kevin Scott Pinard, Kevinpolymath@gmail.com, etc.).
3. STYLE AND TONE: Ensure high-quality professional Markdown with no spelling errors, and that it conforms to the strategist's tailoring instructions.

Output an AuditResult:
- approved: True only if ALL checks pass.
- feedback_notes: Bulleted constructive feedback detailing exactly what needs to be fixed if rejected.
- placeholder_check_passed: True only if absolutely zero placeholder patterns or unresolved bracketed fields remain.
"""

class StrategistAgent(BaseAgent):
    """
    Strategist Agent is the analytical and auditing brain of the multi-agent system.
    It performs gap analyses to guide tailoring, and audits draft outputs for quality and placeholders.
    """
    def __init__(self):
        super().__init__(
            name="Strategist Agent",
            system_prompt_file="strategist_general.txt",
            default_prompt_content="You are a Career Strategist and Quality Assurance Agent."
        )
        self.gap_system_prompt = self._load_sub_prompt("strategist_gap.txt", DEFAULT_GAP_PROMPT)
        self.audit_system_prompt = self._load_sub_prompt("strategist_audit.txt", DEFAULT_AUDIT_PROMPT)

    def _load_sub_prompt(self, filename: str, default_content: str) -> str:
        from agents.base import load_prompt
        return load_prompt(filename, default_content)

    def analyze_gaps(self, job_spec: JobSpecification, candidate_profile: CandidateProfile, user_notes: Optional[str] = None) -> GapAnalysis:
        """
        Compares JobSpecification and CandidateProfile to produce a structured GapAnalysis.
        """
        client = self.get_client()
        prompt = f"""
        Perform a gap analysis between the following Job Specification and Candidate Profile.
        
        --- JOB SPECIFICATION ---
        {job_spec.model_dump_json(indent=2)}
        
        --- CANDIDATE PROFILE ---
        {candidate_profile.model_dump_json(indent=2)}
        """
        if user_notes:
            prompt += f"\n--- ADDITIONAL USER INSTRUCTIONS ---\n{user_notes}"

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.gap_system_prompt,
                response_mime_type="application/json",
                response_schema=GapAnalysis,
                temperature=0.2,
            )
        )

        if response.parsed:
            return response.parsed
        raise ValueError("Strategist Agent failed to perform Gap Analysis.")

    def audit_documents(
        self, 
        job_spec: JobSpecification, 
        candidate_profile: CandidateProfile, 
        gap_analysis: GapAnalysis, 
        tailored_resume: str, 
        cover_letter: str
    ) -> AuditResult:
        """
        Critiques drafted documents for quality, accuracy, compliance, and placeholders.
        """
        client = self.get_client()
        prompt = f"""
        Audit the drafted tailored resume and cover letter based on the Job Specification, Candidate Profile, and Gap Analysis blueprint.
        
        --- JOB SPECIFICATION ---
        {job_spec.model_dump_json(indent=2)}
        
        --- CANDIDATE PROFILE ---
        {candidate_profile.model_dump_json(indent=2)}
        
        --- GAP ANALYSIS BLUEPRINT ---
        {gap_analysis.model_dump_json(indent=2)}
        
        --- DRAFTED RESUME (MARKDOWN) ---
        {tailored_resume}
        
        --- DRAFTED COVER LETTER (MARKDOWN) ---
        {cover_letter}
        """

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.audit_system_prompt,
                response_mime_type="application/json",
                response_schema=AuditResult,
                temperature=0.1,
            )
        )

        if response.parsed:
            return response.parsed
        raise ValueError("Strategist Agent failed to audit documents.")
