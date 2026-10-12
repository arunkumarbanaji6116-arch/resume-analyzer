"""
DOCX Resume Exporter for CareerForge AI
Generates professionally formatted, ATS-compliant Microsoft Word (.docx) resumes
preserving clean typography, page margins, section borders, and bullet hierarchy.
"""

import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn


def _set_cell_margins(cell, top=50, bottom=50, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def _add_bottom_border(paragraph, color_hex="4F46E5", size="12"):
    """Adds a stylish bottom border to a heading paragraph in docx."""
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="{size}" w:space="4" w:color="{color_hex}"/></w:pBdr>')
    pPr.append(pBdr)


def generate_resume_docx(resume: dict, template_style: str = "classic") -> io.BytesIO:
    """
    Builds an ATS-friendly, beautifully formatted Word (.docx) document
    from structured resume data.
    """
    doc = Document()

    # Set 0.6 inch page margins for maximum ATS compatibility & 1-page efficiency
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.65)
        section.right_margin = Inches(0.65)
        section.page_width = Inches(8.27)  # A4
        section.page_height = Inches(11.69)

    # Palette
    if template_style == "modern":
        primary_color = RGBColor(79, 70, 229)      # Indigo 600
        secondary_color = RGBColor(99, 102, 241)   # Indigo 500
        heading_border_hex = "6366F1"
    elif template_style == "minimal":
        primary_color = RGBColor(17, 24, 39)       # Gray 900
        secondary_color = RGBColor(75, 85, 99)     # Gray 600
        heading_border_hex = "111827"
    else:  # classic
        primary_color = RGBColor(15, 23, 42)       # Slate 900
        secondary_color = RGBColor(67, 56, 202)    # Indigo 700
        heading_border_hex = "0F172A"

    dark_neutral = RGBColor(30, 41, 59)            # Slate 800
    muted_color = RGBColor(100, 116, 139)          # Slate 500

    candidate_name = resume.get("candidate_name") or "Alex Morgan"
    target_role = resume.get("target_role") or "Software Engineer"
    contact_line = resume.get("contact_line") or "alex@example.com | +1 (555) 234-5678"
    summary = resume.get("executive_summary") or ""
    skills = resume.get("skills") or []
    experience = resume.get("experience") or []
    education = resume.get("education") or []
    projects = resume.get("projects_or_certifications") or []

    # 1. HEADER
    p_name = doc.add_paragraph()
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(2)
    p_name.paragraph_format.line_spacing = 1.05
    if template_style == "minimal":
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_name = p_name.add_run(candidate_name)
    run_name.font.name = "Calibri"
    run_name.font.size = Pt(22)
    run_name.font.bold = True
    run_name.font.color.rgb = primary_color

    p_role = doc.add_paragraph()
    p_role.paragraph_format.space_before = Pt(0)
    p_role.paragraph_format.space_after = Pt(3)
    if template_style == "minimal":
        p_role.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_role = p_role.add_run(target_role)
    run_role.font.name = "Calibri"
    run_role.font.size = Pt(12)
    run_role.font.bold = True
    run_role.font.color.rgb = secondary_color

    p_contact = doc.add_paragraph()
    p_contact.paragraph_format.space_before = Pt(0)
    p_contact.paragraph_format.space_after = Pt(10)
    if template_style == "minimal":
        p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_contact = p_contact.add_run(contact_line)
    run_contact.font.name = "Calibri"
    run_contact.font.size = Pt(9.5)
    run_contact.font.color.rgb = muted_color

    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title.upper())
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = primary_color
        _add_bottom_border(p, color_hex=heading_border_hex, size="10")
        return p

    # 2. PROFESSIONAL SUMMARY
    if summary:
        add_section_header("Professional Summary")
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_before = Pt(2)
        p_sum.paragraph_format.space_after = Pt(6)
        p_sum.paragraph_format.line_spacing = 1.15
        run_sum = p_sum.add_run(summary)
        run_sum.font.name = "Calibri"
        run_sum.font.size = Pt(10)
        run_sum.font.color.rgb = dark_neutral

    # Check if fresher mode (education & projects prioritized)
    is_fresher = resume.get("fresher_mode", False)

    def render_education_section():
        if not education:
            return
        add_section_header("Education & Academic Background" if is_fresher else "Education")
        for edu in education:
            p_edu = doc.add_paragraph()
            p_edu.paragraph_format.space_before = Pt(2)
            p_edu.paragraph_format.space_after = Pt(1)
            p_edu.paragraph_format.keep_with_next = True

            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            details = edu.get("details", "")

            r_deg = p_edu.add_run(f"{degree}")
            r_deg.font.name = "Calibri"
            r_deg.font.size = Pt(10)
            r_deg.font.bold = True
            r_deg.font.color.rgb = primary_color

            if institution:
                r_inst = p_edu.add_run(f" — {institution}")
                r_inst.font.name = "Calibri"
                r_inst.font.size = Pt(10)
                r_inst.font.color.rgb = dark_neutral

            if year:
                r_yr = p_edu.add_run(f"  ({year})")
                r_yr.font.name = "Calibri"
                r_yr.font.size = Pt(9.5)
                r_yr.font.color.rgb = muted_color

            if details:
                p_det = doc.add_paragraph()
                p_det.paragraph_format.space_before = Pt(0)
                p_det.paragraph_format.space_after = Pt(4)
                p_det.paragraph_format.left_indent = Inches(0.2)
                r_det = p_det.add_run(details)
                r_det.font.name = "Calibri"
                r_det.font.size = Pt(9)
                r_det.font.color.rgb = muted_color

    def render_projects_section():
        if not projects:
            return
        title = "Academic Projects & Capstone" if is_fresher else "Key Projects & Certifications"
        add_section_header(title)
        for proj in projects:
            p_p = doc.add_paragraph()
            p_p.paragraph_format.space_before = Pt(2)
            p_p.paragraph_format.space_after = Pt(2)
            p_p.paragraph_format.left_indent = Inches(0.15)
            
            p_title = proj.get("title", "")
            p_details = proj.get("details", "")

            r_t = p_p.add_run(f"• {p_title}: ")
            r_t.font.name = "Calibri"
            r_t.font.size = Pt(9.5)
            r_t.font.bold = True
            r_t.font.color.rgb = primary_color

            r_d = p_p.add_run(p_details)
            r_d.font.name = "Calibri"
            r_d.font.size = Pt(9.5)
            r_d.font.color.rgb = dark_neutral

    def render_experience_section():
        if not experience:
            return
        title = "Internships & Professional Experience" if is_fresher else "Professional Experience"
        add_section_header(title)
        for job in experience:
            p_job = doc.add_paragraph()
            p_job.paragraph_format.space_before = Pt(4)
            p_job.paragraph_format.space_after = Pt(1)
            p_job.paragraph_format.keep_with_next = True

            role_title = job.get("title", "")
            company = job.get("company", "")
            period = job.get("period", "")
            loc = job.get("location", "")

            r_title = p_job.add_run(role_title)
            r_title.font.name = "Calibri"
            r_title.font.size = Pt(10.5)
            r_title.font.bold = True
            r_title.font.color.rgb = primary_color

            if company:
                r_comp = p_job.add_run(f" | {company}")
                r_comp.font.name = "Calibri"
                r_comp.font.size = Pt(10)
                r_comp.font.bold = True
                r_comp.font.color.rgb = secondary_color

            meta_parts = [p for p in (period, loc) if p]
            if meta_parts:
                r_meta = p_job.add_run(f"  ·  {' — '.join(meta_parts)}")
                r_meta.font.name = "Calibri"
                r_meta.font.size = Pt(9.5)
                r_meta.font.color.rgb = muted_color

            bullets = job.get("bullets", [])
            for bullet in bullets:
                p_b = doc.add_paragraph(style='List Bullet')
                p_b.paragraph_format.space_before = Pt(1)
                p_b.paragraph_format.space_after = Pt(2)
                p_b.paragraph_format.left_indent = Inches(0.25)
                p_b.paragraph_format.line_spacing = 1.12
                r_b = p_b.add_run(bullet)
                r_b.font.name = "Calibri"
                r_b.font.size = Pt(9.5)
                r_b.font.color.rgb = dark_neutral

    # 3. SKILLS SECTION
    if skills:
        add_section_header("Core Competencies & Technical Skills")
        for group in skills:
            category = group.get("category", "Skills")
            items = group.get("items", [])
            items_str = ", ".join(items) if isinstance(items, list) else str(items)

            p_sk = doc.add_paragraph()
            p_sk.paragraph_format.space_before = Pt(1)
            p_sk.paragraph_format.space_after = Pt(2)
            p_sk.paragraph_format.left_indent = Inches(0.1)

            r_cat = p_sk.add_run(f"{category}: ")
            r_cat.font.name = "Calibri"
            r_cat.font.size = Pt(9.5)
            r_cat.font.bold = True
            r_cat.font.color.rgb = primary_color

            r_items = p_sk.add_run(items_str)
            r_items.font.name = "Calibri"
            r_items.font.size = Pt(9.5)
            r_items.font.color.rgb = dark_neutral

    if is_fresher:
        # Fresher order: Education -> Projects -> Internships
        render_education_section()
        render_projects_section()
        render_experience_section()
    else:
        # Professional order: Experience -> Education -> Projects
        render_experience_section()
        render_education_section()
        render_projects_section()

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)
    return stream
