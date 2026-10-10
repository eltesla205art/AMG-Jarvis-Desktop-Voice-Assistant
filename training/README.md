# How `models/hey_orion.onnx` was trained

These scripts produced the bundled "Hey Orion" wake-word model. They follow
openWakeWord's own recipe: synthetic voices say the phrase, a small network
learns it on top of openWakeWord's frozen audio features, and hours of other
audio teach it what to ignore. Everything runs on a CPU (about 2 hours on 4 cores).

## Results (held-out audio, streaming exactly like O.R.I.O.N., threshold 0.5)

| Test | Result |
|---|---|
| "Hey Orion" from 104 English voices never used in training | **96 %** detected |
| Same phrase, robotic espeak-ng voices (a different TTS engine) | 43 % detected |
| "Hey Orion" said the French way ("è-orion") by French voices | 1 % (by design, see below) |
| False wake-ups on 137 min of other audio: dense EN/FR speech, sound-alikes like "hey Ryan", "hey Marion", real environmental sounds, real recorded speech, music | **5.7 per hour** overall; 3 in 76 min of continuous speech |

These numbers come from synthetic and dataset audio, not from real people in
a real room. Expect some difference with your own voice and microphone; tune
`wake_threshold` in `orion_config.json` (higher = fewer false wake-ups).

**Why the French pronunciation is excluded:** said the French way, "Hey Orion"
sounds almost exactly like everyday French ("et aurions", "et horizon"). A
version that accepted it woke up about 140 times an hour during French
conversation. The shipped model wants an English-style "Hey" (like "hay").
French speakers who prefer « Dis Orion » can keep `"wake_engine": "transcript"`.

## Data

| Role | Source | License |
|---|---|---|
| Wake phrase (6,600 clips) | [Piper sample generator](https://github.com/rhasspy/piper-sample-generator) LibriTTS-R voices (904 speakers, mixed) | MIT generator; LibriTTS-R CC BY 4.0 |
| Speech to ignore (EN/FR sentences, sound-alikes) | Same generator + its French MLS model; random common words from [wordfreq](https://github.com/rspeer/wordfreq) | as above |
| Real sounds to ignore / background noise | [ESC-50](https://github.com/karolpiczak/ESC-50) | **CC BY-NC 3.0 (non-commercial)** |
| Real speech to ignore | [Free Spoken Digit Dataset](https://github.com/Jakobovski/free-spoken-digit-dataset) | CC BY-SA 4.0 |
| Music to ignore | [librosa example data](https://github.com/librosa/data) | mixed CC BY / **CC BY-NC** |
| Audio features | openWakeWord melspectrogram + embedding models | Apache 2.0 |

ESC-50 and some librosa tracks are licensed for non-commercial use. Whether
that restriction carries over to a model trained on them is legally unsettled.
If you need a model that avoids the question, retrain without them (drop
`esc` and `music` in `prep.py` / `stream_feats.py`) or use openWakeWord's
Colab notebook (see `models/README.md`).

## Reproduce

Requirements: Python 3.10+, `espeak-ng` on the system, about 15 GB of disk space.

```bash
python -m venv venv && . venv/bin/activate
pip install torch piper-sample-generator onnxruntime onnx scipy scikit-learn tqdm requests numpy soundfile wordfreq
pip install --no-deps openwakeword==0.6.0

# Piper training code (for the generator) and voice generators
git clone --depth 1 https://github.com/rhasspy/piper-sample-generator
mkdir -p pt models && ln -s "$PWD/piper-sample-generator/piper_train" pt/piper_train
cp piper-sample-generator/models/{en_US-libritts_r-medium,fr_FR-mls-medium}.pt.json models/
for m in en_US-libritts_r-medium fr_FR-mls-medium; do
  curl -L -o models/$m.pt https://github.com/rhasspy/piper-sample-generator/releases/download/v2.0.0/$m.pt
done

# Real audio
mkdir -p data && cd data
git clone --depth 1 https://github.com/karolpiczak/ESC-50 esc50
git clone --depth 1 https://github.com/Jakobovski/free-spoken-digit-dataset fsdd
git clone --depth 1 https://github.com/librosa/data librosa_data
cd ..
```

Then:

1. **Generate clips** with `gen.py MODEL OUT_DIR COUNT SEED SPEAKER_LO SPEAKER_HI @texts/FILE`,
   with `PYTHONPATH=pt`. Training speakers were 0–799 (English) and 0–109 (French);
   speakers 800–903 and 110–124 were kept for testing. The output folders
   used were `clips/{pos,adv,sent}_{en,fr}_{train,test}`:
   - `pos_en_train` 5,000, `pos_fr_train` 4,600 (wake phrase)
   - `adv_en_train` 2,500, `adv_fr_train` 1,200 (sound-alikes)
   - `sent_en_train` 3,000, `sent_fr_train` 1,600 (sentences)
   - each with a smaller `_test` set
2. **Features:** `python prep.py`, then
   `python stream_feats.py stream_sent 2 "sent_*_train/**/*.wav"`,
   `python stream_feats.py stream_real 2 esc fsdd music` and
   `python stream_feats.py stream_adv 1 "adv_*_train/**/*.wav"`.
3. **Train:** `python train.py 6000` writes `hey_orion.onnx` (about 4 minutes).
4. **Test:** `python evaluate.py hey_orion.onnx 0.5 0.7 0.85`.
5. Copy the model to `../models/hey_orion.onnx`.

`gen.py` phonemizes with the system `espeak-ng` command because the
espeak bridge bundled with `piper-tts` 1.3 could not find its data files. It
also picks random speaker pairs, so even small runs cover many voices.
