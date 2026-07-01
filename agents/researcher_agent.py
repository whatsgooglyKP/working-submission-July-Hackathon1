import os
from typing import Optional
from google.genai import types
from agents.base import BaseAgent, JobSpecification, CandidateProfile

# Default prompts for Researcher Agent
DEFAULT_JOB_PROMPT = """
You are a highly skilled technical recruiter and Job Reconnaissance Specialist.
Your task is to analyze the provided raw job description and extract a clear, accurate, and structured job specification.

Ensure you carefully extract:
1. Job Title (official, normalized)
2. Company Name
3. Job Location (including remote, hybrid, city, state)
4. Basic/Required Qualifications (minimum experience, degrees, mandatory skills)
5. Preferred/Nice-to-have Qualifications (specific frameworks, adjacent skills, certifications)
6. Technology Stack (explicit languages, tools, databases, cloud providers)
7. Vibe/Culture (enterprise, startup, research, fast-paced, highly collaborative, etc.)

Do not invent requirements that are not in the text, but use professional judgment to accurately categorize terms.
"""

DEFAULT_CANDIDATE_PROMPT = """
You are a Senior Talent sourcer and Resume Parsing Expert.
Your task is to parse a raw resume/candidate profile into a structured schema.

Ensure you carefully extract:
1. Full Name
2. Email Address
3. Phone Number
4. Technical Skills (categorized or structured into a flat list of technical capabilities)
5. Experience (company, role/title, start/end dates, and descriptions/achievements)
6. Projects (title, description, technologies/skills used)

CRITICAL: Maintain absolute fidelity to the provided candidate details.
Do not lose any dates, companies, or metrics. If contact information is incomplete, leave it or use default provided information if present.
"""

class ResearcherAgent(BaseAgent):
    """
    Researcher Agent is responsible for analyzing raw job descriptions and candidate resumes.
    It produces structured JobSpecification and CandidateProfile objects to be used as contracts by other agents.
    """
    def __init__(self):
        # We call super() twice or manage multiple prompts since this agent has two distinct responsibilities.
        super().__init__(
            name="Researcher Agent",
            system_prompt_file="researcher_general.txt",
            default_prompt_content="You are a Job Recon and Candidate Profiling agent."
        )
        # Load the specific system prompts
        self.job_system_prompt = self._load_sub_prompt("researcher_job.txt", DEFAULT_JOB_PROMPT)
        self.candidate_system_prompt = self._load_sub_prompt("researcher_candidate.txt", DEFAULT_CANDIDATE_PROMPT)

    def _load_sub_prompt(self, filename: str, default_content: str) -> str:
        from agents.base import load_prompt
        return load_prompt(filename, default_content)

    def analyze_job(self, job_title: str, raw_job_description: str) -> JobSpecification:
        """
        Analyzes raw job posting text and returns a structured JobSpecification.
        """
        client = self.get_client()
        prompt = f"""
        Analyze the following job description for the role: "{job_title}".
        
        --- RAW JOB DESCRIPTION ---
        {raw_job_description}
        """

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.job_system_prompt,
                response_mime_type="application/json",
                response_schema=JobSpecification,
                temperature=0.2,
            )
        )

        if response.parsed:
            return response.parsed
        raise ValueError("Researcher Agent failed to parse Job Specification.")

    def parse_candidate(self, raw_resume_text: str) -> CandidateProfile:
        """
        Parses raw resume/profile text and returns a structured CandidateProfile.
        """
        client = self.get_client()
        prompt = f"""
        Parse the following raw candidate resume/profile text.
        
        --- RAW CANDIDATE PROFILE ---
        {raw_resume_text}
        """

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.candidate_system_prompt,
                response_mime_type="application/json",
                response_schema=CandidateProfile,
                temperature=0.1,
            )
        )

        if response.parsed:
            return response.parsed
        raise ValueError("Researcher Agent failed to parse Candidate Profile.")
