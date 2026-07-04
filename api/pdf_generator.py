import os
from datetime import datetime
from fpdf import FPDF

def clean_for_pdf(text: str) -> str:
    if not text:
        return ""
    # Map common non-latin-1/fancy unicode characters to safe equivalents
    replacements = {
        '\u2018': "'", '\u2019': "'",  # Smart single quotes
        '\u201c': '"', '\u201d': '"',  # Smart double quotes
        '\u2013': '-', '\u2014': '-',  # En/em dashes
        '\u2022': '-', '\u25c6': '-',  # Bullets
        '\u200b': '',                  # Zero-width space
        '\u2112': 'L', '\u2115': 'N',
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    
    # Encode to latin-1 and ignore anything that can't be encoded
    try:
        return text.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return text.encode('ascii', 'ignore').decode('ascii')

class CareerPathPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(26, 86, 219) # Accent Blue
            self.cell(0, 5, 'EASYAPPLIER CAREER DOSSIER', border=0, ln=0, align='L')
            
            self.set_font('Helvetica', '', 8)
            self.set_text_color(107, 114, 128) # Slate grey
            self.cell(0, 5, 'Tailored Application Strategy', border=0, ln=1, align='R')
            
            # Subtle header line
            self.set_draw_color(229, 231, 235)
            self.set_linewidth(0.4)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(156, 163, 175)
            self.set_draw_color(229, 231, 235)
            self.line(20, self.get_y() - 2, 190, self.get_y() - 2)
            
            self.cell(0, 10, 'CONFIDENTIAL ◆ AI-OPTIMIZED ATS COMPLIANT DOSSIER', border=0, ln=0, align='L')
            self.cell(0, 10, f'Page {self.page_no()}', border=0, ln=1, align='R')

def extract_candidate_name(resume_text: str) -> str:
    if not resume_text:
        return "Kevin Scott Pinard"
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    if lines:
        for line in lines:
            line_clean = line.replace("#", "").replace("*", "").strip()
            # Find first line that looks like a name (usually less than 40 chars and doesn't start with a section heading)
            if len(line_clean) < 40 and not any(h in line_clean.lower() for h in ["summary", "skills", "experience", "education", "profile", "focus"]):
                return line_clean
    return "Kevin Scott Pinard"

def check_page_break(pdf, space_needed: float = 20):
    if pdf.get_y() + space_needed > pdf.h - pdf.b_margin:
        pdf.add_page()

def write_rich_text(pdf, text: str, default_font="Helvetica", default_size=9.5, default_style="", default_color=(31, 41, 55), line_height=5.5):
    pdf.set_font(default_font, default_style, default_size)
    pdf.set_text_color(*default_color)
    
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 1:
            pdf.set_font(default_font, default_style + "B" if "B" not in default_style else default_style, default_size)
        else:
            pdf.set_font(default_font, default_style.replace("B", ""), default_size)
        pdf.write(line_height, clean_for_pdf(part))

def write_markdown_line_by_line(pdf, text: str):
    if not text:
        return
    
    lines = text.split("\n")
    for line in lines:
        line_stripped = line.strip()
        
        # Horizontal rule
        if line_stripped in ("---", "***", "___"):
            pdf.ln(3)
            pdf.set_draw_color(209, 213, 219)
            pdf.set_linewidth(0.4)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            continue
            
        # Heading 1: `# Text`
        if line_stripped.startswith("# "):
            check_page_break(pdf, 25)
            pdf.ln(5)
            cleaned_line = line_stripped[2:].strip()
            write_rich_text(pdf, cleaned_line, default_font="Helvetica", default_size=15, default_style="B", default_color=(26, 86, 219), line_height=7)
            pdf.ln(8)
            continue
            
        # Heading 2: `## Text`
        elif line_stripped.startswith("## "):
            check_page_break(pdf, 20)
            pdf.ln(4)
            cleaned_line = line_stripped[3:].strip()
            write_rich_text(pdf, cleaned_line, default_font="Helvetica", default_size=12, default_style="B", default_color=(17, 24, 39), line_height=6)
            pdf.ln(6)
            
            # Section underline
            pdf.set_draw_color(229, 231, 235)
            pdf.set_linewidth(0.4)
            pdf.line(pdf.l_margin, pdf.get_y() - 1, pdf.w - pdf.r_margin, pdf.get_y() - 1)
            pdf.ln(2.5)
            continue
            
        # Heading 3: `### Text`
        elif line_stripped.startswith("### "):
            check_page_break(pdf, 15)
            pdf.ln(3)
            cleaned_line = line_stripped[4:].strip()
            write_rich_text(pdf, cleaned_line, default_font="Helvetica", default_size=10, default_style="B", default_color=(55, 65, 81), line_height=5.5)
            pdf.ln(5.5)
            continue
            
        # Bullet list: `- Text` or `* Text`
        elif line_stripped.startswith("- ") or line_stripped.startswith("* "):
            pdf.ln(0.5)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(31, 41, 55)
            pdf.cell(5, 5.5, "-", ln=0)
            
            cleaned_line = line_stripped[2:].strip()
            
            old_l_margin = pdf.l_margin
            pdf.set_left_margin(old_l_margin + 5)
            write_rich_text(pdf, cleaned_line, default_font="Helvetica", default_size=9.5, default_style="", default_color=(31, 41, 55), line_height=5.5)
            pdf.ln(5.5)
            pdf.set_left_margin(old_l_margin)
            continue
            
        # Blockquote: `> Text`
        elif line_stripped.startswith("> "):
            pdf.ln(1.5)
            cleaned_line = line_stripped[2:].strip()
            old_l_margin = pdf.l_margin
            
            x_pos = pdf.get_x()
            y_start = pdf.get_y()
            
            pdf.set_left_margin(old_l_margin + 6)
            write_rich_text(pdf, cleaned_line, default_font="Helvetica", default_size=9.5, default_style="I", default_color=(75, 85, 99), line_height=5.5)
            pdf.ln(5.5)
            
            y_end = pdf.get_y()
            pdf.set_draw_color(26, 86, 219)
            pdf.set_linewidth(0.8)
            pdf.line(x_pos + 1, y_start, x_pos + 1, y_end - 1.5)
            
            pdf.set_left_margin(old_l_margin)
            continue
            
        # Standard line or empty line
        else:
            if not line_stripped:
                pdf.ln(2.5)
                continue
                
            write_rich_text(pdf, line_stripped, default_font="Helvetica", default_size=9.5, default_style="", default_color=(31, 41, 55), line_height=5.5)
            pdf.ln(5.5)

def generate_strategy_pdf(res, job_title: str, company: str, linkedin_url: str) -> bytes:
    # Set up PDF with premium geometry
    pdf = CareerPathPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(20, 20, 20) # 20mm margins are much more elegant than 15mm
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Extract candidate name dynamically
    candidate_name = extract_candidate_name(res.tailored_resume)
    
    # ----------------------------------------------------
    # COVER PAGE (Page 1)
    # ----------------------------------------------------
    pdf.ln(10)
    
    # Decorative header element: Elegant horizontal brand stripe
    pdf.set_fill_color(26, 86, 219) # Brand Blue
    pdf.rect(20, 25, 170, 4, style="F")
    
    pdf.ln(20)
    
    # Large beautiful typography
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 86, 219) # Brand Blue
    pdf.cell(0, 6, "AI-OPTIMIZED CAREER PREPARATION DOSSIER", ln=1, align="L")
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(17, 24, 39) # Elegant near-black
    pdf.cell(0, 11, "Tailored Career Path", ln=1, align="L")
    pdf.cell(0, 11, "Document Package", ln=1, align="L")
    pdf.ln(8)
    
    # Decorative subtitle line
    pdf.set_draw_color(229, 231, 235)
    pdf.set_linewidth(1)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(10)
    
    # Beautiful presentation subtitle
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(75, 85, 99)
    pdf.multi_cell(0, 6, "A highly optimized professional portfolio containing a custom tailored resume, personalized cover letter, strategic keywords/gap analysis, and targeted interview preparation instructions.")
    pdf.ln(15)
    
    # Metadata block - layout like a clean table
    pdf.set_fill_color(249, 250, 251) # soft grey card background
    pdf.set_draw_color(229, 231, 235)
    pdf.set_linewidth(0.4)
    pdf.rect(20, pdf.get_y(), 170, 45, style="DF")
    
    y_meta = pdf.get_y() + 5
    
    def draw_meta_row(label, val, y_offset, is_link=False):
        pdf.set_xy(25, y_offset)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(107, 114, 128) # muted grey
        pdf.cell(45, 6, label, ln=0)
        
        pdf.set_font("Helvetica", "B" if not is_link else "", 9.5)
        pdf.set_text_color(26, 86, 219) if is_link else pdf.set_text_color(31, 41, 55)
        if is_link:
            pdf.cell(0, 6, clean_for_pdf(val), ln=1, link=val)
        else:
            pdf.cell(0, 6, clean_for_pdf(val), ln=1)
            
    draw_meta_row("PREPARED FOR:", candidate_name, y_meta)
    draw_meta_row("TARGET POSITION:", job_title, y_meta + 8)
    draw_meta_row("TARGET COMPANY:", company, y_meta + 16)
    draw_meta_row("PORTFOLIO SOURCE:", linkedin_url, y_meta + 24, is_link=True)
    draw_meta_row("GENERATED ON:", datetime.now().strftime("%B %d, %Y"), y_meta + 32)
    
    # Move cursor past the card
    pdf.set_xy(20, y_meta + 45)
    pdf.ln(12)
    
    # Beautiful ATS Match Card
    pdf.set_draw_color(229, 231, 235)
    pdf.set_fill_color(249, 250, 251)
    pdf.rect(20, pdf.get_y(), 170, 26, style="DF")
    
    # Draw left indicator border reflecting match level
    if res.match_score >= 80:
        accent_rgb = (16, 185, 129) # Success Green
    elif res.match_score >= 60:
        accent_rgb = (245, 158, 11) # Amber
    else:
        accent_rgb = (239, 68, 68) # Red
        
    pdf.set_fill_color(*accent_rgb)
    pdf.rect(20, pdf.get_y(), 3, 26, style="F")
    
    # Render match score text
    pdf.set_xy(27, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(100, 5, "ATS ALIGNMENT MATCH SCORE", ln=0)
    
    pdf.set_xy(27, pdf.get_y() + 10)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(120, 130, 140)
    pdf.cell(100, 5, "Optimized for high-dimensional technical terms and requirements.", ln=0)
    
    pdf.set_xy(135, pdf.get_y() - 5)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*accent_rgb)
    pdf.cell(50, 15, f"{res.match_score}%", ln=1, align="R")
    
    # Footer disclaimer on cover page
    pdf.set_xy(20, 265)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(156, 163, 175)
    pdf.cell(0, 5, "Confidential Document Package. Developed in accordance with advanced resume and application guidelines.", ln=1, align="C")
    
    # ----------------------------------------------------
    # PAGE 2: EXECUTIVE ALIGNMENT & STRATEGY
    # ----------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 86, 219)
    pdf.cell(0, 10, "Executive Alignment & Strategic Summary", ln=1)
    pdf.set_draw_color(26, 86, 219)
    pdf.set_linewidth(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 8, "EXECUTIVE FIT SUMMARY", ln=1)
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 5.5, clean_for_pdf(res.fit_summary))
    pdf.ln(10)
    
    # Direct Matches & Gap Areas
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 8, "ATS KEY ALIGNMENTS & KEY GAP UPDATES", ln=1)
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(55, 65, 81)
    
    # Render gaps/suggestions using custom renderer
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 86, 219)
    pdf.cell(0, 7, "Key Recommendations to Address Identified Gaps:", ln=1)
    pdf.ln(1)
    
    for sug in res.resume_suggestions:
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(5, 5.5, "-", ln=0)
        
        old_l_margin = pdf.l_margin
        pdf.set_left_margin(old_l_margin + 5)
        write_rich_text(pdf, sug, default_font="Helvetica", default_size=9.5, default_style="", default_color=(31, 41, 55), line_height=5.5)
        pdf.ln(5.5)
        pdf.set_left_margin(old_l_margin)
        pdf.ln(1)
        
    # ----------------------------------------------------
    # PAGE 3: TAILORED COVER LETTER
    # ----------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 86, 219)
    pdf.cell(0, 10, "1. Tailored Cover Letter", ln=1)
    pdf.set_draw_color(26, 86, 219)
    pdf.set_linewidth(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    write_markdown_line_by_line(pdf, res.cover_letter)
    
    # ----------------------------------------------------
    # PAGE 4: OPTIMIZED PROFESSIONAL RESUME
    # ----------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 86, 219)
    pdf.cell(0, 10, "2. Optimized Professional Resume", ln=1)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    write_markdown_line_by_line(pdf, res.tailored_resume)
    
    # ----------------------------------------------------
    # PAGE 5: STRATEGIC INTERVIEW PREPARATION
    # ----------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 86, 219)
    pdf.cell(0, 10, "3. Targeted Interview Preparation", ln=1)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 8, "Likely Interview Questions & Core Talking Points:", ln=1)
    pdf.ln(2)
    
    for i, prep in enumerate(res.interview_prep):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(26, 86, 219)
        pdf.cell(0, 6, f"Question {i+1}:", ln=1)
        pdf.ln(1)
        
        old_l_margin = pdf.l_margin
        pdf.set_left_margin(old_l_margin + 5)
        
        write_markdown_line_by_line(pdf, prep)
        pdf.ln(4)
        pdf.set_left_margin(old_l_margin)
        
    return bytes(pdf.output())
