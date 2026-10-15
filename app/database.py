from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3

from .config import DATA_DIR, DATABASE_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS curriculums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                profesion TEXT NOT NULL,
                otras_profesiones TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                domicilio TEXT NOT NULL DEFAULT '',
                localidad TEXT NOT NULL DEFAULT '',
                dni TEXT NOT NULL DEFAULT '',
                fecha_nacimiento TEXT NOT NULL DEFAULT '',
                estado_civil TEXT NOT NULL DEFAULT '',
                sexo TEXT NOT NULL DEFAULT '',
                perfil TEXT NOT NULL DEFAULT '',
                nivel_educativo TEXT NOT NULL DEFAULT '',
                estado_estudios TEXT NOT NULL DEFAULT '',
                estudios TEXT NOT NULL DEFAULT '',
                experiencia TEXT NOT NULL DEFAULT '',
                carnets TEXT NOT NULL DEFAULT '',
                foto_path TEXT NOT NULL DEFAULT '',
                certificado_alimentos INTEGER NOT NULL DEFAULT 0,
                movilidad_propia INTEGER NOT NULL DEFAULT 0,
                creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = {row[1] for row in db.execute("PRAGMA table_info(curriculums)")}
        if "foto_path" not in columns:
            db.execute("ALTER TABLE curriculums ADD COLUMN foto_path TEXT NOT NULL DEFAULT ''")
        db.execute("CREATE INDEX IF NOT EXISTS idx_curriculums_apellido ON curriculums(apellido)")
