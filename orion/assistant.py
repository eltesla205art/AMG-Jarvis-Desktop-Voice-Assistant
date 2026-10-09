"""The main listen → understand → act loop.

The Assistant is also the ``ctx`` object handed to every skill, so skills
talk to the user only through ``say``, ``ask`` and ``confirm``.
"""

from __future__ import annotations

import datetime as dt
import logging

from . import SPOKEN_NAME
from .config import Config
from .i18n import t
from .skills import Match, Request, find_skill, load_all
from .text import find_wake_word, has_any_word, normalize, strip_wake_word
from .voice import Heard, Listener, NoMicrophone, Speaker, SpeechServiceError
from .wakeword import WakeWordDetector, create_detector

log = logging.getLogger(__name__)

YES = {"yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "do it", "affirmative", "go ahead",
       "oui", "ouais", "d accord", "vas y", "confirme", "bien sur", "allez y"}
NO = {"no", "nope", "cancel", "stop", "don t", "non", "annule", "pas", "surtout pas"}

# Accept a first transcription without asking the other language when this sure.
CONFIDENT = 0.75
# Speak about a failing speech service at most once per this many failures.
SERVICE_ERROR_EVERY = 5


def greeting_for(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 22:
        return "evening"
    return "night"


class Assistant:
    def __init__(self, config: Config, ui):
        self.config = config
        self.ui = ui
        self.lang = config.default_language
        self.running = False
        self.speaker = Speaker(config.speech_rate)
        self.listener: Listener | None = None
        self._service_errors = 0
        self.wake_detector: WakeWordDetector | None = None
        self._typed: str | None = None  # typed while waiting for the wake word
        load_all()

    # ------------------------------------------------------- skill-facing API

    @property
    def user_suffix(self) -> str:
        """", Andre" when a user name is configured, else ""."""
        return f", {self.config.user_name}" if self.config.user_name else ""

    def say(self, key: str, **kwargs: object) -> None:
        self.say_text(t(key, self.lang, **kwargs))

    def say_text(self, text: str) -> None:
        self.ui.log("orion", text)
        self.ui.status(t("speaking", self.lang), "speaking")
        self.speaker.speak(text, self.lang)

    def ask(self, key: str, attempts: int = 2) -> str | None:
        """Ask a question and return the raw answer, or None."""
        self.say(key)
        for attempt in range(attempts):
            heard = self._next_input(follow_up=True)
            if heard:
                self.ui.log("user", heard[0].text)
                return strip_wake_word(heard[0].text).strip() or None
            if attempt + 1 < attempts and self.running and self.listener:
                self.say("repeat")
        return None

    def confirm(self, key: str) -> bool:
        answer = self.ask(key)
        if not answer:
            return False
        return has_any_word(answer, YES) and not has_any_word(answer, NO)

    def set_language(self, lang: str) -> None:
        """Pin "en"/"fr" (recognition and replies), or "auto" for both."""
        self.config.language = lang
        if lang != "auto":
            self.lang = lang

    def stop(self) -> None:
        self.running = False

    # ------------------------------------------------------------- main loop

    def run(self) -> None:
        self.running = True
        self.ui.start()
        self._setup_listener()
        self.greet()
        while self.running and not self.ui.closed:
            try:
                heard = self._next_input()
                if heard is None and self.listener is None:
                    break  # keyboard input closed (Ctrl+D)
                if heard:
                    self.handle(heard)
            except KeyboardInterrupt:
                raise
            except Exception:  # never let one bad command kill the assistant
                log.exception("Unexpected error")
                self.say("skill_error")
        self.running = False

    def greet(self) -> None:
        hint = f" {t('wake_hint', self.lang)}" if self.needs_wake_word else ""
        self.say_text(f"{t(greeting_for(dt.datetime.now().hour), self.lang)}{self.user_suffix}! "
                      f"{t('intro', self.lang, name=SPOKEN_NAME)}{hint}")

    def _setup_listener(self) -> None:
        if self.config.text_mode:
            return
        try:
            self.listener = Listener(self.config.listen_timeout, self.config.phrase_time_limit)
            self.wake_detector = create_detector(self.config, self.listener.wake_stream)
        except NoMicrophone as exc:
            log.warning("Voice input unavailable: %s", exc)
            self.ui.log("error", str(exc))
            self.say("no_mic")

    def _languages(self) -> list[str]:
        if self.config.language != "auto":
            return [self.config.language]
        other = "fr" if self.lang == "en" else "en"
        return [self.lang, other]

    @property
    def needs_wake_word(self) -> bool:
        return self.config.wake_word and self.listener is not None

    def _next_input(self, follow_up: bool = False, awake: bool = False) -> list[Heard] | None:
        """Get the next command as candidate transcriptions (best first).

        Speech is ignored unless it contains the wake word, except for answers
        to a question (``follow_up``) and right after a bare "Hey Orion"
        (``awake``). Typed commands never need it.

        Returns [] when nothing usable was heard, None when input is closed.
        """
        addressed = follow_up or awake or not self.needs_wake_word
        typed, self._typed = self._typed or self.ui.poll_text(), None
        if typed:
            return [Heard(typed, None, 1.0)]
        if self.listener is None:
            self.ui.status(t("idle", self.lang), "idle")
            text = self.ui.read_text()
            return None if text is None else ([Heard(text, None, 1.0)] if text else [])

        if not addressed and self.wake_detector:
            if not self._wait_for_wake_word():
                return []  # typed command (picked up next turn), or shutting down
            self.say("wake_ack")
            addressed = True

        self.ui.status(t("listening" if addressed else "waiting_wake", self.lang), "listening")
        try:
            audio = self.listener.capture()
        except NoMicrophone as exc:  # e.g. the microphone was unplugged
            log.warning("Microphone lost: %s", exc)
            self.listener = None
            self.say("no_mic")
            return []
        if audio is None:
            return []
        self.ui.status(t("thinking", self.lang), "thinking")
        candidates: list[Heard] = []
        try:
            for lang in self._languages():
                heard = self.listener.transcribe(audio, lang)
                if not heard:
                    continue
                candidates.append(heard)
                # Follow-up answers ("yes", a note) are in the current language;
                # commands only need a second opinion when the first is unsure.
                if follow_up or (heard.confidence >= CONFIDENT and self._match(heard)
                                 and (addressed or find_wake_word(heard.text) is not None)):
                    break
            self._service_errors = 0
        except SpeechServiceError as exc:
            log.warning("Speech service error: %s", exc)
            if self._service_errors % SERVICE_ERROR_EVERY == 0:
                self.say("service_down")
            self._service_errors += 1
        if not addressed:
            # Not talking to O.R.I.O.N.: drop it silently.
            candidates = [h for h in candidates if find_wake_word(h.text) is not None]
        return candidates

    def _wait_for_wake_word(self) -> bool:
        """Listen offline until the wake word. False if interrupted by typing or exit."""
        def interrupted() -> bool:
            self._typed = self._typed or self.ui.poll_text()
            return bool(self._typed) or not self.running or self.ui.closed

        self.ui.status(t("waiting_wake", self.lang), "listening")
        try:
            return self.wake_detector.wait(interrupted)
        except Exception as exc:  # microphone or model failure: keep going without it
            log.warning("Offline wake word stopped (%s); using online detection.", exc)
            self.wake_detector = None
            return False

    def _match(self, heard: Heard) -> Match | None:
        text = strip_wake_word(heard.text)
        return find_skill(normalize(text), prefer=heard.lang or self.lang)

    def choose(self, candidates: list[Heard]) -> tuple[Heard, Match | None]:
        """Pick the transcription that best looks like a command.

        A transcript matching a command *in its own language* wins (French
        speech run through the English recognizer rarely produces English
        commands), then any match, then recognizer confidence.
        """
        def rank(h: Heard):
            m = self._match(h)
            same_lang = bool(m and (h.lang is None or m.lang == h.lang))
            return (m is not None, same_lang, h.confidence), m

        ranked = [(rank(h), h) for h in candidates]
        (_, match), heard = max(ranked, key=lambda item: item[0][0])
        return heard, match

    def handle(self, candidates: list[Heard]) -> None:
        heard, match = self.choose(candidates)
        text = strip_wake_word(heard.text)
        self.ui.log("user", heard.text)
        if not text:  # just "Hey Orion": acknowledge, then take one command
            self.say("wake_ack")
            follow = self._next_input(awake=True)
            if follow:
                self.handle(follow)
            return
        if self.config.language == "auto":
            self.lang = heard.lang or (match.lang if match else self.lang)
        if match is None:
            self.say("not_understood")
            return
        log.info("Skill %s (%s)", match.skill.name, match.lang)
        try:
            match.skill.handler(self, Request(raw=text, lang=self.lang, match=match.match))
        except Exception:
            log.exception("Skill %s failed", match.skill.name)
            self.say("skill_error")
