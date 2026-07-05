import urllib.request
import json
import sys

def test_apply_endpoint():
    url = "http://127.0.0.1:8000/api/apply"
    
    # 1. Test Highly Matching Candidate (Kevin Scott Pinard as AI Developer)
    print("\n--- TEST 1: High Match Candidate (Kevin Scott Pinard -> AI Developer) ---")
    payload = {
        "job_title": "AI Developer at Aligned Labs",
        "job_description": "We are seeking an AI Developer proficient in Python, SQL, Gemini LLMs, FastAPI, and agentic workflows to build multi-agent orchestrations.",
        "resume_text": "https://www.linkedin.com/in/pinardkevin",
        "user_notes": None
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            print("Status Code: 200 OK")
            print(f"Match Score: {response_data.get('match_score')}%")
            print("Tailored Resume Snippet (First 150 chars):")
            print(response_data.get('tailored_resume', '')[:150] + "...")
            if response_data.get('match_score', 0) >= 65:
                print("[SUCCESS] Match score is >= 65% as expected!")
            else:
                print("[FAIL] Match score was less than 65% unexpectedly.")
    except Exception as e:
        print(f"[ERROR] Test 1 failed: {e}")

    # 2. Test Low Matching Candidate (Registered Nurse -> AI Developer)
    print("\n--- TEST 2: Low Match Candidate (Registered Nurse -> AI Developer) ---")
    payload_low = {
        "job_title": "AI Developer at Aligned Labs",
        "job_description": "We are seeking an AI Developer proficient in Python, SQL, Gemini LLMs, FastAPI, and agentic workflows to build multi-agent orchestrations.",
        "resume_text": "https://www.linkedin.com/in/jane-doe-nurse",
        "user_notes": None
    }
    
    req_low = urllib.request.Request(
        url,
        data=json.dumps(payload_low).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req_low, timeout=30) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            print("Status Code: 200 OK (Unexpected!)")
            print(f"Match Score: {response_data.get('match_score')}%")
            print("[FAIL] Mismatching candidate profile should have been rejected under 65%!")
    except urllib.error.HTTPError as e:
        print(f"Status Code: {e.code}")
        try:
            err_detail = json.loads(e.read().decode('utf-8'))
            print(f"Error Detail: {err_detail.get('detail')}")
            if err_detail.get('detail') == "change your linkedin profile to get about 65% score match":
                print("[SUCCESS] Error message is exactly what is required!")
            else:
                print(f"[FAIL] Error message did not match. Got: {err_detail.get('detail')}")
        except Exception as parse_err:
            print(f"Could not parse error response: {parse_err}")
    except Exception as e:
        print(f"[ERROR] Test 2 failed: {e}")

if __name__ == "__main__":
    test_apply_endpoint()
