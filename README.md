# O.R.I.O.N. — AI Voice Assistant

<p align="center">
  <img src="Images/orion_cover.jpg" alt="O.R.I.O.N. AI Voice Assistant — Powered by AMG" width="520">
</p>

<p align="center"><b>A bilingual (English 🇬🇧 / French 🇫🇷) desktop voice assistant for Windows, macOS and Linux.</b><br>
Powered by AMG · Ascension Media Group</p>

O.R.I.O.N. listens on your microphone, works out whether you spoke English or French, and answers in the same language. Run it from one script, `orion.py`. It opens a small window built around the O.R.I.O.N. artwork, and you can also run it in the terminal.

<p align="center"><img src="Images/orion_hud.png" alt="O.R.I.O.N. window" width="300"></p>

## Features

| | English example | Exemple en français |
|---|---|---|
| Greets you by time of day | *(at start-up)* | *(au démarrage)* |
| Time & date | "What time is it?" · "What's the date?" | « Quelle heure est-il ? » · « On est quel jour ? » |
| Open any website | "Open YouTube" · "Open github dot com" | « Ouvre Google » · « Ouvre lemonde point fr » |
| Google / YouTube search | "Search for cheap flights" · "Play Daft Punk on YouTube" | « Cherche des recettes de crêpes » · « Cherche Stromae sur YouTube » |
| Wikipedia summary (read aloud) | "Who is Marie Curie?" · "Search Wikipedia for black holes" | « Qui est Victor Hugo ? » · « Parle-moi de la tour Eiffel » |
| Local music | "Play music" · "Play song get lucky" | « Joue de la musique » · « Mets la chanson alors on danse » |
| Jokes | "Tell me a joke" | « Raconte-moi une blague » |
| Screenshots | "Take a screenshot" | « Fais une capture d'écran » |
| Quick notes | "Take a note call the bank tomorrow" · "Read my notes" | « Prends une note acheter du pain » · « Lis mes notes » |
| Shut down / restart *(asks for confirmation first)* | "Shut down the computer" · "Restart" | « Éteins l'ordinateur » · « Redémarre » |
| Language | "Speak French" · "Bilingual mode" | « Parle anglais » · « Mode bilingue » |
| Help / stop | "Help" · "Goodbye" | « Aide » · « Au revoir » |

### Wake word

O.R.I.O.N. only reacts to speech that starts with **"Hey Orion"** (in French, **« Dis Orion »**). Everything else is ignored, so it won't answer conversations around it.
- Say it together with the command: *"Hey Orion, what time is it?"*
- Or say *"Hey Orion"* on its own. It answers *"Yes?"* and takes the next sentence as a command.
- *"Ok Orion"*, *"Salut Orion"* and *"Orion, …"* at the start of a sentence also work.
- Answers to its own questions (*"Are you sure?"*, *"What should I write down?"*) don't need the wake word, and neither do typed commands.

To turn it off, use `python orion.py --no-wake-word` or set `"wake_word": false` in the config.

### Offline wake word (optional)

By default O.R.I.O.N. finds "Hey Orion" in Google's transcripts, so everything the microphone hears is sent to Google first. For privacy, O.R.I.O.N. can detect the wake word **on your computer** with [openWakeWord](https://github.com/dscripka/openWakeWord). Then nothing leaves your computer until you say "Hey Orion"; only the command after it goes to Google.

A trained "Hey Orion" model is included (`models/hey_orion.onnx`), so you only need to install the engine:

```bash
pip install -r requirements-wakeword.txt
pip install --no-deps openwakeword==0.6.0
```

Then run `python orion.py`. It switches to offline detection automatically. Say *"Hey Orion"*, wait for *"How can I help?"*, then give your command.

- **Pronunciation:** say "Hey" the English way ("hay"). The French pronunciation ("è-orion") sounds too much like everyday French, so the offline model ignores it, and it doesn't detect « Dis Orion ». French speakers who prefer those can set `"wake_engine": "transcript"`.
- **Without the engine:** if openWakeWord isn't installed, O.R.I.O.N. keeps using the transcript-based detection, so nothing breaks.
- **More detail:** see [`models/README.md`](models/README.md) for accuracy, tuning and training your own model, and [`training/`](training/README.md) for how the bundled model was made (including a licensing note on its training data).

### When something goes wrong
- **Missed or unclear speech:** O.R.I.O.N. ignores silence and anything said without the wake word. If you address it and it doesn't understand, it says so and suggests "help". It never crashes on bad input.
- **Missing details:** say "Open…" or "Take a note" on its own and it asks what you meant.
- **No microphone or PyAudio:** it tells you and switches to typed commands.
- **No internet:** speech recognition and Wikipedia need a connection. O.R.I.O.N. tells you once and keeps running.
- **No text-to-speech engine:** replies are still shown on screen.
- **A command fails:** the error is logged, O.R.I.O.N. tells you, and it keeps listening.

## Quick start

**Requires Python 3.9+.**

### 1. System packages (only for the microphone and the voice)

| OS | Command |
|---|---|
| **Windows** | Nothing extra. PyAudio installs from a wheel. |
| **macOS** | `brew install portaudio` |
| **Ubuntu / Debian** | `sudo apt install python3-tk python3-dev portaudio19-dev espeak-ng alsa-utils xdg-utils` |
| **Fedora** | `sudo dnf install python3-tkinter python3-devel portaudio-devel espeak-ng alsa-utils xdg-utils` |

For French speech, install a French voice:
- **Windows:** Settings → Time & Language → Speech → *Add voices* → Français (France).
- **macOS:** System Settings → Accessibility → Spoken Content → System voice → *Manage Voices* → French (e.g. Thomas or Amélie).
- **Linux:** `espeak-ng` already includes French.

### 2. Install and run

```bash
git clone https://github.com/eltesla205art/AMG-Jarvis-Desktop-Voice-Assistant.git
cd AMG-Jarvis-Desktop-Voice-Assistant
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python orion.py
```

On macOS, allow microphone access for your terminal the first time (System Settings → Privacy & Security → Microphone).

### Options

```bash
python orion.py              # window + voice (type commands in the box too)
python orion.py --console    # terminal only
python orion.py --text       # type instead of speaking (no microphone needed)
python orion.py --lang fr    # French only  (en = English only, auto = both, default)
python orion.py --no-wake-word   # react to all speech, not only after "Hey Orion"
python orion.py --debug      # verbose logs
```

## Configuration

Copy `orion_config.example.json` to `orion_config.json` and change only the keys you need:

| Key | Default | Meaning |
|---|---|---|
| `user_name` | `""` | Your name, used in greetings |
| `language` | `"auto"` | `auto` (English + French), `en` or `fr` |
| `default_language` | `"en"` | Language used for the greeting |
| `music_dir` | your Music folder | Folder searched for `.mp3 .flac .wav .ogg .m4a…` files (subfolders included) |
| `notes_file` | `~/ORION/notes.txt` | Where notes are saved |
| `screenshot_dir` | `~/Pictures/ORION` | Where screenshots are saved |
| `confirm_power_actions` | `true` | Ask "are you sure?" before shutting down or restarting |
| `listen_timeout` / `phrase_time_limit` | `6` / `12` | Seconds to wait for speech / maximum command length |
| `speech_rate` | `175` | Speaking speed |
| `wake_word` | `true` | Only react to speech that starts with "Hey Orion" / « Dis Orion » |
| `wake_engine` | `"auto"` | `auto` (offline when the model exists), `openwakeword` or `transcript` |
| `wake_model` | `"models/hey_orion.onnx"` | Offline model file(s), or a built-in name such as `"hey_jarvis"` |
| `wake_threshold` | `0.5` | Offline detection sensitivity: higher means fewer false wake-ups |
| `text_mode` | `false` | Always use typed commands |

## How it works

```
orion.py                 ← the one script you run
orion/
  assistant.py           ← listen → understand → act loop, language detection
  voice.py               ← Speaker (macOS `say` / pyttsx3) and Listener (SpeechRecognition)
  wakeword.py            ← offline "Hey Orion" detection (openWakeWord)
  i18n.py                ← every sentence, in English and French
  text.py                ← accent/punctuation-insensitive phrase matching
  config.py              ← settings + orion_config.json
  platform_utils.py      ← open files/URLs, shut down/restart, per OS
  gui.py / ui.py         ← window and terminal front-ends
  skills/                ← one file per feature (clock, web, wiki, music, jokes, screenshot, notes, system, general)
models/hey_orion.onnx    ← offline "Hey Orion" model (see models/README.md)
training/                ← scripts that trained it
tests/test_orion.py      ← offline tests: python -m unittest discover tests
```

**Language detection.** Every phrase you say is first transcribed in the current language. If that transcript doesn't clearly match a command, the same audio is also transcribed in the other language. O.R.I.O.N. keeps the transcript that matches a command *in its own language*. French run through the English recognizer rarely turns into a valid English command, so this choice is reliable. Replies follow the language you last used.

**Speech engines.** Recognition uses the free Google Web Speech API through the `SpeechRecognition` package, so it needs internet access. Speech output works offline: SAPI5 on Windows, `say` on macOS and eSpeak NG on Linux.

**Wake word detection** runs offline with openWakeWord and the bundled `models/hey_orion.onnx` when openWakeWord is installed (`wakeword.py`). Otherwise it reads the online transcripts, which needs no extra software but means phrases without the wake word are still sent to Google before O.R.I.O.N. ignores them.

## Adding your own command

Create a file in `orion/skills/`. It is picked up automatically:

```python
# orion/skills/weather.py
from . import skill

@skill("weather", en=["weather", "forecast"], fr=["météo", "quel temps"])
def weather(ctx, req):
    city = req.rest or "your city"     # words spoken after the trigger
    ctx.say_text(f"Looking up the weather in {city}..." if ctx.lang == "en"
                 else f"Je regarde la météo à {city}...")
```

- `ctx.say(key, **values)` speaks a sentence from `i18n.py` in the current language. `ctx.say_text(text)` speaks any text.
- `ctx.ask(key)` asks a question and returns the answer. `ctx.confirm(key)` returns True or False.
- `ctx.lang`, `ctx.config`, `ctx.stop()`.
- `req.raw`, `req.rest` (text after the trigger) and `req.before` (text before it).

When two trigger phrases match, the longer one wins. Add the trigger in both languages and put new sentences in both blocks of `i18n.py`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not find PyAudio` / no microphone | Install the system packages above, then `pip install PyAudio`. Or use `--text`. |
| It speaks English with an English voice when you speak French | Install a French system voice (see above). |
| Linux: no sound from the voice | Install `espeak-ng` and `alsa-utils`. |
| Linux Wayland: screenshot fails | Install `gnome-screenshot` or `grim`, which Pillow uses as a fallback. |
| Linux: shutdown or restart refused | Your session must be allowed to run `systemctl poweroff` / `reboot` (the default on desktop distros). |
| No window appears | Install Tk (`python3-tk`), or run with `--console`. |
| Offline wake word not used | Run with `--debug`: the log says why (model file missing, openWakeWord not installed, first-run download failed). |
| `tflite-runtime` fails to install | Install openWakeWord with `--no-deps` as shown above; O.R.I.O.N. uses onnxruntime. |

## Credits & license

O.R.I.O.N. is built by AMG · Ascension Media Group on top of the open-source [Jarvis Desktop Voice Assistant](https://github.com/kishanrajput23/Jarvis-Desktop-Voice-Assistant) by Kishan Kumar Rai. The original script is still in `Jarvis/` for reference; it needs `pip install pyautogui wikipedia pyttsx3 SpeechRecognition pyjokes`.

Released under the [MIT License](LICENSE).
