import os
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from google.genai.errors import APIError
from job_scraper import search_linkedin_jobs
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import docx
import pypdf
from io import BytesIO

# Load local .env
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EasyApplier ◆ AI Agent Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme selection (default to light for cornsilk theme)
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# CSS variables depending on theme
if IS_DARK:
    bg_color = "#09090b"
    bg_subtle = "#0c0c0f"
    card_color = "#0c0c0f"
    card_hover = "#131316"
    border_color = "#1e1e24"
    border_subtle = "#16161a"
    text_color = "#fafafa"
    text_muted = "#71717a"
    text_dim = "#52525b"
    shadow = "none"
    accent_color = "#6366f1"
    accent_hover = "#4f46e5"
else:
    bg_color = "#ffffff" # Pure White background
    bg_subtle = "#f6f8fa" # Very light grey sidebar/subtle background
    card_color = "#ffffff" 
    card_hover = "#f6f8fa" 
    border_color = "#d0d7de" # Soft grey borders
    border_subtle = "#ebf0f4"
    text_color = "#000000" # Pure Black text
    text_muted = "#4c4c4c"
    text_dim = "#6c6c6c"
    shadow = "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.05)"
    accent_color = "#4285F4" # Google Logo Blue
    accent_hover = "#357ae8" # Darker Google Blue

# Inject custom CSS matching shared design patterns
st.markdown(f"""
<style>
    :root {{
        --bg: {bg_color};
        --bg-subtle: {bg_subtle};
        --card: {card_color};
        --card-hover: {card_hover};
        --border: {border_color};
        --border-subtle: {border_subtle};
        --text: {text_color};
        --text-muted: {text_muted};
        --text-dim: {text_dim};
        --accent: {accent_color};
        --accent-hover: {accent_hover};
        --green: #10b981;
        --green-muted: rgba(16, 185, 129, 0.1);
        --red: #ef4444;
        --red-muted: rgba(239, 68, 68, 0.1);
        --amber: #f59e0b;
        --amber-muted: rgba(245, 158, 11, 0.1);
        --shadow: {shadow};
        --radius: 10px;
    }}

    /* Hide default elements */
    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {{
        display: none !important;
    }}

    /* Global styling overrides */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"], section[data-testid="stSidebar"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-subtle) !important;
        border-right: 1px solid var(--border) !important;
    }}
    
    /* Fix text visibility inside Streamlit widgets (Radio, Selectbox, Labels) for dark mode */
    .stMarkdown p, 
    div[data-testid="stRadio"] label, 
    div[data-testid="stRadio"] p, 
    div[data-testid="stRadio"] span, 
    label[data-baseweb="radio"] div, 
    div[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] p,
    div[data-baseweb="select"] div,
    span[data-baseweb="select"] {{
        color: var(--text) !important;
    }}

    .block-container {{
        padding: 2rem 2.5rem 3rem !important;
        max-width: 1360px !important;
    }}

    /* Custom Metric Cards */
    .metric-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        box-shadow: var(--shadow);
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: var(--text-muted);
        font-weight: 500;
        margin-bottom: 0.2rem;
    }}
    .metric-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.02em;
    }}

    /* Custom Chart wrap */
    .chart-wrap {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
    }}
    .chart-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text);
    }}
    .chart-subtitle {{
        font-size: 0.75rem;
        color: var(--text-dim);
        margin-bottom: 1rem;
    }}

    /* Horizontal list gap */
    [data-testid="stHorizontalBlock"] {{
        gap: 1.25rem !important;
    }}

    /* Custom pill-style tabs */
    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-muted) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.2rem !important;
        border: 1px solid transparent !important;
        border-radius: 7px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--text) !important;
        background: var(--card) !important;
        border-color: var(--border) !important;
    }}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    [data-baseweb="tab-list"] {{
        gap: 6px !important;
        background: var(--bg-subtle) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 4px;
        margin-bottom: 20px;
    }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
    }}
    .badge-green {{ color: var(--green); background: var(--green-muted); border: 1px solid rgba(16, 185, 129, 0.2); }}
    .badge-red {{ color: var(--red); background: var(--red-muted); border: 1px solid rgba(239, 68, 68, 0.2); }}
    .badge-amber {{ color: var(--amber); background: var(--amber-muted); border: 1px solid rgba(245, 158, 11, 0.2); }}
    .badge-blue {{ color: var(--accent); background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); }}

    /* Style all buttons on the page to use brand red */
    div[data-testid="stButton"] button, .stButton button {{
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border: 1px solid var(--accent) !important;
        transition: background-color 0.2s, border-color 0.2s !important;
    }}
    div[data-testid="stButton"] button:hover, .stButton button:hover {{
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
        color: #ffffff !important;
    }}
</style>
""", unsafe_allow_html=True)

# Custom helpers
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name.lower()
        if filename.endswith(".docx"):
            doc = docx.Document(BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        elif filename.endswith(".pdf"):
            reader = pypdf.PdfReader(BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            return text
        elif filename.endswith(".doc"):
            # Basic fallback for legacy doc files
            decoded = file_bytes.decode('utf-8', errors='ignore')
            lines = [line.strip() for line in decoded.split('\n') if len(line.strip()) > 3]
            return "\n".join(lines)
    except Exception as e:
        return f"Error parsing file: {e}"
    return ""

def render_metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# Plotly theme configuration
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#000000" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=40, r=20, t=20, b=40),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#000000" if not IS_DARK else "#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#000000" if not IS_DARK else "#71717a"),
    ),
)

# Header Section
logo_path = "aligned_labs_logo.jpg"
if not os.path.exists(logo_path):
    logo_path = "C:/Users/pinar/.gemini/antigravity-cli/brain/5ab6de28-73cb-4611-8a6d-8d4c0c72d395/aligned_labs_logo_1781851225345.jpg"

if os.path.exists(logo_path):
    st.image(logo_path, width=150)

st.markdown("""
<div style="display:flex; align-items:center; gap:12px;">
    <span style="font-family:'Outfit', sans-serif; font-size:28px; font-weight:700; color:var(--accent);">EasyApplier</span>
    <span class="badge badge-green" style="font-size:12px; font-weight:600; border-radius:20px;">AI Dashboard</span>
</div>
""", unsafe_allow_html=True)
if "searched_title" in st.session_state and st.session_state.job_listings:
    st.markdown(f"<div style='font-size:14px; color:var(--text-muted); margin-top:4px;'>Most Recent {st.session_state.searched_title} 35 Job Postings on LinkedIn</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin:1.2rem 0; border:0; border-top:1px solid var(--border);'>", unsafe_allow_html=True)

# Sidebar Configuration / Credentials
with st.sidebar:
    st.markdown("### ⚙️ Agent Settings")
    
    # Preloaded key defaults
    default_key = os.getenv("GEMINI_API_KEY", "")
    # If the user input is present in session state, override
    if "api_key" not in st.session_state:
        st.session_state.api_key = default_key if default_key else "AQ.Ab8RN6KUiT8oh9KCbfdN25iizco0cZkWN49mjwwetIaR4yRDiA"
        
    api_key_input = st.text_input(
        "Gemini API Key / Project Token",
        value=st.session_state.api_key,
        type="password",
        help="Paste your Google AI Studio API Key or course token starting with AIzaSy... or AQ.Ab..."
    )
    st.session_state.api_key = api_key_input

    model_input = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp"],
        index=0
    )

# Load resume dynamically from local file to prevent manual upload/exposure of PII data
default_resume = "Kevin Pinard - MS in AI Student. Proficient in Python. Set up Google Antigravity IDE and developed local test scripts. Experience with Gemini API."
resume_input = default_resume
try:
    doc_path = "C:/Users/pinar/Google Kaggle 5DAYAI Vibe Coding Project/RESUME.Google.Day3.docx"
    if os.path.exists(doc_path):
        doc = docx.Document(doc_path)
        resume_input = "\n".join([p.text for p in doc.paragraphs])
except Exception:
    pass

# Pydantic schema for structured output
class ApplicationStrategy(BaseModel):
    match_score: int = Field(..., description="Overall fit score from 1 to 100")
    fit_summary: str = Field(..., description="A 3-4 sentence summary of why the candidate fits this role")
    cover_letter: str = Field(..., description="A professional, tailored cover letter based on the job and resume")
    tailored_resume: str = Field(..., description="A rewritten version of the candidate resume, fully optimized to align with the job description keywords")
    resume_suggestions: list[str] = Field(..., description="Bullet points suggesting specific updates to the resume to align with keywords")
    interview_prep: list[str] = Field(..., description="Top 3 likely interview questions with suggested talking points")

# Initialize strategy cache in session state
if "cached_strategies" not in st.session_state:
    st.session_state.cached_strategies = {}

# Main Content Layout
search_col1, search_col2 = st.columns([6, 2])
with search_col1:
    job_title = st.text_input("Search Job Title", placeholder="e.g. Python Developer, Machine Learning Engineer...", label_visibility="collapsed")
with search_col2:
    search_clicked = st.button("Search LinkedIn Jobs", width="stretch", type="primary")

# Retrieve job listings or use session state
if "job_listings" not in st.session_state:
    st.session_state.job_listings = []

if search_clicked and job_title:
    with st.spinner("Scraping 35 most recent job listings from LinkedIn guest search..."):
        try:
            st.session_state.job_listings = search_linkedin_jobs(job_title, limit=35)
            st.session_state.searched_title = job_title.title()
            st.toast(f"Successfully loaded {len(st.session_state.job_listings)} jobs!", icon="✅")
        except Exception as e:
            st.error(f"Error scraping LinkedIn: {e}")

# If we have listings, render dashboard
if st.session_state.job_listings:
    df = pd.DataFrame(st.session_state.job_listings)
    
    # Calculate some helper metrics
    total_jobs = len(df)
    unique_companies = df['company'].nunique()
    top_location = df['location'].value_counts().index[0] if not df.empty else "N/A"
    
    # Metric KPI Row
    m1, m2, m3 = st.columns(3)
    with m1:
        render_metric_card("Total Jobs Loaded", f"{total_jobs} Postings")
    with m2:
        render_metric_card("Unique Companies Hiring", f"{unique_companies} Companies")
    with m3:
        render_metric_card("Primary Hiring Location", top_location)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Split main layout into 3 columns: Listings & Selection, Candidate Profile & Actions, AI Application Strategy
    col_list, col_profile, col_tailor = st.columns([4, 3, 5])
    
    with col_list:
        st.markdown("### 💼 Job Listings")
        
        # Create a clickable list of cards in Streamlit using radio buttons
        job_options = [f"{idx+1}. {row['title']} @ {row['company']} ({row['location']})" for idx, row in df.iterrows()]
        selected_option = st.radio("Select job posting to optimize:", options=job_options, label_visibility="collapsed")
        
        selected_idx = int(selected_option.split(".")[0]) - 1
        
        # State-change detection: Clear stale results if the user selects a new job listing
        if "previous_selected_idx" not in st.session_state:
            st.session_state.previous_selected_idx = selected_idx
        elif st.session_state.previous_selected_idx != selected_idx:
            st.session_state.previous_selected_idx = selected_idx
            if "tailor_result" in st.session_state:
                del st.session_state.tailor_result
                
        selected_job = st.session_state.job_listings[selected_idx]
        st.session_state.selected_job = selected_job
        
        # Display detailed card
        st.markdown(f"""
        <div style="background:var(--card-hover); border:1px solid var(--border); border-radius:var(--radius); padding:1rem; margin-top:1rem;">
            <h4 style="margin:0 0 4px 0;">{selected_job['title']}</h4>
            <div style="color:var(--text-muted); font-size:13px; margin-bottom:8px;">{selected_job['company']} — {selected_job['location']}</div>
            <div class="badge badge-blue">{selected_job['posted_date']}</div>
            <p style="margin-top:10px;"><a href="{selected_job['link']}" target="_blank" style="color:var(--accent); text-decoration:none; font-weight:600;">View original post on LinkedIn ↗</a></p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_profile:
        st.markdown("### 👤 Candidate Details")
        
        linkedin_url = st.text_input("1. Enter LinkedIn Profile URL", value="https://www.linkedin.com/in/pinardkevin", placeholder="https://www.linkedin.com/in/username")
        
        default_notes = "Highlight my familiarity with Google's Antigravity CLI and App Hub."
        notes_input = st.text_input("2. Focus Notes / User Instructions", value=default_notes)
        
        # Parse resume text dynamically from local file
        resume_text_doc = ""
        if linkedin_url:
            try:
                doc_path = "C:/Users/pinar/Google Kaggle 5DAYAI Vibe Coding Project/RESUME.Google.Day3.docx"
                if os.path.exists(doc_path):
                    doc = docx.Document(doc_path)
                    resume_text_doc = "\n".join([p.text for p in doc.paragraphs])
                else:
                    resume_text_doc = default_resume
            except Exception:
                resume_text_doc = default_resume
                
        # Validate LinkedIn URL
        is_valid_linkedin = False
        if linkedin_url:
            cleaned_url = linkedin_url.strip().lower()
            if (cleaned_url.startswith("http://") or cleaned_url.startswith("https://")) and "linkedin.com" in cleaned_url:
                is_valid_linkedin = True
                
        # Setup caching key
        cache_key = (
            selected_job['link'] if selected_job else "",
            linkedin_url,
            notes_input,
            st.session_state.api_key
        )
        
        # Load from cache if available
        if cache_key in st.session_state.cached_strategies:
            st.session_state.tailor_result = st.session_state.cached_strategies[cache_key]
        else:
            if "tailor_result" in st.session_state:
                del st.session_state.tailor_result
                
        is_generated = cache_key in st.session_state.cached_strategies
        
        # Action button
        st.markdown("<br>", unsafe_allow_html=True)
        optimize_btn = st.button(
            "Generate Tailored Career Path",
            width="stretch",
            type="primary",
            disabled=is_generated or not (is_valid_linkedin and selected_job)
        )
        
        if not selected_job:
            st.caption("⚠️ Please select a Job Listing.")
        elif not linkedin_url:
            st.caption("⚠️ Please enter your LinkedIn Profile URL.")
        elif not is_valid_linkedin:
            st.caption("⚠️ Please enter a valid LinkedIn Profile URL (must start with http/https and contain 'linkedin.com').")
            
        if optimize_btn:
            if not st.session_state.api_key:
                st.warning("Please configure your Gemini API key in the sidebar.")
            else:
                with st.spinner("Analyzing requirements and customizing resume with Gemini..."):
                    prompt = f"""
                    You are an expert career advisor and job application optimization agent. 
                    Analyze the job details and candidate resume below, then return a structured ApplicationStrategy.
                    Specifically, rewrite the candidate's resume/profile to create a tailored, optimized resume that aligns with the job keywords, and place it in the `tailored_resume` field.

                    Job Title: {selected_job['title']}
                    Company: {selected_job['company']}
                    Location: {selected_job['location']}
                    Job Link: {selected_job['link']}
                    
                    Candidate Resume:
                    {resume_text_doc}
                    """
                    if notes_input:
                        prompt += f"\nAdditional User Instructions/Focus Areas:\n{notes_input}"
                        
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        response = client.models.generate_content(
                            model=model_input,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ApplicationStrategy,
                                temperature=0.35,
                            ),
                        )
                        if response.parsed:
                            st.session_state.cached_strategies[cache_key] = response.parsed
                            st.session_state.tailor_result = response.parsed
                            st.toast("Strategy generated successfully!", icon="✨")
                            st.rerun()
                        else:
                            st.error("Response could not be parsed into the required schema.")
                    except APIError as ae:
                        st.error(f"Gemini API Connection failed: {ae}")
                    except Exception as e:
                        st.error(f"Failed to generate strategy: {e}")
                        
    with col_tailor:
        st.markdown("### 🏆 AI Application Strategy")
        
        # Render results if generated
        if "tailor_result" in st.session_state:
            res = st.session_state.tailor_result
            score = res.match_score
            badge_class = "badge-green" if score >= 80 else ("badge-amber" if score >= 60 else "badge-red")
            
            st.markdown(f"""
            <div style="background:rgba(99, 102, 241, 0.05); border:1px solid rgba(99, 102, 241, 0.2); border-radius:var(--radius); padding:1rem; margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h4 style="margin:0 0 2px 0;">Resume Match Score</h4>
                    <div style="color:var(--text-muted); font-size:12px;">Based on keywords, skills, and experience alignment</div>
                </div>
                <div class="badge {badge_class}" style="font-size:1.6rem; font-weight:800; padding:8px 16px;">{score}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📝 Tailored Executive Recommendation", expanded=True):
                st.write(res.fit_summary)
                
            with st.expander("📄 Tailored Optimized Resume", expanded=False):
                st.code(res.tailored_resume, language="text")
                st.caption("Copy the text block above to use in your application.")
                
            with st.expander("✉️ Cover Letter Draft", expanded=False):
                st.code(res.cover_letter, language="text")
                st.caption("Copy the text block above to use in your application.")
                
            with st.expander("🔧 Resume Update Suggestions", expanded=False):
                for sug in res.resume_suggestions:
                    st.markdown(f"- {sug}")
                    
            with st.expander("💬 Interview Prep Q&A", expanded=False):
                for prep in res.interview_prep:
                    st.markdown(prep)
        else:
            st.info("Select a job listing on the left, verify your profile details, and click 'Generate Tailored Career Path' to view the optimized strategy.")

    # Raw scraped data view in collapsible bottom expander
    st.markdown("<br><hr style='margin:1.5rem 0; border:0; border-top:1px solid var(--border);'>", unsafe_allow_html=True)
    with st.expander("🔍 Raw Scraped Job Data View", expanded=False):
        st.dataframe(df, width="stretch")
        
else:
    st.markdown("""
    <div style="text-align:center; padding:80px 40px; border:1px dashed var(--border); border-radius:var(--radius); color:var(--text-muted);">
        <svg width="64" height="64" fill="none" stroke="currentColor" stroke-width="1.2" viewBox="0 0 24 24" style="margin-bottom:15px; color:var(--text-dim);">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 14.15v4.25c0 .621-.504 1.125-1.125 1.125H4.875c-.621 0-1.125-.504-1.125-1.125v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.45.258-.717.258H3.75c-.266 0-.523-.093-.717-.258m16.5 0a2.18 2.18 0 01.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m0 0V6.25c0-1.098-.826-1.97-1.922-2.025a47.95 47.95 0 00-6.071 0C5.122 4.28 4.3 5.152 4.3 6.25v.806m9.75 0a48.693 48.693 0 01-6.071 0"></path>
        </svg>
        <h3>No Job Listings Loaded</h3>
        <p style="font-size:14px; margin-top:5px;">Enter a job title in the search box above to retrieve live postings from LinkedIn guest search.</p>
    </div>
    """, unsafe_allow_html=True)


