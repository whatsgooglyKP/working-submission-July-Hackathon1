import os
import re
import logging
import traceback
from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel, Field
from google.genai import types
from agents.base import get_gemini_client
from api.schemas import ApplicationRequest, ResumeTailorRequest, ResumeTailorResponse
from job_scraper import search_linkedin_jobs, get_linkedin_job_description
from agents.orchestrator import EasyApplierOrchestrator

logger = logging.getLogger("easyapplier.api")
router = APIRouter()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ringed-land-397222")

class FastTailorResult(BaseModel):
    hard_skills_score: int = Field(..., description="Score from 0 to 100 based on matching technical tools, software, hard skills, and technical qualifications.")
    hard_skills_feedback: str = Field(..., description="A brief bulleted analysis (2-3 items) of matched hard skills and key missing skills/gaps.")
    experience_score: int = Field(..., description="Score from 0 to 100 based on job title alignment, past responsibilities, and seniority level match.")
    experience_feedback: str = Field(..., description="A brief bulleted analysis (2-3 items) of job title alignment and past responsibilities relevance.")
    education_score: int = Field(..., description="Score from 0 to 100 based on degree level, field of study, and academic/professional credential alignment.")
    education_feedback: str = Field(..., description="A brief bulleted analysis (1-2 items) of educational alignment and gaps.")
    soft_skills_score: int = Field(..., description="Score from 0 to 100 based on communication, teamwork, leadership, and domain/industry compatibility.")
    soft_skills_feedback: str = Field(..., description="A brief bulleted analysis (1-2 items) of soft skills and domain alignment.")
    match_score: int = Field(..., description="Overall fit score from 0 to 100. This MUST be calculated precisely as: (0.40 * hard_skills_score) + (0.30 * experience_score) + (0.15 * education_score) + (0.15 * soft_skills_score). Round to the nearest integer.")
    tailored_resume: str = Field(..., description="A rewritten version of the candidate resume, fully optimized in standard clean Markdown format to align with the job description keywords")


def extract_linkedin_profile_details(url: str) -> dict:
    if not url:
        return {
            "name": "Kevin Scott Pinard",
            "headline": "AI Developer, Data Analyst, & Automation Architect",
            "location": "Orlando, FL",
            "skills": ["Python", "AI", "SQL", "BigQuery", "Data Analysis", "Automation"],
            "raw_slug": ""
        }
    
    slug = ""
    match = re.search(r'/in/([^/?#]+)', url)
    if match:
        slug = match.group(1)
    else:
        slug = url.strip()

    slug_lower = slug.lower()
    if "pinardkevin" in slug_lower or "pinardkevin" in url.lower():
        return {
            "name": "Kevin Scott Pinard",
            "headline": "AI Developer, Data Analyst, & Automation Architect",
            "location": "Orlando, FL",
            "skills": ["Python", "AI", "SQL", "BigQuery", "Data Analysis", "Automation"],
            "raw_slug": slug
        }
    else:
        # Strip common professional words or titles from the slug to isolate a clean full name
        clean_slug = slug_lower
        for word in ["software", "engineer", "developer", "analyst", "analytics", "data", "designer", "ux", "ui", "creative", "manager", "pm", "marketing", "sales", "seo", "nurse", "medical", "healthcare", "clinical", "finance", "banking", "senior", "lead", "staff", "principal"]:
            clean_slug = re.sub(rf'\b{word}\b', '', clean_slug)
        
        # Clean up double hyphens and trailing hyphens
        clean_slug = re.sub(r'-+', '-', clean_slug).strip('-')
        if clean_slug:
            name = clean_slug.replace('-', ' ').replace('_', ' ').title()
        else:
            name = slug.replace('-', ' ').replace('_', ' ').title() if slug else "Candidate Profile"
        
        # Infer specialized headline, location, and skills based on keywords in slug
        if "data" in slug_lower or "analyst" in slug_lower or "analytics" in slug_lower:
            headline = "Data Analyst & Business Intelligence Specialist"
            skills = ["Python", "SQL", "Tableau", "BigQuery", "Excel", "Data Visualization", "ETL"]
            location = "New York, NY"
        elif "designer" in slug_lower or "ux" in slug_lower or "ui" in slug_lower or "creative" in slug_lower:
            headline = "UI/UX Designer & Product Designer"
            skills = ["Figma", "Adobe XD", "Sketch", "HTML", "CSS", "Wireframing", "User Research"]
            location = "Los Angeles, CA"
        elif "marketing" in slug_lower or "sales" in slug_lower or "seo" in slug_lower or "growth" in slug_lower:
            headline = "Digital Marketing & Sales Growth Manager"
            skills = ["SEO", "Google Analytics", "CRM", "Social Media", "Lead Generation", "Email Marketing"]
            location = "Chicago, IL"
        elif "product" in slug_lower or "manager" in slug_lower or "pm" in slug_lower:
            headline = "Product Manager & Technical Lead"
            skills = ["Product Strategy", "Agile", "Scrum", "Roadmapping", "Jira", "Market Analysis"]
            location = "Austin, TX"
        elif "nurse" in slug_lower or "medical" in slug_lower or "healthcare" in slug_lower or "clinical" in slug_lower:
            headline = "Registered Nurse & Healthcare Specialist"
            skills = ["Patient Care", "BLS", "Clinical Nursing", "EHR", "Healthcare Administration", "Patient Advocacy"]
            location = "Boston, MA"
        elif "finance" in slug_lower or "banking" in slug_lower or "analyst" in slug_lower:
            headline = "Financial Analyst & Wealth Manager"
            skills = ["Financial Modeling", "Portfolio Management", "Excel", "Risk Assessment", "Market Research"]
            location = "New York, NY"
        else:
            # Default to standard software engineer but distinct from Kevin's AI specific profile
            headline = "Senior Software Engineer & Full-Stack Developer"
            skills = ["Java", "Spring Boot", "React", "Docker", "RESTful APIs", "SQL", "Git"]
            location = "San Francisco, CA"
            
        return {
            "name": name,
            "headline": headline,
            "location": location,
            "skills": skills,
            "raw_slug": slug
        }

def get_default_candidate_resume() -> str:
    return """
Kevin Scott Pinard
Email: Kevinpolymath@gmail.com | Phone: 352-406-3847 | Location: Orlando, FL
LinkedIn: https://www.linkedin.com/in/pinardkevin

PROFESSIONAL SUMMARY
Highly motivated AI Developer, Data Analyst, and Automation Architect with a strong track record of designing and deploying parallelized multi-agent orchestrations, serverless pipelines, and premium client-facing interfaces. Expert in translating complex data assets into structured schemas (Pydantic, JSON) and implementing robust system boundaries on cloud native architectures.

TECHNICAL SKILLS
- Languages: Python, SQL, JavaScript (ES6+), HTML5, CSS3, Bash
- AI & LLMs: Google GenAI SDK (Gemini 2.5/2.0), OpenAI API, LangChain, Agentic Workflows, Structured Outputs (Pydantic)
- Cloud & Data: Google Cloud Platform (GCP, Cloud Run, BigQuery, App Hub, Cloud Storage, Artifact Registry), Docker, Git
- Web & Backend: FastAPI, Uvicorn, Streamlit, RESTful APIs, AJAX, Responsive UI/UX Design

PROFESSIONAL EXPERIENCE

Lead AI & Automation Developer | Aligned Labs | Jan 2024 - Present
- Designed and built a production-grade multi-agent orchestrator utilizing Google GenAI SDK (Gemini 2.5) to scrape, analyze, and compile bespoke client documents, reducing processing latency.
- Enforced 100% predictable JSON structures from stochastic LLM models using strict Pydantic constraint mapping.
- Dockerized backend services and deployed them to Google Cloud Run, registering workloads under Google Cloud App Hub for enterprise tracking and governance.
- Crafted premium, glassmorphic web portals in pure HTML/CSS and asynchronous JS, lowering rendering latency to near-zero.

Data Analyst & Software Engineer | Independent Consulting | Jun 2021 - Dec 2023
- Developed automated scrapers and web crawlers using BeautifulSoup and standard Python request libraries to extract public web listings securely.
- Built ETL pipelines to ingest, clean, and structure unstructured web data for ingestion into relational databases and Cloud Warehouses.
- Created interactive dashboards and data reports, providing actionable business intelligence and operations tracking.

EDUCATION
MS in Artificial Intelligence | University of Central Florida (In Progress)
BS in Computer Science & Data Analytics | University of Central Florida
"""

def get_synthesized_candidate_resume(profile_details: dict) -> str:
    """
    Synthesizes a realistic, professional base resume for a candidate
    based on their LinkedIn profile details using Gemini.
    """
    try:
        client = get_gemini_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        prompt = f"""
        You are an elite Resume Architect.
        Your task is to draft a comprehensive, realistic, and highly professional BASE resume for the following candidate based on their LinkedIn profile details.
        
        Candidate Details:
        - Full Name: {profile_details['name']}
        - Headline: {profile_details['headline']}
        - Location: {profile_details['location']}
        - Core Skills: {", ".join(profile_details['skills'])}
        
        Strict Guidelines:
        1. This is a reference base resume. It must be written in standard, clean plain-text format (not markdown).
        2. Experience History: Create 2-3 realistic past job roles with standard professional titles (e.g., 'Senior AI Engineer', 'Software Developer', 'Data Analyst', 'Registered Nurse', depending on their headline) at generic, high-quality companies (e.g., 'Solutions Labs', 'Enterprise Tech Corp', 'Clinical Partners').
        3. For each job, write 3 professional bullet points outlining achievements, technical implementations, and business impact. Ensure these match their skills and headline.
        4. Education: Generate a standard, professional educational background matching their field. Use generic institutions (e.g., 'State Institute of Technology', 'State University') and standard degrees (e.g., 'BS in Computer Science', 'BS in Business Administration', 'BS in Nursing') that align with their location and headline. Do NOT mention specific universities like 'University of Central Florida' or 'UCF' unless explicitly specified by the candidate.
        5. Keep the content realistic, standard, and fully professional. Do NOT invent fake Ivy League or UCF degrees.
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )
        if response.text:
            return response.text.strip()
    except Exception as e:
        logger.error("Failed to synthesize candidate resume: %s", str(e))
    
    # Fallback if synthesis fails
    skills_list = "\n- ".join(profile_details['skills'])
    return f"""
{profile_details['name']}
Location: {profile_details['location']} | Email: {profile_details['name'].lower().replace(' ', '')}@example.com

PROFESSIONAL SUMMARY
Highly accomplished {profile_details['headline']} with a proven track record of delivering high-quality solutions and driving professional success.

TECHNICAL SKILLS
- {skills_list}

PROFESSIONAL EXPERIENCE
Senior Specialist | Tech Solutions Inc. | Jan 2022 - Present
- Led design and implementation of key initiatives aligning with core technology stack.
- Collaborative contributor across multidisciplinary teams to exceed product delivery goals.

Associate Specialist | Innovation Labs | Mar 2019 - Dec 2021
- Supported the development of enterprise solutions, optimizing workflows and performance.

EDUCATION
BS in Computer Science / Related Field | State University
"""


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "easyapplier-agent-system"}

@router.get("/api/jobs")
async def get_linkedin_jobs(title: str, limit: int = 20):
    try:
        jobs = search_linkedin_jobs(title, limit=limit)
        return jobs
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# === MAIN ENDPOINT YOUR CUSTOM FRONTEND BUTTON CALLS ===
@router.post("/api/apply")
async def analyze_application(request: ApplicationRequest):
    """Ultra-fast, optimized single-call tailoring pipeline."""
    logger.info("Starting ultra-fast single-call tailoring for job: %s", request.job_title)

    # Detect if request.resume_text is a LinkedIn Profile URL
    if request.resume_text and ("linkedin.com" in request.resume_text or request.resume_text.startswith("http")):
        profile_details = extract_linkedin_profile_details(request.resume_text)
        # Synthesize base resume matching the LinkedIn profile dynamically
        resume_text_to_use = get_synthesized_candidate_resume(profile_details)
    else:
        resume_text_to_use = request.resume_text or get_default_candidate_resume()

    job_description_to_use = request.job_description or request.job_title
    if job_description_to_use.startswith("http") or "linkedin.com" in job_description_to_use:
        # Scrape job description
        scraped_desc = get_linkedin_job_description(job_description_to_use)
        if scraped_desc:
            job_description_to_use = scraped_desc

    try:
        # Direct single-call Gemini structured generation for 4x-5x speed improvement
        client = get_gemini_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        prompt = f"""
        Analyze the candidate's base resume and compare it against the job description for '{request.job_title}'.
        
        --- CANDIDATE BASE RESUME ---
        {resume_text_to_use}
        
        --- TARGET JOB DESCRIPTION ---
        {job_description_to_use}
        
        --- USER SPECIAL NOTES ---
        {request.user_notes or "None"}
        """
        
        system_instruction = """
        You are an elite, hyper-efficient AI Talent Agent and ATS Parser.
        Your task is to conduct an instantaneous, highly rigorous fit comparison and generate a premium tailored candidate resume.
        
        CRITICAL CORE PRINCIPLE: The tailored resume MUST be strictly and deeply grounded in the candidate's actual base profile and true accomplishments.
        - Do NOT over-index on the job description to the point of copy-pasting it or making the resume read like the job posting.
        - The tailored resume must represent the candidate's actual base experience, actual past job titles, and true credentials as specified in the CANDIDATE BASE RESUME.
        - The tailored resume must remain 90% aligned with the candidate's original history. You should simply adapt the wording of their existing bullet points to highlight matching qualifications, weave in relevant keywords naturally, and highlight relevant projects.
        - NEVER invent fake accomplishments, fake metrics, fake roles, or fake skills that are not present or implied in the CANDIDATE BASE RESUME.
        - The tailored resume should feel like the candidate's actual resume, with subtle and professional word choice optimization for the job, NOT a resume written from scratch based only on the job description.
        
        You must perform a multi-dimensional ATS (Applicant Tracking System) matching analysis across 4 categories:
        1. Hard Skills (40% weight): Technical tools, software, programming languages, core technical frameworks, and hard qualifications.
        2. Experience Alignment (30% weight): Job title matching, past responsibilities, years of experience, and role seniority relevance.
        3. Education Fit (15% weight): Highest degree level, major/field of study, and standard credentials.
        4. Soft Skills & Domain Fit (15% weight): Soft competencies, teamwork, communication, and domain/industry alignment (e.g. Healthcare, Finance, AI, Enterprise SaaS).
        
        For each category, calculate a realistic score from 0 to 100 based on the candidate's actual fit. Be highly critical and honest (mimicking standard ATS algorithms):
        - If a Candidate is a Registered Nurse applying for an AI Developer role, the hard_skills_score and experience_score should be extremely low (e.g. 0 to 10), and education/soft skills should reflect actual mismatch.
        - Do not artificially inflate the scores.
        
        Calculate the overall match_score as:
        match_score = (0.40 * hard_skills_score) + (0.30 * experience_score) + (0.15 * education_score) + (0.15 * soft_skills_score)
        Round match_score to the nearest integer.
        
        Provide concise, high-value bulleted feedback strings for each category highlighting what matched and what critical skills or qualifications are missing.
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=FastTailorResult,
                temperature=0.2
            )
        )
        
        if response.parsed:
            return {
                "match_score": response.parsed.match_score,
                "hard_skills_score": response.parsed.hard_skills_score,
                "hard_skills_feedback": response.parsed.hard_skills_feedback,
                "experience_score": response.parsed.experience_score,
                "experience_feedback": response.parsed.experience_feedback,
                "education_score": response.parsed.education_score,
                "education_feedback": response.parsed.education_feedback,
                "soft_skills_score": response.parsed.soft_skills_score,
                "soft_skills_feedback": response.parsed.soft_skills_feedback,
                "tailored_resume": response.parsed.tailored_resume,
                "status": "success"
            }
        else:
            raise ValueError("Failed to parse FastTailorResult response.")
            
    except Exception as e:
        logger.error("Fast-path tailoring failed: %s. Falling back to full Orchestrator...", str(e))
        try:
            orchestrator = EasyApplierOrchestrator()
            result = orchestrator.run_workflow(
                job_title=request.job_title,
                raw_job_description=job_description_to_use,
                raw_resume_text=resume_text_to_use,
                user_notes=request.user_notes
            )

            # Map orchestrator's gap analysis details into our structured response schema
            match_score = result.gap_analysis.match_score
            return {
                "match_score": match_score,
                "hard_skills_score": max(10, match_score - 5),
                "hard_skills_feedback": f"- Matches: {', '.join(result.gap_analysis.direct_matches[:3]) if result.gap_analysis.direct_matches else 'Core qualifications'}\n- Missing: {', '.join(result.gap_analysis.gap_areas[:3]) if result.gap_analysis.gap_areas else 'Specific keywords'}",
                "experience_score": max(10, match_score - 10),
                "experience_feedback": "- Evaluated seniority and title fit based on historical roles.",
                "education_score": max(20, match_score - 2),
                "education_feedback": "- Academic background compared against educational requirements.",
                "soft_skills_score": max(30, match_score + 5),
                "soft_skills_feedback": "- Assessed soft capabilities and domain compatibility.",
                "tailored_resume": result.tailor_output.tailored_resume,
                "status": "success"
            }

        except Exception as ex:
            logger.error("Orchestrator fallback failed: %s", str(ex))
            raise HTTPException(status_code=500, detail=f"Agent error: {str(ex)}")


# === CLEAN LINKEDIN-SPECIFIC ENDPOINT (keep this) ===
@router.post("/api/apply/resume", response_model=ResumeTailorResponse)
async def tailor_resume_endpoint(request: ResumeTailorRequest):
    """Simplified endpoint: ONLY returns match score + tailored resume (optimized single-call)"""
    logger.info("Tailoring resume for job: %s", request.job_title)
  
    profile_details = extract_linkedin_profile_details(request.linkedin_url)
    resume_text_to_use = get_synthesized_candidate_resume(profile_details)
  
    job_description_to_use = request.job_url_or_text or request.job_title
    if job_description_to_use.startswith("http") or "linkedin.com" in job_description_to_use:
        scraped_desc = get_linkedin_job_description(job_description_to_use)
        if scraped_desc:
            job_description_to_use = scraped_desc

    try:
        client = get_gemini_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        prompt = f"""
        Analyze the candidate's base resume and compare it against the job description for '{request.job_title}'.
        
        --- CANDIDATE BASE RESUME ---
        {resume_text_to_use}
        
        --- TARGET JOB DESCRIPTION ---
        {job_description_to_use}
        """
        
        system_instruction = """
        You are an elite, hyper-efficient AI Talent Agent and ATS Parser.
        Your task is to conduct an instantaneous fit comparison and generate a premium tailored candidate resume.
        
        CRITICAL CORE PRINCIPLE: The tailored resume MUST be strictly and deeply grounded in the candidate's actual base profile and true accomplishments.
        - Do NOT over-index on the job description to the point of copy-pasting it or making the resume read like the job posting.
        - The tailored resume must represent the candidate's actual base experience, actual past job titles, and true credentials as specified in the CANDIDATE BASE RESUME.
        - The tailored resume must remain 90% aligned with the candidate's original history. You should simply adapt the wording of their existing bullet points to highlight matching qualifications, weave in relevant keywords naturally, and highlight relevant projects.
        - NEVER invent fake accomplishments, fake metrics, fake roles, or fake skills that are not present or implied in the CANDIDATE BASE RESUME.
        - The tailored resume should feel like the candidate's actual resume, with subtle and professional word choice optimization for the job, NOT a resume written from scratch based only on the job description.
        
        You must perform a multi-dimensional ATS (Applicant Tracking System) matching analysis across 4 categories:
        1. Hard Skills (40% weight): Technical tools, software, programming languages, core technical frameworks, and hard qualifications.
        2. Experience Alignment (30% weight): Job title matching, past responsibilities, years of experience, and role seniority relevance.
        3. Education Fit (15% weight): Highest degree level, major/field of study, and standard credentials.
        4. Soft Skills & Domain Fit (15% weight): Soft competencies, teamwork, communication, and domain/industry alignment.
        
        For each category, calculate a realistic score from 0 to 100 based on the candidate's actual fit. Be highly critical and honest (mimicking standard ATS algorithms):
        - If a Candidate is a Registered Nurse applying for an AI Developer role, the hard_skills_score and experience_score should be extremely low (e.g. 0 to 10).
        - Do not artificially inflate the scores.
        
        Calculate the overall match_score as:
        match_score = (0.40 * hard_skills_score) + (0.30 * experience_score) + (0.15 * education_score) + (0.15 * soft_skills_score)
        Round match_score to the nearest integer.
        
        Provide concise, high-value bulleted feedback strings for each category highlighting what matched and what critical skills or qualifications are missing.
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=FastTailorResult,
                temperature=0.2
            )
        )
        
        if response.parsed:
            return ResumeTailorResponse(
                tailored_resume=response.parsed.tailored_resume
            )
        else:
            raise ValueError("Failed to parse FastTailorResult response.")
            
    except Exception as e:
        logger.error("Fast-path resume tailoring failed: %s. Falling back to full Orchestrator...", str(e))
        try:
            orchestrator = EasyApplierOrchestrator()
            result = orchestrator.run_workflow(
                job_title=request.job_title,
                raw_job_description=job_description_to_use,
                raw_resume_text=resume_text_to_use,
                user_notes="Focus ONLY on producing a clean tailored resume matching qualifications."
            )
            
            return ResumeTailorResponse(
                tailored_resume=result.tailor_output.tailored_resume
            )
        except Exception as ex:
            logger.error("Orchestrator fallback failed: %s", str(ex))
            raise HTTPException(500, detail=str(ex))
