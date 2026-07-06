# 🚀 EasyApplier Demo Startup Guide

**For Hackathon Reviewers, Collaborators & Anyone Who Wants the Full Experience**

The page at https://www.acteustis.com is our project showcase.  
Because EasyApplier is a full-stack AI system (FastAPI backend + Gemini 2.5 Flash + multi-agent fallback), the **best way** to experience the beautiful glassmorphic dashboard, live LinkedIn scraping, dynamic resume synthesis, and 4-dimensional ATS scoring is to run it locally. It takes about 5–10 minutes.

## Prerequisites
- Python 3.10 or higher
- Git
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Modern browser (Chrome, Edge, or Firefox recommended)

**Optional but recommended:** Docker Desktop

---

## Method 1: Run with Python Virtual Environment (Recommended for Most Users)

### Step 1: Clone the Repository
```bash
git clone https://github.com/whatsgooglyKP/working-submission-July-Hackathon1.git
cd working-submission-July-Hackathon1

### Step 2: Set up the Venv

macOS / Linux:

python3 -m venv .venv
source .venv/bin/activate

OR

Windows (PowerShell):

PowerShellpython -m venv .venv
.\.venv\Scripts\Activate.ps1

### Step 3: Install Dependencies

pip install -r requirements.txt

### Step 4: Configure Your Gemini API Key

cp .env.example .env

### Step 5: Start the App 

Option A – Simple (recommended for first run):

python main.py

OR option B – With auto-reload (best during development):

uvicorn main:app --reload --host 0.0.0.0 --port 8000

### Step 6: Open the Demo

Go to http://localhost:8000 in your browser.


--------------ALTERNATIVELY, THERE IS THE DOCKER METHOD---------------------


### Step 1: Build the Image

docker build -t easyapplier .

### Step 2: Run the Container

docker run --rm -p 8080:8080 --env-file .env easyapplier

### Step 3: Open 

open http://localhost:8080 in your browser.


### Docker Notes

The container runs uvicorn directly on port 8080.
--rm automatically cleans up the container when you stop it.
If you want to use a different external port, change it like this: -p 9000:8080




