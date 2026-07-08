from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import List, Sequence

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


@dataclass(frozen=True)
class RuntimeDevice:
    name: str
    torch_device: object


def _resolve_device() -> RuntimeDevice:
    if platform.system().lower() == "windows":
        try:
            import torch_directml  # type: ignore

            return RuntimeDevice(name="DirectML (AMD/Windows)", torch_device=torch_directml.device())
        except Exception:
            pass

    if torch.cuda.is_available():
        return RuntimeDevice(name="CUDA", torch_device=torch.device("cuda"))

    cpu_threads = max(1, (os.cpu_count() or 1) - 1)
    torch.set_num_threads(cpu_threads)
    return RuntimeDevice(name=f"CPU ({cpu_threads} hilos)", torch_device=torch.device("cpu"))


class CatZeroShotClassifier:
    def __init__(
        self,
        model_id: str = "openai/clip-vit-base-patch32",
        labels: Sequence[str] | None = None,
    ) -> None:
        self.labels = list(
            labels
            or (
                "una foto de un gato",
                "una foto de otra cosa, meme o captura de pantalla",
            )
        )
        self.runtime_device = _resolve_device()
        self.processor = CLIPProcessor.from_pretrained(model_id)
        # Evita torch.load de .bin en entornos con torch-directml (torch < 2.6).
        self.model = CLIPModel.from_pretrained(model_id, use_safetensors=True)
        self.model.to(self.runtime_device.torch_device)
        self.model.eval()

    @property
    def device_name(self) -> str:
        return self.runtime_device.name

    def predict_cat_probability(self, images: Sequence[Image.Image]) -> List[float]:
        if not images:
            return []

        try:
            return self._predict(images)
        except Exception:
            if str(self.runtime_device.torch_device) != "cpu":
                self.runtime_device = RuntimeDevice(name="CPU (fallback)", torch_device=torch.device("cpu"))
                self.model.to(self.runtime_device.torch_device)
                return self._predict(images)
            raise

    def _predict(self, images: Sequence[Image.Image]) -> List[float]:
        inputs = self.processor(text=self.labels, images=list(images), return_tensors="pt", padding=True)
        inputs = {k: v.to(self.runtime_device.torch_device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)
        return probs[:, 0].detach().cpu().tolist()
