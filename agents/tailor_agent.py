import os
from typing import Optional, List
from google.genai import types
from agents.base import BaseAgent, JobSpecification, CandidateProfile, GapAnalysis, TailorOutput

DEFAULT_TAILOR_PROMPT = """
You are an Elite Resume Writer.

Your ONLY job is to produce:
1. match_score: integer from 1-100
2. tailored_resume: complete submission-ready resume in clean Markdown.

Use candidate details from the profile provided.
Optimize heavily for job qualifications.
Include a strong Skills section.

No cover letter. No interview prep. Keep output minimal and clean.
"""

class TailorAgent(BaseAgent):
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
        client = self.get_client()
        prompt = f"""
        Draft the tailored resume.

        --- JOB SPECIFICATION ---
        {job_spec.model_dump_json(indent=2)}

        --- CANDIDATE PROFILE ---
        {candidate_profile.model_dump_json(indent=2)}

        --- STRATEGIC GAP ANALYSIS ---
        {gap_analysis.model_dump_json(indent=2)}
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
        raise ValueError("Tailor Agent failed to generate output.")