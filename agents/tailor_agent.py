import os
from typing import Optional, List
from google.genai import types
from agents.base import BaseAgent, JobSpecification, CandidateProfile, GapAnalysis, TailorOutput

DEFAULT_TAILOR_PROMPT = """
You are an Elite Resume Writer and Professional Career Copywriter.
Your goal is to perform a detailed comparison and alignment check, and craft a 100% complete, submission-ready, highly tailored resume, cover letter, and interview prep guide.

========================================================================
CORE MANDATE: SUBMISSION-READY TAILORED RESUME (NO TEMPLATES OR PLACEHOLDERS)
- In the `tailored_resume` field, rewrite the candidate's resume/profile to create a fully tailored, optimized resume in standard clean Markdown.
- This resume must be 100% COMPLETE and ready to be submitted.
- There must be absolutely NO placeholders, incomplete sections, or templates (like '[insert project]', 'your.email@example.com', or 'kevin.pinard@email.com').
- You MUST use the actual candidate details provided in the profile:
  * Full Name: Kevin Scott Pinard
  * Email Address: Kevinpolymath@gmail.com
  * Phone Number: 352-406-3847
  * Portfolio Links: LinkedIn (https://www.linkedin.com/in/pinardkevin), GitHub (https://github.com/kevinpolymath), Tableau
  * Location: Orlando, FL
- Carefully verify and incorporate these exact real details in the tailored resume and cover letter.

========================================================================
STYLE AND FORMATTING:
- Resume should use clear, elegant Markdown headers, bullet points, bold text for key terms, and modern design layouts.
- Cover Letter should be professional, compelling, 3-4 paragraphs, perfectly styled in Markdown, addressed to the hiring manager or company.
- Interview Prep should contain exactly 3 high-probability questions custom-tailored to the role and projects, with actionable talking points.
"""

class TailorAgent(BaseAgent):
    """
    Tailor Agent is responsible for the actual generation and refinement of tailored documents (Resumes, Cover Letters, Interview Prep).
    It takes the analytical blueprint from the Strategist Agent and crafts submission-ready artifacts.
    """
    def __init__(self):
        super().__init__(
            name="Tailor Agent",
            system_prompt_file="tailor_application.txt",
            default_prompt_content=DEFAULT_TAILOR_PROMPT
        )

    def tailor_application(
        self, 
        job_spec: JobSpecification, 
        candidate_profile: CandidateProfile, 
        gap_analysis: GapAnalysis, 
        previous_feedback: Optional[List[str]] = None
    ) -> TailorOutput:
        """
        Generates/tailors resume, cover letter, and interview prep.
        Can incorporate previous feedback if iterating from an audit failure.
        """
        client = self.get_client()
        prompt = f"""
        Draft the tailored resume, cover letter, and interview prep guide.
        
        --- JOB SPECIFICATION ---
        {job_spec.model_dump_json(indent=2)}
        
        --- CANDIDATE PROFILE ---
        {candidate_profile.model_dump_json(indent=2)}
        
        --- STRATEGIC GAP ANALYSIS & BLUEPRINT ---
        {gap_analysis.model_dump_json(indent=2)}
        """

        if previous_feedback:
            prompt += f"""
            
            ========================================================================
            ⚠️ CRITICAL REVISION REQUESTS FROM THE AUDITOR:
            The previous draft failed the quality audit. You MUST correct the following issues in this version:
            {chr(10).join(f"- {f}" for f in previous_feedback)}
            ========================================================================
            """

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                response_mime_type="application/json",
                response_schema=TailorOutput,
                temperature=0.35,
            )
        )

        if response.parsed:
            return response.parsed
        raise ValueError("Tailor Agent failed to generate tailored application documents.")
