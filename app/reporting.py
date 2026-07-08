from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, Optional


def write_report(destination_dir: str, rows: Iterable[Dict[str, Optional[str]]]) -> Path:
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "reporte_clasificacion.csv"

    with report_path.open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["Ruta_Archivo", "Resultado", "Confianza_Gato", "Detalle_Error"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return report_path

