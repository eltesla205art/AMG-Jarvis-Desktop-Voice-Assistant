"""Offline tests for command matching and the skills' pure logic.

Run with:  python -m unittest discover tests
No microphone, speakers, network or third-party packages needed.
"""

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orion.assistant import Assistant, greeting_for  # noqa: E402
from orion.config import Config  # noqa: E402
from orion.i18n import STRINGS  # noqa: E402
from orion.skills import find_skill, load_all  # noqa: E402
from orion.skills.clock import format_date, format_time  # noqa: E402
from orion.skills.music import pick_song  # noqa: E402
from orion.skills.web import resolve_site  # noqa: E402
from orion.skills.wiki import parse_summary  # noqa: E402
from orion.text import find_wake_word, normalize, strip_wake_word  # noqa: E402
from orion.voice import Heard  # noqa: E402

load_all()


def skill_for(text, prefer="en"):
    m = find_skill(normalize(strip_wake_word(text)), prefer)
    return (m.skill.name, m.lang) if m else None


class FakeUI:
    def __init__(self, typed=()):
        self.typed = list(typed)
        self.said = []

    def start(self): pass
    def status(self, text, state="idle"): pass
    def poll_text(self): return None
    closed = False

    def log(self, who, text):
        if who == "orion":
            self.said.append(text)

    def read_text(self, prompt=""):
        return self.typed.pop(0) if self.typed else None


def make_assistant(typed=(), **cfg):
    """A text-mode assistant that reads ``typed`` and stays silent."""
    tmp = tempfile.mkdtemp()
    config = Config(text_mode=True, notes_file=str(Path(tmp) / "notes.txt"), **cfg)
    ui = FakeUI(typed)
    assistant = Assistant(config, ui)
    assistant.speaker.speak = lambda text, lang="en": None
    return assistant, ui


class TextTests(unittest.TestCase):
    def test_normalize_keeps_length(self):
        raw = "Prends une note : appeler Sébastien à 15h"
        self.assertEqual(len(normalize(raw)), len(raw))
        self.assertIn("appeler sebastien a 15h", normalize(raw))

    def test_wake_word(self):
        self.assertEqual(strip_wake_word("Hey Orion, what time is it"), "what time is it")
        self.assertEqual(strip_wake_word("Dis Orion, joue de la musique"), "joue de la musique")
        self.assertEqual(strip_wake_word("um hey orien play music"), "play music")
        self.assertEqual(strip_wake_word("what time is it"), "what time is it")
        self.assertIsNotNone(find_wake_word("Orion, quelle heure est-il ?"))
        # The name in the middle of a sentence is not a wake word.
        self.assertIsNone(find_wake_word("tell me about the Orion nebula"))


class MatchingTests(unittest.TestCase):
    CASES = {
        "what time is it": ("time", "en"),
        "Quelle heure est-il ?": ("time", "fr"),
        "what is the date today": ("date", "en"),
        "On est quel jour ?": ("date", "fr"),
        "open YouTube": ("open_website", "en"),
        "ouvre Google": ("open_website", "fr"),
        "open wikipedia": ("open_website", "en"),
        "search google for cheap flights": ("google_search", "en"),
        "cherche des recettes de crêpes": ("google_search", "fr"),
        "play daft punk on youtube": ("youtube_search", "en"),
        "search wikipedia for black holes": ("wikipedia", "en"),
        "qui est Marie Curie": ("wikipedia", "fr"),
        "play music": ("music", "en"),
        "joue de la musique": ("music", "fr"),
        "tell me a joke": ("joke", "en"),
        "raconte-moi une blague": ("joke", "fr"),
        "take a screenshot": ("screenshot", "en"),
        "fais une capture d'écran": ("screenshot", "fr"),
        "take a note call mom": ("take_note", "en"),
        "prends une note acheter du pain": ("take_note", "fr"),
        "read my notes": ("read_notes", "en"),
        "shut down the computer": ("shutdown", "en"),
        "éteins l'ordinateur": ("shutdown", "fr"),
        "restart the computer": ("restart", "en"),
        "redémarre l'ordinateur": ("restart", "fr"),
        "speak french": ("speak_french", "en"),
        "parle anglais": ("speak_english", "fr"),
        "goodbye": ("goodbye", "en"),
        "au revoir": ("goodbye", "fr"),
    }

    def test_cases(self):
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                self.assertEqual(skill_for(text), expected)

    def test_gibberish(self):
        self.assertIsNone(skill_for("purple monkey dishwasher"))


class SkillLogicTests(unittest.TestCase):
    def test_time_and_date(self):
        moment = dt.datetime(2026, 7, 1, 15, 5)
        self.assertEqual(format_time(moment, "en"), "3:05 PM")
        self.assertEqual(format_time(moment, "fr"), "15 h 05")
        self.assertEqual(format_date(moment, "en"), "Wednesday, July 1, 2026")
        self.assertEqual(format_date(moment, "fr"), "mercredi 1er juillet 2026")

    def test_greeting_for(self):
        self.assertEqual([greeting_for(h) for h in (2, 7, 13, 19, 23)],
                         ["night", "morning", "afternoon", "evening", "night"])

    def test_resolve_site(self):
        self.assertEqual(resolve_site("youtube")[1], "https://www.youtube.com")
        self.assertEqual(resolve_site("github dot com")[1], "https://github.com")
        self.assertEqual(resolve_site("le site lemonde point fr")[1], "https://lemonde.fr")
        self.assertEqual(resolve_site("open ai")[1], "https://openai.com")
        self.assertIsNone(resolve_site("the"))

    def test_wiki_parse(self):
        data = {"query": {"pages": [{"title": "Orion", "extract":
                "Orion is a constellation. It is visible worldwide. Third sentence."}]}}
        self.assertEqual(parse_summary(data), "Orion is a constellation. It is visible worldwide.")
        self.assertIsNone(parse_summary({"batchcomplete": True}))

    def test_pick_song(self):
        root = Path("/music")
        songs = [root / "Daft Punk" / "Get Lucky.mp3", root / "Stromae" / "Alors on danse.mp3"]
        self.assertEqual(pick_song(songs, "daft", root), songs[0])
        self.assertEqual(pick_song(songs, "alors on danse", root), songs[1])
        self.assertIsNone(pick_song(songs, "beethoven", root))


class ReadmeExampleTests(unittest.TestCase):
    """The README examples reach the right skill with the right details."""

    def run_one(self, command, **cfg):
        opened = []
        import orion.skills.web as web
        import orion.skills.wiki as wiki
        web.open_url, saved_open = (lambda url: opened.append(url) or True), web.open_url
        wiki.fetch_summary, saved_fetch = (lambda q, lang: f"<{q}|{lang}>"), wiki.fetch_summary
        try:
            assistant, ui = make_assistant([command, "bye"], **cfg)
            assistant.run()
        finally:
            web.open_url, wiki.fetch_summary = saved_open, saved_fetch
        return opened, ui.said

    def test_examples(self):
        opened, _ = self.run_one("Cherche Stromae sur YouTube")
        self.assertEqual(opened, ["https://www.youtube.com/results?search_query=Stromae"])
        opened, _ = self.run_one("Open github dot com")
        self.assertEqual(opened, ["https://github.com"])
        _, said = self.run_one("Parle-moi de la tour Eiffel")
        self.assertIn("<tour Eiffel|fr>", said[2])
        _, said = self.run_one("Who is Marie Curie?")
        self.assertIn("<Marie Curie|en>", said[2])


class FakeListener:
    """Plays back utterances; each is {language: transcript}."""

    def __init__(self, assistant, utterances):
        self.assistant = assistant
        self.utterances = list(utterances)

    def capture(self):
        if not self.utterances:
            self.assistant.stop()
            return None
        return self.utterances.pop(0)

    def transcribe(self, audio, lang):
        text = audio.get(lang)
        return Heard(text, lang, 0.9) if text else None


def voice_session(utterances, **cfg):
    assistant, ui = make_assistant(**cfg)
    assistant._setup_listener = lambda: setattr(
        assistant, "listener", FakeListener(assistant, utterances))
    assistant.config.text_mode = False
    assistant.run()
    return assistant, ui


class WakeWordTests(unittest.TestCase):
    def test_ignores_speech_without_wake_word(self):
        _, ui = voice_session([
            {"en": "what time is it"},                      # not addressed: ignored
            {"en": "hey orion what time is it"},
        ])
        self.assertEqual(len(ui.said), 2)                   # greeting + time
        self.assertIn("Hey Orion", ui.said[0])
        self.assertTrue(ui.said[1].startswith("It's"))

    def test_bare_wake_word_then_command(self):
        _, ui = voice_session([
            {"en": "hey orion"},
            {"fr": "quelle heure est-il", "en": "kel er a teal"},   # no wake word needed now
        ])
        self.assertIn(ui.said[1], STRINGS["en"]["wake_ack"])
        self.assertTrue(ui.said[2].startswith("Il est"))

    def test_french_wake_phrase(self):
        _, ui = voice_session([{"fr": "dis Orion raconte-moi une blague", "en": "the sorry on"}])
        self.assertEqual(len(ui.said), 2)

    def test_answers_to_questions_need_no_wake_word(self):
        _, ui = voice_session([{"en": "hey orion shut down the computer"}, {"en": "no"}])
        self.assertIn("Okay, cancelled.", ui.said)

    def test_can_be_turned_off(self):
        _, ui = voice_session([{"en": "what time is it"}], wake_word=False)
        self.assertTrue(ui.said[1].startswith("It's"))
        self.assertNotIn("Hey Orion", ui.said[0])


class AssistantTests(unittest.TestCase):
    def test_session_switches_language_per_command(self):
        assistant, ui = make_assistant(["what time is it", "quelle heure est-il", "blah", "au revoir"])
        assistant.run()
        self.assertTrue(ui.said[1].startswith("It's"))
        self.assertTrue(ui.said[2].startswith("Il est"))
        # Unclear input is answered in the language of the previous command.
        self.assertIn(ui.said[3], STRINGS["fr"]["not_understood"])
        self.assertFalse(assistant.running)

    def test_note_is_saved_with_accents(self):
        assistant, ui = make_assistant(["prends une note appeler Sébastien", "bye"])
        assistant.run()
        notes = Path(assistant.config.notes_file).read_text(encoding="utf-8")
        self.assertIn("appeler Sébastien", notes)

    def test_power_action_needs_confirmation(self):
        assistant, ui = make_assistant(["shut down the computer", "no", "bye"])
        assistant.run()
        self.assertIn("Okay, cancelled.", ui.said)

    def test_voice_candidates_prefer_own_language_match(self):
        assistant, _ = make_assistant()
        heard, match = assistant.choose([
            Heard("can tell me a fair", "en", 0.4),        # French run through English
            Heard("quelle heure est-il", "fr", 0.9),
        ])
        self.assertEqual((heard.lang, match.skill.name), ("fr", "time"))


if __name__ == "__main__":
    unittest.main()
