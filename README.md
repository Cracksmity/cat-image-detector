# cat-image-detector

Detector de imágenes de gatos con IA. La app recorre una carpeta, clasifica imágenes con CLIP y copia al destino solo las que superan el umbral de confianza.

## Características
- Escaneo recursivo de imágenes (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`, `.tif`).
- Clasificación por lotes con `openai/clip-vit-base-patch32`.
- Interfaz de escritorio con progreso, ETA, contador y cancelación.
- Soporte de aceleración en Windows con `torch-directml` (opcional) y fallback a CPU/CUDA.
- Reporte final `reporte_clasificacion.csv` con resultados y errores.

## Requisitos
- Python 3.10+
- Windows (recomendado para GUI + DirectML)

## Instalación (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Opcional para GPU AMD en Windows:
```powershell
pip install torch-directml
```

## Ejecución
```powershell
python main.py
```

## Uso
1. Selecciona la carpeta **origen**.
2. Selecciona la carpeta **destino**.
3. Ajusta el umbral de confianza.
4. (Opcional) activa **Modo de prueba**.
5. Inicia la clasificación.

## Estructura
```text
cat-image-detector/
├─ main.py
├─ requirements.txt
├─ README.md
├─ CONTRIBUTING.md
├─ .gitignore
└─ app/
   ├─ __init__.py
   ├─ gui.py
   ├─ worker.py
   ├─ classifier.py
   ├─ reporting.py
   └─ utils.py
```

## Contribuciones

¿Quieres mejorar el proyecto? Consulta la [guía de contribución](CONTRIBUTING.md) para ver el flujo de trabajo, ideas de mejora y convenciones.
