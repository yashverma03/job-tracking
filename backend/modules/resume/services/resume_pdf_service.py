import io
import os

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from common.exceptions.api_exceptions import ApiError
from modules.resume.types.resume_types import ResumeAiOutput, ResumeInput

PAGE_MARGIN = 0.45 * inch

NAME_STYLE = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=3)
CONTACT_STYLE = ParagraphStyle('Contact', fontName='Helvetica', fontSize=8.5, alignment=1, textColor=colors.HexColor('#333333'))
HEADING_STYLE = ParagraphStyle('Heading', fontName='Helvetica-Bold', fontSize=10.5, spaceBefore=6, spaceAfter=1)
BODY_STYLE = ParagraphStyle('Body', fontName='Helvetica', fontSize=9, leading=11)
BULLET_STYLE = ParagraphStyle('Bullet', fontName='Helvetica', fontSize=9, leading=11, leftIndent=14, bulletIndent=2, spaceAfter=1)
ROLE_STYLE = ParagraphStyle('Role', fontName='Helvetica-Bold', fontSize=9.5)
DATE_STYLE = ParagraphStyle('Date', fontName='Helvetica', fontSize=9, alignment=2, textColor=colors.HexColor('#333333'))


def _heading(text: str) -> list:
    return [
        Paragraph(text, HEADING_STYLE),
        HRFlowable(width='100%', thickness=0.75, color=colors.HexColor('#999999'), spaceAfter=4),
    ]


def _two_column_row(left: str, right: str, left_style: ParagraphStyle, right_style: ParagraphStyle, usable_width: float) -> Table:
    table = Table(
        [[Paragraph(left, left_style), Paragraph(right, right_style)]],
        colWidths=[usable_width * 0.7, usable_width * 0.3],
    )
    table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _build_story(resume_input: ResumeInput, ai_output: ResumeAiOutput, usable_width: float) -> list:
    contact = resume_input.contact
    story = [
        Paragraph(contact.name, NAME_STYLE),
        Paragraph(
            ' | '.join([
                contact.portfolio_url, contact.email, contact.phone,
                contact.linkedin_url, contact.github_url, contact.gfg_url, contact.leetcode_url,
            ]),
            CONTACT_STYLE,
        ),
        Spacer(1, 6),
    ]

    story += _heading('SUMMARY')
    story.append(Paragraph(ai_output.summary, BODY_STYLE))

    story += _heading('EXPERIENCE')
    for entry, bullets in zip(resume_input.experience, ai_output.experience_bullets):
        story.append(_two_column_row(
            f'{entry.title} | {entry.company}', entry.duration, ROLE_STYLE, DATE_STYLE, usable_width,
        ))
        for bullet in bullets:
            story.append(Paragraph(f'●&nbsp;&nbsp;{bullet}', BULLET_STYLE))
        story.append(Spacer(1, 2))

    story += _heading('SKILLS')
    for category, items in ai_output.skills.items():
        if not items:
            continue
        story.append(Paragraph(f'<b>{category}:</b> {", ".join(items)}', BODY_STYLE))

    story += _heading('CERTIFICATIONS')
    for cert in resume_input.certifications:
        story.append(Paragraph(f'●&nbsp;&nbsp;{cert.label} (<link href="{cert.url}">link</link>)', BULLET_STYLE))

    story += _heading('EDUCATION')
    for edu in resume_input.education:
        story.append(_two_column_row(
            f'{edu.degree}, {edu.institution}', edu.years, BODY_STYLE, DATE_STYLE, usable_width,
        ))

    return story


def render_resume_pdf(resume_input: ResumeInput, ai_output: ResumeAiOutput, output_path: str) -> None:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=f'{resume_input.contact.name} Resume',
        author=resume_input.contact.name,
    )
    usable_width = A4[0] - PAGE_MARGIN * 2

    story = _build_story(resume_input, ai_output, usable_width)
    doc.build(story)

    page_count = len(PdfReader(io.BytesIO(buffer.getvalue())).pages)
    if page_count > 1:
        raise ApiError(
            f'Generated resume would span {page_count} pages; content must fit on a single page.',
            status_code=500,
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
