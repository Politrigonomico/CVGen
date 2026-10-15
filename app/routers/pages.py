"""Landing and source-code walkthrough pages."""

import inspect

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..config import SOURCE_ARCHIVE_URL, SOURCE_REPOSITORY_URL, TEMPLATES_DIR
from ..database import connect, init_db
from ..pdf import generate_pdf
from ..services.curriculums import (
    create_cv,
    parse_form_fields,
    update_cv,
    validate_form,
)
from .curriculums import read_submission


router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, q: str = Query(default="", max_length=100)):
    with connect() as db:
        if q.strip():
            needle = f"%{q.strip()}%"
            rows = db.execute(
                """SELECT * FROM curriculums
                   WHERE nombre LIKE ? OR apellido LIKE ? OR profesion LIKE ? OR localidad LIKE ? OR otras_profesiones LIKE ?
                   ORDER BY creado_en DESC, id DESC""",
                (needle, needle, needle, needle, needle),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM curriculums ORDER BY creado_en DESC, id DESC LIMIT 8"
            ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM curriculums").fetchone()[0]
        today = db.execute(
            "SELECT COUNT(*) FROM curriculums WHERE date(creado_en) = date('now','localtime')"
        ).fetchone()[0]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "people": [dict(row) for row in rows],
            "total": total,
            "today": today,
            "q": q,
            "source_archive_url": SOURCE_ARCHIVE_URL,
            "source_repository_url": SOURCE_REPOSITORY_URL,
        },
    )


@router.get("/como-funciona", response_class=HTMLResponse)
async def how_it_works(request: Request):
    sections = [
        {
            "step": "01",
            "title": "El navegador muestra el formulario",
            "file": "app/templates/new_cv.html · estructura simplificada",
            "description": "El formulario reúne los datos. El navegador los envía al servidor con POST; el mismo formulario sirve para crear un CV y editar uno existente.",
            "code": '<form action="/cv/nuevo" method="post" enctype="multipart/form-data">\n  <input name="nombre" required>\n  <input name="apellido" required>\n  <input name="profesion" required>\n  <button type="submit">Guardar y generar CV</button>\n</form>',
        },
        {
            "step": "02",
            "title": "FastAPI revisa los datos",
            "file": "app/routers/curriculums.py · read_submission()",
            "description": "El servidor recibe el formulario, controla campos obligatorios, límites de texto, correo y foto antes de guardar.",
            "code": inspect.getsource(read_submission).strip(),
        },
        {
            "step": "03",
            "title": "SQLite guarda el currículum",
            "file": "app/database.py · connect() e init_db()",
            "description": "SQLite conserva cada CV en un archivo local. La tabla define los datos y cada registro tiene un identificador para volver a abrirlo o editarlo.",
            "code": f"{inspect.getsource(connect).strip()}\n\n{inspect.getsource(init_db).strip()}",
        },
        {
            "step": "04",
            "title": "La edición actualiza los datos y el PDF",
            "file": "app/services/curriculums.py · update_cv()",
            "description": "Al guardar cambios, se actualiza el registro correspondiente y se vuelve a generar el PDF con la información nueva.",
            "code": inspect.getsource(update_cv).strip(),
        },
        {
            "step": "05",
            "title": "ReportLab arma el CV descargable",
            "file": "app/pdf.py · generate_pdf()",
            "description": "ReportLab compone las secciones, los datos de contacto y el diseño en una página PDF lista para descargar o compartir.",
            "code": inspect.getsource(generate_pdf).strip(),
        },
        {
            "step": "06",
            "title": "Las reglas del formulario viven en un servicio",
            "file": "app/services/curriculums.py · parse_form_fields() y validate_form()",
            "description": "La lógica queda separada de las rutas web: una función normaliza los textos y otra valida antes de crear o actualizar el CV.",
            "code": f"{inspect.getsource(parse_form_fields).strip()}\n\n{inspect.getsource(validate_form).strip()}\n\n{inspect.getsource(create_cv).strip()}",
        },
    ]
    return templates.TemplateResponse(
        request=request,
        name="how_it_works.html",
        context={
            "sections": sections,
            "source_archive_url": SOURCE_ARCHIVE_URL,
            "source_repository_url": SOURCE_REPOSITORY_URL,
        },
    )
