import sys
import io
import os

# Failsafe: Ensure standard streams use UTF-8 encoding on Windows without stream replacement
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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
from api.routes import router

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="EasyApplier AI Multi-Agent System",
    description="Production-grade FastAPI backend for the EasyApplier Job Customization Suite, powered by Gemini 2.5",
    version="2.0.0"
)

# Configure CORS for public accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the modular routing endpoints
app.include_router(router)

# Serve the static visual and UI components
@app.get("/", response_class=HTMLResponse)
async def root():
    """Renders the dashboard UI from index.html."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return HTMLResponse(content=f"<h3>Error loading index.html: {str(e)}</h3>", status_code=500)

@app.get("/aligned_labs_logo.jpg")
async def get_logo():
    """Serves the generated Aligned Labs logo image."""
    logo_path = "aligned_labs_logo.jpg"
    if not os.path.exists(logo_path):
        logo_path = "C:/Users/pinar/.gemini/antigravity-cli/brain/5ab6de28-73cb-4611-8a6d-8d4c0c72d395/aligned_labs_logo_1781851225345.jpg"
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")

if __name__ == "__main__":
    import uvicorn
    # Read port from environment (Cloud Run injects PORT environment variable)
    port = int(os.getenv("PORT", 8000))
    print(f"[SYSTEM] Launching EasyApplier Multi-Agent API on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
