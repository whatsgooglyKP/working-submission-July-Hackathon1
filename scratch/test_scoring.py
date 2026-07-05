import requests
import json

def test_apply_endpoint(linkedin_url, job_title, job_description):
    url = "http://127.0.0.1:8000/api/apply"
    payload = {
        "job_title": job_title,
        "job_description": job_description,
        "resume_text": linkedin_url
    }
    
    print(f"\n--- Testing Endpoint with: {linkedin_url} for job: '{job_title}' ---")
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Overall Match Score: {data.get('match_score')}%")
            print(f"Hard Skills Score: {data.get('hard_skills_score')}%")
            print(f"Hard Skills Feedback: {data.get('hard_skills_feedback')}")
            print(f"Experience Score: {data.get('experience_score')}%")
            print(f"Experience Feedback: {data.get('experience_feedback')}")
            print(f"Education Score: {data.get('education_score')}%")
            print(f"Education Feedback: {data.get('education_feedback')}")
            print(f"Soft Skills Score: {data.get('soft_skills_score')}%")
            print(f"Soft Skills Feedback: {data.get('soft_skills_feedback')}")
            print("-" * 50)
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test case 1: High match (Kevin Scott Pinard applying for AI Developer)
    test_apply_endpoint(
        linkedin_url="https://www.linkedin.com/in/pinardkevin",
        job_title="AI Developer",
        job_description="We are looking for a Senior AI Developer expert in Python, SQL, Google GenAI SDK (Gemini), agentic workflows, and deploying dockerized services to Google Cloud Run."
    )
    
    # Test case 2: Low match (Nurse applying for AI Developer - previously failed with 400, now should succeed with low score!)
    test_apply_endpoint(
        linkedin_url="https://www.linkedin.com/in/sarah-nurse-clinical",
        job_title="AI Developer",
        job_description="We are looking for a Senior AI Developer expert in Python, SQL, Google GenAI SDK (Gemini), agentic workflows, and deploying dockerized services to Google Cloud Run."
    )
