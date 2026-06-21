# EasyApplier UI and Layout Design Rules

Always adhere to the following rules when developing or modifying the EasyApplier dashboard interface:

1. **Prefer Accordion/Expanders Over Tabs**:
   - Avoid using tabbed containers (such as Streamlit `st.tabs` or HTML custom tabs).
   - Display dashboard sections in a clean, multi-column dashboard layout. For dense output content (e.g. Fit Summary, Cover Letter, suggestions), use collapsible accordion/expander widgets (`st.expander` in Streamlit or `<details>`/`<summary>` in HTML).

2. **Aesthetics & Branding Control**:
   - Maintain the standard Google Blue branding theme with modern sans-serif typography (`Outfit` or `Plus Jakarta Sans`).
   - Do not force rigid custom color schemes (like black-and-white print styles) or monospaced Courier fonts unless explicitly requested. Avoid hardcoding global background overrides that override system dark/light modes.

3. **No File Upload Boxes for Profiles**:
   - Do not include manual resume/document upload components on the user interface.
   - Resolve and parse the candidate's profile strictly through the LinkedIn URL input pointing to local document copies on disk (e.g., `C:/Users/pinar/Google Kaggle 5DAYAI Vibe Coding Project/RESUME.Google.Day3.docx`) to prevent unnecessary exposure.
