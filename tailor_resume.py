#!/usr/bin/env python
"""
EasyApplier: CLI tool for generating a tailored resume based on a job posting's
basic/preferred qualifications and the user's LinkedIn URL.
"""
import argparse
import os
import sys
import re
from dotenv import load_dotenv

# Ensure standard streams use UTF-8 encoding on Windows to prevent charmap/emoji print crashes
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure correct python path so local packages can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import EasyApplierOrchestrator
from api.routes import extract_linkedin_profile_details, get_default_candidate_resume
from job_scraper import get_linkedin_job_description

# Load local environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Tailor a resume based on LinkedIn job qualifications and a user's LinkedIn profile URL."
    )
    parser.add_argument(
        "--job", "-j",
        required=True,
        help="LinkedIn job posting URL or raw job description text"
    )
    parser.add_argument(
        "--linkedin", "-l",
        required=True,
        help="User's LinkedIn profile URL"
    )
    parser.add_argument(
        "--title", "-t",
        default="Target Position",
        help="Job title (optional, defaults to 'Target Position' or scraped title)"
    )
    parser.add_argument(
        "--output", "-o",
        help="File path to save the tailored resume (optional)"
    )

    args = parser.parse_args()

    # Validate GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] GEMINI_API_KEY is not set in your environment or .env file.", file=sys.stderr)
        sys.exit(1)

    # 1. Resolve Job Description (Scrape if URL)
    job_desc = args.job.strip()
    job_title = args.title.strip()
    
    link_match = re.search(r'https?://[^\s]+', job_desc)
    if link_match:
        print(f"[INFO] Scraping LinkedIn job description from URL: {link_match.group(0)}...", file=sys.stderr)
        try:
            scraped = get_linkedin_job_description(link_match.group(0))
            if scraped:
                job_desc = scraped
                print("[INFO] Successfully scraped job description.", file=sys.stderr)
            else:
                print("[WARNING] Could not scrape job description from URL. Using raw URL text.", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Scraper error: {e}. Using raw URL text.", file=sys.stderr)

    # 2. Synthesize Candidate Profile from LinkedIn URL
    print(f"[INFO] Parsing candidate profile from LinkedIn URL: {args.linkedin}...", file=sys.stderr)
    try:
        profile_details = extract_linkedin_profile_details(args.linkedin)
        default_resume = get_default_candidate_resume()
        
        resume_text = f"""
=====================================================
EXTRACTED CANDIDATE PROFILE (LINKEDIN URL)
=====================================================
Full Name: {profile_details['name']}
Professional Headline: {profile_details['headline']}
Target Location: {profile_details['location']}
Inferred Skills & Focus: {", ".join(profile_details['skills'])}

=====================================================
CANDIDATE BASE RESUME (FALLBACK & EXPERIENCE SOURCE)
=====================================================
{default_resume}

CRITICAL PARSING GUIDELINES:
- The candidate's name MUST be parsed as "{profile_details['name']}".
- The candidate's summary and location MUST align with "{profile_details['location']}" and headline "{profile_details['headline']}".
- Merge the inferred skills ({", ".join(profile_details['skills'])}) into the resume.
- Ensure all tailored outputs use "{profile_details['name']}" as the candidate's name.
"""
    except Exception as e:
        print(f"[ERROR] Failed to extract LinkedIn profile details: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Run Multi-Agent Orchestrator
    print("[INFO] Running parallel multi-agent tailoring workflow...", file=sys.stderr)
    try:
        orchestrator = EasyApplierOrchestrator()
        result = orchestrator.run_workflow(
            job_title=job_title,
            raw_job_description=job_desc,
            raw_resume_text=resume_text,
            user_notes="Focus strictly on basic and preferred qualifications to align the resume."
        )
        
        tailored_resume = result.tailor_output.tailored_resume
        
        # Print ONLY the tailored resume to stdout
        print("\n" + "="*80)
        print("                        TAILORED RESUME (MARKDOWN)                      ")
        print("="*80 + "\n")
        print(tailored_resume)
        print("\n" + "="*80 + "\n")
        
        # If output file is requested, save it
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(tailored_resume)
            print(f"[INFO] Tailored resume saved successfully to: {args.output}", file=sys.stderr)
            
    except Exception as e:
        print(f"[ERROR] Multi-agent execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
