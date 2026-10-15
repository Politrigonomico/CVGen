"""Service tests that use a disposable SQLite database and PDF directory."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import database
from app.services import curriculums


class CurriculumServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "test.db"
        self.data_dir = self.root / "data"
        self.pdf_dir = self.root / "pdfs"
        self.data_patch = patch.object(database, "DATA_DIR", self.data_dir)
        self.db_patch = patch.object(database, "DATABASE_PATH", self.db_path)
        self.pdf_patch = patch.object(curriculums, "GENERATED_CVS_DIR", self.pdf_dir)
        self.data_patch.start()
        self.db_patch.start()
        self.pdf_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.pdf_patch.stop)
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


if __name__ == "__main__":
    unittest.main()
