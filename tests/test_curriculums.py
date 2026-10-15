"""Service tests that use a disposable SQLite database and PDF directory."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app import database
from app.services import curriculums


class CurriculumServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "test.db"
        self.data_dir = self.root / "data"
        self.photo_dir = self.data_dir / "fotos"
        self.pdf_dir = self.root / "pdfs"
        self.data_patch = patch.object(database, "DATA_DIR", self.data_dir)
        self.db_patch = patch.object(database, "DATABASE_PATH", self.db_path)
        self.pdf_patch = patch.object(curriculums, "GENERATED_CVS_DIR", self.pdf_dir)
        self.photo_patch = patch.object(curriculums, "PHOTO_DIR", self.photo_dir)
        self.data_patch.start()
        self.db_patch.start()
        self.pdf_patch.start()
        self.photo_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.pdf_patch.stop)
        self.addCleanup(self.photo_patch.stop)
        database.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_update_cv_regenerates_pdf(self):
        form = curriculums.parse_form_fields(
            {"nombre": "Ada", "apellido": "Lovelace", "profesion": "Programadora"}
        )
        created = curriculums.create_cv(form, b"")
        pdf_path = self.pdf_dir / f"cv_{created['id']}.pdf"
        self.assertTrue(pdf_path.is_file())
        self.assertGreater(pdf_path.stat().st_size, 0)

        updated_form = curriculums.parse_form_fields(
            {"nombre": "Ada", "apellido": "Lovelace", "profesion": "Analista"}
        )
        updated = curriculums.update_cv(created["id"], updated_form, b"")

        self.assertEqual(updated["profesion"], "Analista")
        self.assertTrue(pdf_path.is_file())

    def test_free_text_fields_are_preserved_and_validated(self):
        form = curriculums.parse_form_fields(
            {
                "nombre": "Ada",
                "apellido": "Lovelace",
                "profesion": "Programadora",
                "experiencia": "Experiencia redactada libremente.",
                "email": "correo-invalido",
                "movilidad_propia": "on",
            }
        )

        errors = curriculums.validate_form(form, b"")

        self.assertEqual(form["experiencia"], "Experiencia redactada libremente.")
        self.assertTrue(form["movilidad_propia"])
        self.assertIn("Ingresá un correo electrónico válido.", errors)

    def test_delete_cv_removes_record_pdf_and_uploaded_photo(self):
        form = curriculums.parse_form_fields(
            {"nombre": "Ada", "apellido": "Lovelace", "profesion": "Programadora"}
        )
        person = curriculums.create_cv(form, b"")
        pdf_path = self.pdf_dir / f"cv_{person['id']}.pdf"
        self.photo_dir.mkdir(parents=True)
        photo_path = self.photo_dir / f"foto_{person['id']}.jpg"
        photo_path.write_bytes(b"foto de prueba")
        with database.connect() as db:
            db.execute(
                "UPDATE curriculums SET foto_path = ? WHERE id = ?",
                (str(photo_path), person["id"]),
            )

        curriculums.delete_cv(person["id"])

        self.assertFalse(pdf_path.exists())
        self.assertFalse(photo_path.exists())
        with self.assertRaises(HTTPException) as error:
            curriculums.get_cv(person["id"])
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
