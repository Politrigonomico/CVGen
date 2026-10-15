"""HTTP routes for creating, editing, viewing, and downloading CVs."""

from pathlib import Path
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import PHOTO_DIR, TEMPLATES_DIR
from ..services.curriculums import (
    EDUCATION_LEVELS,
    create_cv,
    get_cv,
    parse_form_fields,
    update_cv,
    validate_form,
    write_pdf,
)


router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
MAX_PHOTO_BYTES = 2 * 1024 * 1024


async def read_submission(request: Request) -> tuple[dict, bytes, list[str]]:
    """Read and validate one browser form submission, including its optional photo."""
    form_data = await request.form()
    form = parse_form_fields(form_data)
    photo_bytes = b""
    upload = form_data.get("foto")
    if upload is not None and getattr(upload, "filename", ""):
        photo_bytes = await upload.read(MAX_PHOTO_BYTES + 1)
    errors = validate_form(form, photo_bytes)
    return form, photo_bytes, errors


def render_cv_form(
    request: Request,
    *,
    form: dict,
    errors: list[str],
    person: dict | None = None,
    cv_id: int | None = None,
    editing: bool = False,
    status_code: int = 200,
):
    """Render the shared create/edit form with current data and validation errors."""
    return templates.TemplateResponse(
        request=request,
        name="new_cv.html",
        status_code=status_code,
        context={
            "errors": errors,
            "form": form,
            "person": person,
            "editing": editing,
            "cv_id": cv_id,
            "levels": EDUCATION_LEVELS,
        },
    )


@router.get("/cv/nuevo", response_class=HTMLResponse)
async def new_cv(request: Request):
    return render_cv_form(request, form={}, errors=[])


@router.post("/cv/nuevo")
async def create_cv_route(request: Request):
    form, photo_bytes, errors = await read_submission(request)
    if errors:
        return render_cv_form(request, form=form, errors=errors, status_code=422)

    person = create_cv(form, photo_bytes)
    return RedirectResponse(url=f"/cv/{person['id']}?creado=1", status_code=303)


@router.get("/cv/{cv_id}/editar", response_class=HTMLResponse)
async def edit_cv_form(request: Request, cv_id: int):
    person = get_cv(cv_id)
    return render_cv_form(request, form=person, errors=[], person=person, cv_id=cv_id, editing=True)


@router.post("/cv/{cv_id}/editar")
async def update_cv_route(request: Request, cv_id: int):
    person = get_cv(cv_id)
    form, photo_bytes, errors = await read_submission(request)
    if errors:
        return render_cv_form(
            request,
            form=form,
            errors=errors,
            person=person,
            cv_id=cv_id,
            editing=True,
            status_code=422,
        )

    update_cv(cv_id, form, photo_bytes)
    return RedirectResponse(url=f"/cv/{cv_id}?actualizado=1", status_code=303)


@router.get("/cv/{cv_id}/foto")
async def show_photo(cv_id: int):
    person = get_cv(cv_id)
    path = Path(person.get("foto_path", ""))
    if not path.is_file() or path.parent.resolve() != PHOTO_DIR.resolve():
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/cv/{cv_id}/pdf")
async def download_pdf(cv_id: int):
    person = get_cv(cv_id)
    path = write_pdf(person)
    filename = re.sub(r"[^\w-]+", "_", f"CV_{person['nombre']}_{person['apellido']}", flags=re.UNICODE)
    return FileResponse(path, media_type="application/pdf", filename=f"{filename}.pdf")


@router.get("/cv/{cv_id}", response_class=HTMLResponse)
async def show_cv(request: Request, cv_id: int, creado: bool = False, actualizado: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="show_cv.html",
        context={"person": get_cv(cv_id), "created": creado, "updated": actualizado},
    )
