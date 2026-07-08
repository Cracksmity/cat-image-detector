from __future__ import annotations

import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional

from PIL import Image

from app.classifier import CatZeroShotClassifier
from app.reporting import write_report
from app.utils import chunked, list_image_files

BATCH_SIZE = 32


@dataclass
class WorkerConfig:
    source_dir: str
    destination_dir: str
    threshold: float
    test_mode: bool


class ProcessingWorker(threading.Thread):
    def __init__(self, config: WorkerConfig, message_queue: Queue, stop_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.config = config
        self.message_queue = message_queue
        self.stop_event = stop_event
        self.report_rows: List[Dict[str, str]] = []
        self.error_count = 0
        self.processed_count = 0
        self.selected_count = 0
        self._start_time = 0.0

    def run(self) -> None:
        self._start_time = time.perf_counter()
        try:
            files = list_image_files(self.config.source_dir)
            if self.config.test_mode:
                files = files[:100]

            total = len(files)
            classifier = CatZeroShotClassifier()
            self.message_queue.put({"type": "started", "total": total, "device": classifier.device_name})

            for batch_paths in chunked(files, BATCH_SIZE):
                if self.stop_event.is_set():
                    break

                images, valid_paths = self._load_batch(batch_paths)
                if images:
                    try:
                        probs = classifier.predict_cat_probability(images)
                        self._handle_predictions(valid_paths, probs)
                    except Exception as exc:
                        for failed_path in valid_paths:
                            self.error_count += 1
                            self.processed_count += 1
                            self.report_rows.append(
                                {
                                    "Ruta_Archivo": str(failed_path),
                                    "Resultado": "Error",
                                    "Confianza_Gato": "",
                                    "Detalle_Error": f"Error de inferencia: {exc}",
                                }
                            )

                self._emit_progress(total)

            report_path = write_report(self.config.destination_dir, self.report_rows)
            elapsed = time.perf_counter() - self._start_time
            finished_type = "cancelled" if self.stop_event.is_set() else "completed"
            self.message_queue.put(
                {
                    "type": finished_type,
                    "processed": self.processed_count,
                    "selected": self.selected_count,
                    "errors": self.error_count,
                    "total": total,
                    "elapsed": elapsed,
                    "report_path": str(report_path),
                }
            )
        except Exception as exc:
            self.message_queue.put({"type": "fatal_error", "message": str(exc)})

    def _load_batch(self, paths: List[Path]) -> tuple[List[Image.Image], List[Path]]:
        images: List[Image.Image] = []
        valid_paths: List[Path] = []
        for path in paths:
            if self.stop_event.is_set():
                break
            try:
                with Image.open(path) as img:
                    images.append(img.convert("RGB").copy())
                valid_paths.append(path)
            except Exception as exc:
                self.error_count += 1
                self.processed_count += 1
                self.report_rows.append(
                    {
                        "Ruta_Archivo": str(path),
                        "Resultado": "Error",
                        "Confianza_Gato": "",
                        "Detalle_Error": str(exc),
                    }
                )
        return images, valid_paths

    def _handle_predictions(self, paths: List[Path], probabilities: List[float]) -> None:
        for path, prob in zip(paths, probabilities):
            if self.stop_event.is_set():
                break

            self.processed_count += 1
            confidence_pct = round(prob * 100.0, 2)
            if prob >= self.config.threshold:
                try:
                    self._copy_to_destination(path)
                    self.selected_count += 1
                    result = "Gato"
                    detail = ""
                except Exception as exc:
                    self.error_count += 1
                    result = "Error"
                    detail = f"Error al copiar: {exc}"
            else:
                result = "Descartado"
                detail = ""

            self.report_rows.append(
                {
                    "Ruta_Archivo": str(path),
                    "Resultado": result,
                    "Confianza_Gato": f"{confidence_pct:.2f}",
                    "Detalle_Error": detail,
                }
            )

    def _copy_to_destination(self, source_path: Path) -> None:
        source_root = Path(self.config.source_dir)
        destination_root = Path(self.config.destination_dir)
        relative_path = source_path.relative_to(source_root)
        destination_path = destination_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    def _emit_progress(self, total: int) -> None:
        elapsed = time.perf_counter() - self._start_time
        eta: Optional[float]
        if self.processed_count > 0 and total > self.processed_count:
            avg = elapsed / self.processed_count
            eta = avg * (total - self.processed_count)
        else:
            eta = 0.0

        self.message_queue.put(
            {
                "type": "progress",
                "processed": self.processed_count,
                "selected": self.selected_count,
                "errors": self.error_count,
                "total": total,
                "elapsed": elapsed,
                "eta": eta,
            }
        )
