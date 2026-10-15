"""Paths and public project links shared across the application."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = ROOT / "data"
DATABASE_PATH = DATA_DIR / "curriculums.db"
PHOTO_DIR = DATA_DIR / "fotos"
GENERATED_CVS_DIR = ROOT / "generated_cvs"

SOURCE_REPOSITORY_URL = "https://github.com/Politrigonomico/CVGen"
SOURCE_ARCHIVE_URL = f"{SOURCE_REPOSITORY_URL}/archive/refs/heads/main.zip"
