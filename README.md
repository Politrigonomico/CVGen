# Generador de CV · LAB21 del ISP21

Aplicación local para crear, editar y descargar currículums en PDF. Está hecha con FastAPI, SQLite, Tailwind CSS y ReportLab para la exposición LAB21 del ISP21.

El código es abierto bajo licencia MIT. El QR de la aplicación descarga el ZIP del repositorio público: <https://github.com/Politrigonomico/CVGen>.

## Ejecutar en Windows

Instalá [Python 3.11 o superior](https://www.python.org/downloads/) y [Node.js LTS](https://nodejs.org/). Después, en PowerShell:

```powershell
git clone https://github.com/Politrigonomico/CVGen.git
cd CVGen
.\start.ps1
```

Si Windows bloquea la ejecución del script en esa sesión, iniciá con:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

La aplicación abre en <http://127.0.0.1:8002>. `start.ps1` crea el entorno Python, instala las dependencias, compila el CSS de Tailwind y levanta FastAPI.

## Iniciar manualmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
npm run build:css
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

## Estructura

```text
app/
  routers/       páginas y endpoints HTTP
  services/      validación, almacenamiento y operaciones de CV
  static/        estilos, imágenes y QR de descarga
  templates/     vistas HTML con Jinja2
  config.py      rutas locales y enlaces públicos del proyecto
  database.py    esquema y conexión SQLite
  pdf.py         diseño del documento PDF
scripts/         herramientas para regenerar recursos
tests/           pruebas con datos temporales
```

La base `data/curriculums.db`, las fotos subidas y los PDF generados quedan en la computadora que ejecuta la aplicación. Se excluyen de Git para que no se publiquen currículums ni datos personales. La aplicación está pensada para uso local y no incluye inicio de sesión.

## Desarrollo

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/generate_qr.py
npm run build:css
```

Para cambiar el QR, actualizá `SOURCE_ARCHIVE_URL` en `app/config.py` y ejecutá `python scripts/generate_qr.py`.

## Créditos

Desarrollo de Software · LAB21 · ISP21. Consultá `LICENSE` y `THIRD_PARTY_NOTICES.md` para las condiciones del código y el uso del logotipo.
