"""CV validation and business operations."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
import re

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import GENERATED_CVS_DIR, PHOTO_DIR
from ..database import connect
from ..pdf import generate_pdf


FORM_FIELDS = (
    "nombre", "apellido", "profesion", "otras_profesiones", "telefono", "email", "domicilio", "localidad", "dni",
    "fecha_nacimiento", "estado_civil", "sexo", "perfil", "nivel_educativo", "estado_estudios", "estudios", "experiencia", "carnets",
)
FIELD_LIMITS = {
    "nombre": 100,
    "apellido": 100,
    "profesion": 140,
    "telefono": 40,
    "email": 150,
    "domicilio": 180,
    "localidad": 120,
    "dni": 30,
    "estado_civil": 60,
    "sexo": 40,
    "perfil": 1800,
    "otras_profesiones": 800,
    "estudios": 1800,
    "experiencia": 3000,
    "carnets": 200,
}
EDUCATION_LEVELS = ("Primaria", "Secundaria", "Terciario", "Universidad")


def parse_form_fields(form_data) -> dict:
    """Normalize browser form values into the fields stored by SQLite."""
    form = {key: str(form_data.get(key, "")).strip() for key in FORM_FIELDS}
    form["certificado_alimentos"] = "certificado_alimentos" in form_data
    form["movilidad_propia"] = "movilidad_propia" in form_data
    return form


def validate_form(form: dict, photo_bytes: bytes) -> list[str]:
    """Return user-facing validation errors and normalize education fields."""
    errors = []
    if not all(form[key] for key in ("nombre", "apellido", "profesion")):
        errors.append("Completá nombre, apellido y profesión para generar el CV.")

    for field, maximum in FIELD_LIMITS.items():
        if len(form[field]) > maximum:
            errors.append(f"{field.replace('_', ' ').capitalize()}: máximo {maximum} caracteres.")

    if form["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", form["email"]):
        errors.append("Ingresá un correo electrónico válido.")
    if form["fecha_nacimiento"]:
        try:
            datetime.strptime(form["fecha_nacimiento"], "%Y-%m-%d")
        except ValueError:
            errors.append("Ingresá una fecha de nacimiento válida.")

    if len(photo_bytes) > 2 * 1024 * 1024:
        errors.append("La foto no debe superar los 2 MB.")
    elif photo_bytes:
        try:
            with Image.open(BytesIO(photo_bytes)) as source:
                source.verify()
            with Image.open(BytesIO(photo_bytes)) as source:
                if source.width * source.height > 20_000_000:
                    raise ValueError("Imagen demasiado grande")
        except (UnidentifiedImageError, OSError, ValueError):
            errors.append("La foto debe ser una imagen JPG, PNG o WebP válida.")

    if form["nivel_educativo"] not in EDUCATION_LEVELS:
        form["nivel_educativo"] = ""
        form["estado_estudios"] = ""
    elif form["estado_estudios"] not in {"completada", "cursando"}:
        form["estado_estudios"] = "completada"
    return errors


def list_cvs(search: str = "") -> list[dict]:
    with connect() as db:
        if search:
            needle = f"%{search.strip()}%"
            rows = db.execute(
                """SELECT * FROM curriculums
                   WHERE nombre LIKE ? OR apellido LIKE ? OR profesion LIKE ? OR localidad LIKE ? OR otras_profesiones LIKE ?
                   ORDER BY creado_en DESC, id DESC""",
                (needle, needle, needle, needle, needle),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM curriculums ORDER BY creado_en DESC, id DESC LIMIT 8").fetchall()
    return [dict(row) for row in rows]


def get_cv(cv_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT * FROM curriculums WHERE id = ?", (cv_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    return dict(row)


def save_photo(cv_id: int, photo_bytes: bytes) -> str:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(BytesIO(photo_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image_path = PHOTO_DIR / f"foto_{cv_id}.jpg"
            ImageOps.fit(image, (720, 720)).save(image_path, "JPEG", quality=88, optimize=True)
        return str(image_path)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="No se pudo procesar la foto seleccionada.") from exc


def write_pdf(person: dict) -> Path:
    GENERATED_CVS_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_CVS_DIR / f"cv_{person['id']}.pdf"
    path.write_bytes(generate_pdf(person))
    return path


def create_cv(form: dict, photo_bytes: bytes) -> dict:
    columns = list(form)
    values = [int(form[key]) if key in {"certificado_alimentos", "movilidad_propia"} else form[key] for key in columns]
    with connect() as db:
        placeholders = ", ".join("?" for _ in columns)
        cursor = db.execute(f"INSERT INTO curriculums ({', '.join(columns)}) VALUES ({placeholders})", values)
        cv_id = cursor.lastrowid

    person = get_cv(cv_id)
    if photo_bytes:
        person["foto_path"] = save_photo(cv_id, photo_bytes)
        with connect() as db:
            db.execute("UPDATE curriculums SET foto_path = ? WHERE id = ?", (person["foto_path"], cv_id))
    write_pdf(person)
    return person


def update_cv(cv_id: int, form: dict, photo_bytes: bytes) -> dict:
    person = get_cv(cv_id)
    if photo_bytes:
        form["foto_path"] = save_photo(cv_id, photo_bytes)

    columns = list(form)
    assignments = ", ".join(f"{column} = ?" for column in columns)
    values = [int(form[key]) if key in {"certificado_alimentos", "movilidad_propia"} else form[key] for key in columns]
    with connect() as db:
        db.execute(f"UPDATE curriculums SET {assignments} WHERE id = ?", (*values, cv_id))

    updated_person = get_cv(cv_id)
    write_pdf(updated_person)
    return updated_person


def pdf_path_for(cv_id: int) -> Path:
    person = get_cv(cv_id)
    return write_pdf(person)
