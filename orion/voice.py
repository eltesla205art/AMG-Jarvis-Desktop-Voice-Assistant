"""Speech in and out.

* ``Speaker`` — text-to-speech. Uses the built-in ``say`` command on macOS
  (reliable, good French voices) and pyttsx3 elsewhere (SAPI5 on Windows,
  eSpeak NG on Linux). If no engine works, replies are only printed.
* ``Listener`` — microphone capture + Google Web Speech recognition through
  the SpeechRecognition package. Falls back to typed commands when no
  microphone (or PyAudio) is available.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass

from .i18n import LOCALES
from .platform_utils import IS_MAC

log = logging.getLogger(__name__)

PREFERRED_REGION = {"en": "US", "fr": "FR"}


# ----------------------------------------------------------------- speaking

class Speaker:
    def __init__(self, rate: int = 175):
        self.rate = rate
        self._lock = threading.Lock()
        self._engine = None          # pyttsx3 engine, created lazily
        self._voices: dict[str, str] = {}
        self._backend: str | None = None
        self._ready = False

    def _setup(self) -> None:
        """Pick a backend on first use (in the thread that will speak)."""
        self._ready = True
        if IS_MAC and shutil.which("say"):
            self._backend = "say"
            self._voices = self._mac_voices()
            return
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._voices = self._pyttsx3_voices(self._engine)
            self._backend = "pyttsx3"
        except Exception as exc:
            log.warning("Text-to-speech unavailable (%s). Replies will only be printed.", exc)

    @staticmethod
    def _mac_voices() -> dict[str, str]:
        voices: dict[str, str] = {}
        preferred: set[str] = set()
        try:
            out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return voices
        for line in out.splitlines():
            m = re.match(r"^(.+?)\s+([a-z]{2})[_-]([A-Z]{2})\s", line)
            if not m:
                continue
            name, lang, region = m.group(1).strip(), m.group(2), m.group(3)
            # Take the first voice per language, upgraded to a France/US one if found.
            if lang not in voices or (region == PREFERRED_REGION.get(lang) and lang not in preferred):
                voices[lang] = name
                if region == PREFERRED_REGION.get(lang):
                    preferred.add(lang)
        return voices

    @staticmethod
    def _pyttsx3_voices(engine) -> dict[str, str]:
        voices: dict[str, str] = {}
        candidates = [(v.id, f"{v.id} {v.name} {v.languages}".lower())
                      for v in engine.getProperty("voices") or []]
        for lang, words in (("fr", ("french", "français", "francais")), ("en", ("english",))):
            region = PREFERRED_REGION[lang].lower()
            tests = (
                lambda info: re.search(rf"(?<![a-z]){lang}[-_]{region}(?![a-z])", info),
                lambda info: any(w in info for w in words)
                or re.search(rf"(?<![a-z]){lang}(?![a-z])", info),
            )
            for test in tests:  # best match first: fr-FR / en-US, then any variant
                found = next((vid for vid, info in candidates if test(info)), None)
                if found:
                    voices[lang] = found
                    break
        return voices

    def speak(self, text: str, lang: str = "en") -> None:
        with self._lock:
            if not self._ready:
                self._setup()
            try:
                if self._backend == "say":
                    cmd = ["say", "-r", str(self.rate)]
                    if lang in self._voices:
                        cmd += ["-v", self._voices[lang]]
                    subprocess.run(cmd + [text], timeout=120)
                elif self._backend == "pyttsx3":
                    if lang in self._voices:
                        self._engine.setProperty("voice", self._voices[lang])
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception as exc:
                log.warning("Speech failed (%s); continuing silently.", exc)


# ---------------------------------------------------------------- listening

class SpeechServiceError(Exception):
    """The online recognizer could not be reached."""


class NoMicrophone(Exception):
    pass


@dataclass
class Heard:
    text: str
    lang: str | None      # None for typed text (language unknown)
    confidence: float


class Listener:
    def __init__(self, listen_timeout: float, phrase_time_limit: float):
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise NoMicrophone("SpeechRecognition is not installed") from exc
        self.sr = sr
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:  # calibrate once for background noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as exc:  # no PyAudio, no input device, permission denied...
            raise NoMicrophone(str(exc)) from exc

    def wake_stream(self):
        """A 16 kHz microphone stream in 80 ms chunks, for the offline wake word."""
        return self.sr.Microphone(sample_rate=16000, chunk_size=1280)

    def capture(self):
        """Record one phrase. Returns audio data, or None if nobody spoke."""
        try:
            with self.microphone as source:
                return self.recognizer.listen(source, timeout=self.listen_timeout,
                                              phrase_time_limit=self.phrase_time_limit)
        except self.sr.WaitTimeoutError:
            return None
        except OSError as exc:
            raise NoMicrophone(str(exc)) from exc

    def transcribe(self, audio, lang: str) -> Heard | None:
        """Turn audio into text in ``lang``. None if it wasn't understood."""
        try:
            result = self.recognizer.recognize_google(
                audio, language=LOCALES[lang], with_confidence=True)
        except self.sr.UnknownValueError:
            return None
        except self.sr.RequestError as exc:
            raise SpeechServiceError(str(exc)) from exc
        text, confidence = result if isinstance(result, tuple) else (result, 0.5)
        text = (text or "").strip()
        return Heard(text, lang, float(confidence or 0.0)) if text else None
