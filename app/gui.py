from __future__ import annotations

import threading
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.utils import format_seconds
from app.worker import ProcessingWorker, WorkerConfig


class CatDetectorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Detector de Gatos - Clasificación Zero-shot")
        self.geometry("860x620")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.message_queue: Queue = Queue()
        self.stop_event = threading.Event()
        self.worker: ProcessingWorker | None = None

        self.source_var = ctk.StringVar(value="")
        self.dest_var = ctk.StringVar(value="")
        self.threshold_var = ctk.DoubleVar(value=80.0)
        self.test_mode_var = ctk.BooleanVar(value=False)
        self.status_var = ctk.StringVar(value="Listo para iniciar.")
        self.device_var = ctk.StringVar(value="Dispositivo: --")
        self.progress_var = ctk.DoubleVar(value=0.0)
        self.counter_var = ctk.StringVar(value="Procesadas: 0 / 0")
        self.error_var = ctk.StringVar(value="Errores: 0")
        self.eta_var = ctk.StringVar(value="ETA: --:--")

        self._build_layout()
        self.after(150, self._poll_messages)

    def _build_layout(self) -> None:
        container = ctk.CTkFrame(self, corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title = ctk.CTkLabel(
            container,
            text="Filtro de imágenes de gato por IA",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(anchor="w", padx=16, pady=(16, 8))

        source_frame = ctk.CTkFrame(container)
        source_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(source_frame, text="Carpeta origen").pack(anchor="w", padx=10, pady=(8, 4))
        source_row = ctk.CTkFrame(source_frame, fg_color="transparent")
        source_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkEntry(source_row, textvariable=self.source_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(source_row, text="Seleccionar", width=120, command=self._select_source).pack(side="right")

        dest_frame = ctk.CTkFrame(container)
        dest_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(dest_frame, text="Carpeta destino").pack(anchor="w", padx=10, pady=(8, 4))
        dest_row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkEntry(dest_row, textvariable=self.dest_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(dest_row, text="Seleccionar", width=120, command=self._select_destination).pack(side="right")

        options_frame = ctk.CTkFrame(container)
        options_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(options_frame, text="Umbral de confianza (gato)").pack(anchor="w", padx=10, pady=(8, 2))
        slider_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        slider_row.pack(fill="x", padx=8, pady=(0, 4))
        ctk.CTkSlider(
            slider_row,
            from_=0,
            to=100,
            variable=self.threshold_var,
            command=self._on_threshold_change,
        ).pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.threshold_label = ctk.CTkLabel(slider_row, text="80%")
        self.threshold_label.pack(side="right")
        ctk.CTkCheckBox(options_frame, text="Modo de prueba (máximo 100 imágenes)", variable=self.test_mode_var).pack(
            anchor="w", padx=10, pady=(2, 8)
        )

        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=8)
        self.start_button = ctk.CTkButton(actions, text="Iniciar clasificación", command=self._start_processing)
        self.start_button.pack(side="left")
        self.cancel_button = ctk.CTkButton(actions, text="Cancelar", state="disabled", command=self._cancel_processing)
        self.cancel_button.pack(side="left", padx=8)

        progress = ctk.CTkFrame(container)
        progress.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(progress, textvariable=self.device_var).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkProgressBar(progress, variable=self.progress_var).pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(progress, textvariable=self.counter_var).pack(anchor="w", padx=10, pady=(2, 0))
        ctk.CTkLabel(progress, textvariable=self.error_var).pack(anchor="w", padx=10, pady=(0, 0))
        ctk.CTkLabel(progress, textvariable=self.eta_var).pack(anchor="w", padx=10, pady=(0, 8))

        status = ctk.CTkFrame(container)
        status.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        ctk.CTkLabel(status, text="Estado").pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(status, textvariable=self.status_var, justify="left", wraplength=760).pack(
            anchor="w", padx=10, pady=(0, 10)
        )

    def _on_threshold_change(self, value: float) -> None:
        self.threshold_label.configure(text=f"{int(round(value))}%")

    def _select_source(self) -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta origen")
        if folder:
            self.source_var.set(folder)

    def _select_destination(self) -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta destino")
        if folder:
            self.dest_var.set(folder)

    def _start_processing(self) -> None:
        source = self.source_var.get().strip()
        destination = self.dest_var.get().strip()
        if not source or not destination:
            messagebox.showwarning("Campos requeridos", "Debes seleccionar carpeta origen y destino.")
            return
        if not Path(source).exists():
            messagebox.showerror("Origen inválido", "La carpeta origen no existe.")
            return

        self.stop_event.clear()
        self.progress_var.set(0)
        self.counter_var.set("Procesadas: 0 / 0")
        self.error_var.set("Errores: 0")
        self.eta_var.set("ETA: --:--")
        self.status_var.set("Inicializando modelo y escaneo de imágenes...")
        self.device_var.set("Dispositivo: preparando...")

        config = WorkerConfig(
            source_dir=source,
            destination_dir=destination,
            threshold=self.threshold_var.get() / 100.0,
            test_mode=self.test_mode_var.get(),
        )
        self.worker = ProcessingWorker(config=config, message_queue=self.message_queue, stop_event=self.stop_event)
        self.worker.start()
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")

    def _cancel_processing(self) -> None:
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.status_var.set("Cancelación solicitada. Finalizando lote actual...")
            self.cancel_button.configure(state="disabled")

    def _poll_messages(self) -> None:
        try:
            while True:
                msg = self.message_queue.get_nowait()
                self._handle_message(msg)
        except Empty:
            pass
        finally:
            self.after(150, self._poll_messages)

    def _handle_message(self, msg: dict) -> None:
        msg_type = msg.get("type")
        if msg_type == "started":
            total = msg.get("total", 0)
            device = msg.get("device", "--")
            self.device_var.set(f"Dispositivo: {device}")
            self.counter_var.set(f"Procesadas: 0 / {total}")
            self.status_var.set("Procesando imágenes...")
            return

        if msg_type == "progress":
            processed = int(msg.get("processed", 0))
            total = max(1, int(msg.get("total", 0)))
            errors = int(msg.get("errors", 0))
            eta = float(msg.get("eta", 0.0))
            self.progress_var.set(min(1.0, processed / total))
            self.counter_var.set(f"Procesadas: {processed} / {total}")
            self.error_var.set(f"Errores: {errors}")
            self.eta_var.set(f"ETA: {format_seconds(eta)}")
            return

        if msg_type in {"completed", "cancelled"}:
            processed = int(msg.get("processed", 0))
            total = int(msg.get("total", 0))
            selected = int(msg.get("selected", 0))
            errors = int(msg.get("errors", 0))
            elapsed = float(msg.get("elapsed", 0.0))
            report_path = msg.get("report_path", "")
            self.progress_var.set(1.0 if total and processed >= total else self.progress_var.get())
            self.counter_var.set(f"Procesadas: {processed} / {total}")
            self.error_var.set(f"Errores: {errors}")
            self.eta_var.set("ETA: 00:00")
            if msg_type == "completed":
                self.status_var.set(
                    "Proceso completado.\n"
                    f"Imágenes seleccionadas: {selected}\n"
                    f"Tiempo total: {format_seconds(elapsed)}\n"
                    f"Reporte: {report_path}"
                )
            else:
                self.status_var.set(
                    "Proceso cancelado por el usuario.\n"
                    f"Imágenes seleccionadas: {selected}\n"
                    f"Tiempo transcurrido: {format_seconds(elapsed)}\n"
                    f"Reporte parcial: {report_path}"
                )
            self.start_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            return

        if msg_type == "fatal_error":
            self.status_var.set(f"Error crítico: {msg.get('message', 'desconocido')}")
            self.start_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            return


def run_app() -> None:
    app = CatDetectorApp()
    app.mainloop()

