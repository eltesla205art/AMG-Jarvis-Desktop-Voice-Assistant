# Wake-word models

Put your trained openWakeWord model here as **`hey_orion.onnx`**. O.R.I.O.N.
picks it up automatically on the next start and then listens for "Hey Orion"
fully offline. Without it, O.R.I.O.N. still works: it spots "Hey Orion" in the
online transcripts instead.

## Train "Hey Orion" (about an hour, no coding)

openWakeWord's training notebook generates thousands of synthetic voice clips
of your phrase and trains a small model on them, all in Google's free cloud.

1. Open the official notebook:
   <https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing>
   (linked from the "Training New Models" section of
   <https://github.com/dscripka/openWakeWord>). Sign in with a Google account.
2. Set the target wake word/phrase field to `hey orion`. If the notebook
   lets you play a sample clip and "Orion" sounds wrong, respell it
   phonetically (for example `hey oh rye un`) and try again.
3. Choose **Runtime → Run all** and wait for it to finish (roughly 45–60 minutes).
4. Download the `.onnx` file it produces, rename it `hey_orion.onnx` and put
   it in this folder.
5. Install the offline engine if you haven't yet (from the project folder):

   ```bash
   pip install -r requirements-wakeword.txt
   pip install --no-deps openwakeword==0.6.0
   ```

6. Run `python orion.py --debug`. The log line
   `Offline wake word active: hey_orion` confirms it is working.

The first start downloads openWakeWord's shared audio-feature models (about
6 MB, once). After that, wake-word detection needs no internet connection.

## Tuning

- **Wakes up by mistake?** Raise `wake_threshold` in `orion_config.json`
  (for example `0.6` or `0.7`).
- **Misses you?** Lower it (for example `0.4`), or retrain with more steps.
- **French wake phrase too:** train a second model for `dis orion`, save it as
  `dis_orion.onnx`, and list both models:
  `"wake_model": ["models/hey_orion.onnx", "models/dis_orion.onnx"]`.
  The notebook's synthetic voices are English, so a French phrase may be less
  accurate.
- **Try it before training:** `"wake_model": "hey_jarvis"` uses openWakeWord's
  built-in "Hey Jarvis" model (downloaded on first use).
