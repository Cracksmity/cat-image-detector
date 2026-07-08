"""
Instalación rápida en terminal (PowerShell):
  1) py -m venv .venv
  2) .\\.venv\\Scripts\\Activate.ps1
  3) pip install -r requirements.txt
  4) (Opcional AMD Windows) pip install torch-directml
     Nota: si usas Python 3.14 puede no existir rueda; usa un entorno con Python 3.11.
  5) python main.py
"""

from app.gui import run_app


if __name__ == "__main__":
    run_app()
