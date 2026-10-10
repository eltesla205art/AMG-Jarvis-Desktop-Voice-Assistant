"""Offline wake-word detection with openWakeWord.

The detector listens to the microphone locally (16 kHz, 80 ms frames) and
only hands control to the online speech recognizer once it hears the wake
phrase, so nothing leaves the computer until you say "Hey Orion".

The bundled ``models/hey_orion.onnx`` was trained with the scripts in
``training/``. If openWakeWord isn't installed or the model is missing,
O.R.I.O.N. falls back to spotting the wake phrase in the online transcripts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from .config import PROJECT_ROOT, Config

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
FRAME = 1280  # 80 ms, the frame size openWakeWord is built around
MODEL_SUFFIXES = (".onnx", ".tflite")


class WakeWordUnavailable(Exception):
    pass


def resolve_model(spec: str) -> str:
    """A model file path (relative paths are from the project folder), or a
    built-in openWakeWord model name such as "hey_jarvis"."""
    if not spec.endswith(MODEL_SUFFIXES):
        return spec
    path = Path(spec).expanduser()
    return str(path if path.is_absolute() else PROJECT_ROOT / path)


def _ensure_resources(models: list[str]) -> None:
    """Download openWakeWord's shared feature models (and any built-in wake
    models named) the first time. Afterwards everything is local."""
    import openwakeword
    from openwakeword.utils import download_models

    features = Path(openwakeword.FEATURE_MODELS["melspectrogram"]["model_path"]).with_suffix(".onnx")
    builtin = [m for m in models if not m.endswith(MODEL_SUFFIXES)]
    if features.exists() and not builtin:
        return
    log.info("Downloading openWakeWord models (first run only)...")
    # A name that matches nothing downloads just the shared feature models.
    download_models(builtin or ["__features_only__"])


class WakeWordDetector:
    def __init__(self, models: list[str], threshold: float, open_stream: Callable):
        """``open_stream()`` returns a context manager whose ``.stream.read(n)``
        yields 16-bit mono PCM at 16 kHz (a SpeechRecognition Microphone)."""
        try:
            import numpy as np
            from openwakeword.model import Model
        except ImportError as exc:
            raise WakeWordUnavailable(f"openWakeWord is not installed ({exc})") from exc
        for model in models:
            if model.endswith(MODEL_SUFFIXES) and not Path(model).exists():
                raise WakeWordUnavailable(f"wake-word model not found: {model}")
        framework = "tflite" if all(m.endswith(".tflite") for m in models) else "onnx"
        try:
            _ensure_resources(models)
            self.model = Model(wakeword_models=list(models), inference_framework=framework)
        except Exception as exc:  # download failed, corrupt model, missing runtime...
            raise WakeWordUnavailable(str(exc)) from exc
        self.np = np
        self.threshold = threshold
        self.open_stream = open_stream
        self.name = ", ".join(Path(m).stem if m.endswith(MODEL_SUFFIXES) else m for m in models)

    def score(self, pcm: bytes) -> float:
        """Highest wake-word score (0..1) for one chunk of 16 kHz int16 audio."""
        scores = self.model.predict(self.np.frombuffer(pcm, dtype=self.np.int16))
        return max(scores.values(), default=0.0)

    def wait(self, interrupted: Callable[[], bool]) -> bool:
        """Block until the wake word is heard (True) or ``interrupted()`` (False)."""
        self.model.reset()  # forget audio from before this wait
        with self.open_stream() as source:
            while not interrupted():
                pcm = source.stream.read(FRAME)
                if self.score(pcm) >= self.threshold:
                    log.info("Wake word %r detected", self.name)
                    return True
        return False


def create_detector(config: Config, open_stream: Callable) -> WakeWordDetector | None:
    """The offline detector, or None to use transcript-based detection."""
    if not config.wake_word or config.wake_engine == "transcript":
        return None
    specs = [config.wake_model] if isinstance(config.wake_model, str) else config.wake_model
    try:
        detector = WakeWordDetector([resolve_model(s) for s in specs], config.wake_threshold, open_stream)
    except WakeWordUnavailable as exc:
        # "auto" quietly falls back; an explicit "openwakeword" deserves a warning.
        level = logging.WARNING if config.wake_engine == "openwakeword" else logging.INFO
        log.log(level, "Offline wake word unavailable (%s); listening for \"Hey Orion\" "
                       "in online transcripts instead.", exc)
        return None
    log.info("Offline wake word active: %s", detector.name)
    return detector
