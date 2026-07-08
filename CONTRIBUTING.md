# Guía de contribución

¡Gracias por tu interés en mejorar **cat-image-detector**! Esta guía explica cómo configurar el entorno, proponer mejoras y enviar un Pull Request.

---

## 1. Configura tu entorno local

```powershell
# 1. Clona el repositorio
git clone https://github.com/Cracksmity/cat-image-detector.git
cd cat-image-detector

# 2. Crea un entorno virtual e instala dependencias
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Opcional: GPU AMD en Windows
pip install torch-directml

# 4. Lanza la app para verificar que todo funciona
python main.py
```

---

## 2. Flujo para contribuir (GitHub Flow)

```
main  ──┬──────────────────────────────────────► main (estable)
        │
        └──► feature/mi-mejora  ──► PR  ──► revisión  ──► merge
```

```powershell
# Crea una rama descriptiva desde main
git switch -c feature/nombre-de-tu-mejora

# Haz tus cambios y confirma con mensajes claros
git add .
git commit -m "feat: descripción breve de la mejora"

# Sube la rama a tu fork
git push origin feature/nombre-de-tu-mejora
```

Luego abre un **Pull Request** en GitHub contra la rama `main` con:
- **Título** claro y corto.
- **Descripción** de qué cambia y por qué.
- Capturas de pantalla si hay cambios visuales.

---

## 3. Ideas de mejora

Estas son áreas concretas donde el proyecto puede crecer:

### 🧠 Modelos / Clasificador (`app/classifier.py`)
- Cambiar el `model_id` por un modelo más preciso, como `openai/clip-vit-large-patch14`.
- Agregar soporte para etiquetas personalizadas por el usuario desde la GUI.
- Implementar caché del modelo en disco para acelerar el arranque.

### ⚡ Rendimiento (`app/worker.py`)
- Paralelizar la carga de imágenes con `concurrent.futures.ThreadPoolExecutor`.
- Redimensionar imágenes antes de enviarlas al modelo para reducir uso de memoria.
- Ajustar `BATCH_SIZE` dinámicamente según la VRAM/RAM disponible.

### 🖼️ Interfaz (`app/gui.py`)
- Agregar previsualizaciones de las imágenes clasificadas como gato.
- Mostrar una galería de resultados al finalizar.
- Añadir soporte para arrastrar y soltar carpetas.

### 📊 Reportes (`app/reporting.py`)
- Exportar resultados en JSON además de CSV.
- Agregar un resumen estadístico (total procesadas, % de gatos, etc.).

### 🧪 Tests
- Añadir tests unitarios para `app/utils.py` y `app/reporting.py` con `pytest`.
- Agregar mocks del clasificador para probar el worker sin GPU.

### 🌐 Multiplataforma
- Verificar compatibilidad en macOS y Linux (la app usa `customtkinter`, es portable).
- Documentar pasos de instalación para esos sistemas operativos.

---

## 4. Convenciones

| Área | Convención |
|------|-----------|
| **Commits** | `feat:`, `fix:`, `refactor:`, `docs:`, `test:` |
| **Ramas** | `feature/`, `fix/`, `docs/` |
| **Estilo** | PEP 8, type hints donde sea posible |
| **Compatibilidad** | Python 3.10+ |

---

## 5. Reportar un bug

Abre un [Issue](https://github.com/Cracksmity/cat-image-detector/issues) con:
- Versión de Python usada.
- Sistema operativo y GPU (si aplica).
- Mensaje de error completo.
- Pasos para reproducirlo.
