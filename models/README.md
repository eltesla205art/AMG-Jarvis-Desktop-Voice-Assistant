# Wake-word models

**`hey_orion.onnx`** is a ready-trained openWakeWord model for "Hey Orion".
O.R.I.O.N. uses it automatically when the offline engine is installed:

```bash
pip install -r requirements-wakeword.txt
pip install --no-deps openwakeword==0.6.0
python orion.py --debug    # log shows: Offline wake word active: hey_orion
```

The first start downloads openWakeWord's shared audio-feature models (about
6 MB, once). After that, wake-word detection needs no internet connection.

## About the bundled model

- Trained on synthetic voices (904 English speakers) with the scripts in
  [`../training`](../training/README.md). In held-out tests it caught 98 % of
  "Hey Orion" from voices it never heard, with about 7 false wake-ups per
  hour on dense background audio.
- **Say "Hey" the English way ("hay").** The French pronunciation
  ("è-orion") sounds like everyday French and is deliberately ignored.
  « Dis Orion » isn't detected offline either; for that, use
  `"wake_engine": "transcript"`.
- It hasn't been tested with real voices in a real room yet. See Tuning below.
- Trained only on audio whose licenses allow commercial use (CC BY, CC0,
  CC BY-SA, public domain); sources and attributions are in
  [`../training/README.md`](../training/README.md#data).

## Tuning

- **Wakes up by mistake?** Raise `wake_threshold` in `orion_config.json`
  (for example `0.7` or `0.85`). In tests, 0.85 cut false wake-ups to about 5 per hour
  and still caught 97 % of English voices.
- **Misses you?** Lower it (for example `0.3`), or train your own model (below).
- **Try another phrase:** `"wake_model": "hey_jarvis"` uses openWakeWord's
  built-in "Hey Jarvis" model (downloaded on first use).
- **Several phrases:** list several models, e.g.
  `"wake_model": ["models/hey_orion.onnx", "models/dis_orion.onnx"]`.

## Train your own (about an hour, no coding)

openWakeWord's notebook trains on far more background audio than the bundled
model and runs in Google's free cloud. Its output can replace this file.

1. Open the official notebook:
   <https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing>
   (linked from the "Training New Models" section of
   <https://github.com/dscripka/openWakeWord>). Sign in with a Google account.
2. Set the target wake word/phrase field to `hey orion`. If the notebook
   lets you play a sample clip and "Orion" sounds wrong, respell it
   phonetically (for example `hey oh rye un`) and try again.
3. Choose **Runtime → Run all** and wait for it to finish (roughly 45–60 minutes).
4. Download the `.onnx` file it produces, rename it `hey_orion.onnx` and
   replace the one in this folder.
