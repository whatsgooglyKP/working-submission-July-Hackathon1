---
name: streamlit-frontend
description: Expert guidelines and design patterns for building and maintaining the EasyApplier Streamlit web dashboard.
---

# Streamlit Frontend Development Skill

Use this skill when developing, refactoring, or extending the Streamlit-based web dashboard interface for EasyApplier located in `app.py`.

## Core Guidelines & Principles

1. **Elegant Aesthetics & Themes**:
   - Maintain support for both **Light Theme** (default) and **Dark Theme** utilizing `st.session_state.theme`.
   - Ensure the color tokens strictly follow the design system values (for borders, backgrounds, text colors, and highlights).
   - Inject the core styles dynamically into markdown using `st.markdown("<style>...</style>", unsafe_allow_html=True)`.

2. **Clean Streamlit App Defaults Override**:
   - Hide the default Streamlit headers, menu buttons, footers, status widgets, and deployment buttons to achieve a native app appearance.
   - Use the custom CSS class `.block-container` to restrict padding and set the maximum app width to `1360px` for optimal grid alignment on wide screens.

3. **Visual Components Implementation**:
   - **Metric Cards**: Use custom HTML inside a styled `div` instead of Streamlit's default `st.metric` for premium aesthetics:
     ```html
     <div class="metric-card">
         <div class="metric-label">{label}</div>
         <div class="metric-value">{value}</div>
     </div>
     ```
   - **Badges**: Use tailored badges for statuses (e.g., `.badge-green`, `.badge-amber`, `.badge-red`, `.badge-blue`) to represent metrics or dates nicely.
   - **Buttons**: Style all buttons to utilize Google/Aligned Labs brand colors. Provide smooth transitions on hover.
   - **Pill-Style Tabs**: Override Streamlit's tab borders with clean custom pills.

4. **File Upload & Parsing Patterns**:
   - Safely process and extract text from uploaded candidate profile/resume files (`.docx` and `.pdf` formats) using `python-docx` and `pypdf`.
   - Utilize a helper function like `extract_text_from_file(uploaded_file)` that safely reads binary file content and handles exceptions.

5. **Layout & Grid Structure**:
   - Organize the layout using standard columns. The main job search and application suite uses a split of `[4, 3, 5]` for:
     - `col_list`: Displaying active LinkedIn job listings as a interactive radio list card.
     - `col_profile`: Candidate profile details, focus notes, and action button to generate tailored materials.
     - `col_tailor`: Output of the AI Application Strategy containing match score, resume, cover letter, and interview prep in standard expanding lists (`st.expander`).

---

## Code Patterns

### Theme CSS Variables Setup
```python
if "theme" not in st.session_state:
    st.session_state.theme = "light"

IS_DARK = st.session_state.theme == "dark"

if IS_DARK:
    bg_color = "#09090b"
    bg_subtle = "#0c0c0f"
    card_color = "#0c0c0f"
    border_color = "#1e1e24"
    text_color = "#fafafa"
    text_muted = "#71717a"
    accent_color = "#6366f1"
else:
    bg_color = "#ffffff"
    bg_subtle = "#f6f8fa"
    card_color = "#ffffff"
    border_color = "#d0d7de"
    text_color = "#000000"
    text_muted = "#4c4c4c"
    accent_color = "#4285F4"
```

### Dynamic CSS Styling Block
```python
st.markdown(f"""
<style>
    :root {{
        --bg: {bg_color};
        --bg-subtle: {bg_subtle};
        --card: {card_color};
        --border: {border_color};
        --text: {text_color};
        --accent: {accent_color};
        --radius: 10px;
    }}
    /* Hide default header/footer */
    header[data-testid="stHeader"], #MainMenu, footer {{
        display: none !important;
    }}
</style>
""", unsafe_allow_html=True)
```

### Resume Document Parsing (PDF / DOCX)
```python
import docx
import pypdf
from io import BytesIO

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
    except Exception as e:
        return f"Error parsing file: {e}"
```

### Plotly Custom Styling Object
To align Plotly with the overall theme without breaking UI elements:
```python
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#000000" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=40, r=20, t=20, b=40),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
    ),
)
```
