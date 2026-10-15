"""Regenerate the QR image used to download this public repository archive."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import qrcode
from qrcode.constants import ERROR_CORRECT_H

from app.config import SOURCE_ARCHIVE_URL, STATIC_DIR


def main() -> None:
    destination = STATIC_DIR / "images" / "cvgen-source-qr.png"
    destination.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(SOURCE_ARCHIVE_URL)
    qr.make(fit=True)
    qr.make_image(fill_color="#123252", back_color="white").save(destination)
    print(f"QR listo: {destination}")


if __name__ == "__main__":
    main()
