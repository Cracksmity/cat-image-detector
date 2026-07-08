# Contexto del proyecto (handoff)

## Objetivo
Filtrar un dataset local grande de imágenes (p. ej. WhatsApp) para extraer fotos de gato con clasificación zero-shot, manteniendo la UI fluida y generando trazabilidad en CSV.

## Estado actual
- App funcional con GUI (`customtkinter`).
- Clasificación por lotes (`BATCH_SIZE = 32` en `app/worker.py`).
- Worker en hilo separado para evitar congelar interfaz.
- Fallback de dispositivo:
  1) intenta DirectML en Windows (`torch-directml`)
  2) CUDA si existe
  3) CPU con ajuste de hilos.
- Reporte final automático: `reporte_clasificacion.csv`.
- Fix aplicado en carga de modelo: uso forzado de `safetensors` para compatibilidad con `torch-directml`.

## Flujo técnico
1. `main.py` inicia `run_app()`.
2. `app/gui.py` recoge configuración y lanza `ProcessingWorker`.
3. `app/worker.py`:
   - lista imágenes recursivas con `list_image_files()`.
   - limita a 100 si `test_mode=True`.
   - abre imágenes en bloques, tolerando errores de lectura.
   - llama al clasificador y decide copiar/descartar según umbral.
   - emite eventos de progreso (`Queue`) para la GUI.
   - escribe CSV final al terminar o cancelar.
4. `app/classifier.py` usa CLIP + processor para probabilidad de clase "gato".

## Decisiones de diseño importantes
- Etiquetas del clasificador (en español):
  - `una foto de un gato`
  - `una foto de otra cosa, meme o captura de pantalla`
- Se preserva estructura relativa de carpetas al copiar al destino.
- Errores no detienen el proceso; se registran en CSV.
- En `app/classifier.py`, CLIP se carga con `use_safetensors=True` para evitar fallos de `torch.load` en ciertos entornos DirectML.

## Dependencias
Ver `requirements.txt`:
- `customtkinter`, `Pillow`, `transformers`, `torch`, `safetensors`
- opcional: `torch-directml`

## Puntos de ajuste rápido
- Modelo: `model_id` en `CatZeroShotClassifier` (`app/classifier.py`).
- Umbral default GUI: `threshold_var` inicial en `app/gui.py`.
- Tamaño de lote: `BATCH_SIZE` en `app/worker.py`.
- Extensiones soportadas: `SUPPORTED_EXTENSIONS` en `app/utils.py`.

## Riesgos / notas para siguiente agente
- Primera ejecución descarga pesos del modelo (requiere internet).
- Rendimiento depende de I/O de disco y decodificación de imagen.
- Si se desea más precisión, evaluar modelos más grandes o prompt labels alternativos.
- Si se desea más velocidad en CPU, considerar resize previo o lotes más pequeños/grandes según RAM/VRAM.
- Si se cambia esta línea y vuelve `torch.load` de `.bin`, puede reaparecer el bloqueo/error de compatibilidad en `.venv311` + `torch-directml`.

## Checklist de continuidad
1. Crear repo Git y subir (`README.md` incluye comandos).
2. Probar con Modo de prueba activado.
3. Ejecutar lote completo y revisar métricas del CSV.
4. Ajustar umbral según precisión/recall observados.
