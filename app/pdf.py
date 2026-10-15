from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

BLUE = colors.HexColor("#087EAE")
RED = colors.HexColor("#E5303C")
INK = colors.HexColor("#283544")
MUTED = colors.HexColor("#64748B")
WHITE = colors.white


def _register_fonts() -> str:
    font_dir = Path("C:/Windows/Fonts")
    regular, bold = font_dir / "arial.ttf", font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        try:
            pdfmetrics.registerFont(TTFont("Arroyo", str(regular)))
            pdfmetrics.registerFont(TTFont("Arroyo-Bold", str(bold)))
            return "Arroyo"
        except (OSError, ValueError):
            pass
    return "Helvetica"


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def generate_pdf(person: dict) -> bytes:
    font = _register_fonts()
    bold_font = "Arroyo-Bold" if font == "Arroyo" else "Helvetica-Bold"
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", parent=styles["Title"], fontName=bold_font, fontSize=23, leading=27, textColor=INK, alignment=TA_LEFT, spaceAfter=5)
    role_style = ParagraphStyle("Role", parent=styles["Normal"], fontName=font, fontSize=10, leading=15, textColor=BLUE, spaceAfter=10)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontName=bold_font, fontSize=10, leading=14, textColor=BLUE, spaceBefore=12, spaceAfter=5, keepWithNext=True)
    body_style = ParagraphStyle("Body", parent=styles["BodyText"], fontName=font, fontSize=9, leading=13, textColor=INK, spaceAfter=5, splitLongWords=True)
    side_title = ParagraphStyle("SideTitle", parent=styles["BodyText"], fontName=bold_font, fontSize=7.5, leading=10, textColor=colors.HexColor("#B8E8F6"), spaceBefore=7, spaceAfter=2)
    side_body = ParagraphStyle("SideBody", parent=styles["BodyText"], fontName=font, fontSize=8, leading=11, textColor=WHITE, spaceAfter=4, splitLongWords=True)

    story = [_p(f"{person['nombre']} {person['apellido']}".strip(), name_style), _p(person["profesion"], role_style)]
    sections = [
        ("Perfil profesional", person["perfil"]),
        ("Formación académica", "\n".join(filter(None, [
            (person["nivel_educativo"] + (" · En curso" if person["estado_estudios"] == "cursando" else " · Completado")) if person["nivel_educativo"] else "",
            person["estudios"],
        ]))),
        ("Experiencia, habilidades y disponibilidad", person["experiencia"]),
        ("Otros oficios", person["otras_profesiones"]),
    ]
    for title, text in sections:
        if text:
            story.extend([_p(title, section_style), _p(text, body_style)])
    if not any(person[key] for key in ("perfil", "estudios", "experiencia", "otras_profesiones")):
        story.extend([_p("Perfil profesional", section_style), _p("Información disponible a solicitud.", body_style)])

    contact = [("Teléfono", person["telefono"]), ("Correo electrónico", person["email"])]
    address = ", ".join(filter(None, [person["domicilio"], person["localidad"]]))
    contact += [("Domicilio", address), ("DNI", person["dni"])]
    if person["fecha_nacimiento"]:
        try:
            birth = datetime.strptime(person["fecha_nacimiento"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            birth = person["fecha_nacimiento"]
        contact.append(("Fecha de nacimiento", birth))
    personal = " · ".join(filter(None, [person["estado_civil"], person["sexo"]]))
    if personal:
        contact.append(("Datos personales", personal))
    skills = list(filter(None, [person["carnets"], "Manipulación de alimentos" if person["certificado_alimentos"] else "", "Movilidad propia" if person["movilidad_propia"] else ""]))
    if skills:
        contact.append(("Competencias", " · ".join(skills)))

    def draw_sidebar(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BLUE)
        canvas.rect(0, 0, 55 * mm, A4[1], fill=1, stroke=0)
        canvas.setFillColor(RED)
        canvas.rect(55 * mm, 0, 1.5 * mm, A4[1], fill=1, stroke=0)
        photo = person.get("foto_path", "")
        side_top = A4[1] - 16 * mm
        if photo and Path(photo).is_file():
            size = 36 * mm
            canvas.drawImage(photo, 9.5 * mm, side_top - size, width=size, height=size, preserveAspectRatio=True, anchor="c", mask="auto")
            side_top -= size + 7 * mm
        else:
            side_top -= 4 * mm
        width = 39 * mm
        y = side_top
        for label, text in contact:
            if not text:
                continue
            heading = _p(label.upper(), side_title)
            _, height = heading.wrap(width, y)
            if y - height < 16 * mm:
                break
            heading.drawOn(canvas, 8 * mm, y - height)
            y -= height + 2
            content = _p(text, side_body)
            _, height = content.wrap(width, y)
            if y - height < 12 * mm:
                break
            content.drawOn(canvas, 8 * mm, y - height)
            y -= height + 5
        canvas.setFont(font, 7)
        canvas.setFillColor(WHITE)
        canvas.drawString(8 * mm, 8 * mm, "LAB21 · ISP21")
        canvas.setFont(font, 6.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - 15 * mm, 8 * mm, "Creado en LAB21 del ISP21 · Desarrollo de Software")
        canvas.restoreState()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=68 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"CV — {person['nombre']} {person['apellido']}", author="LAB21 del ISP21 · Desarrollo de Software")
    doc.build(story, onFirstPage=draw_sidebar, onLaterPages=draw_sidebar)
    return buffer.getvalue()
