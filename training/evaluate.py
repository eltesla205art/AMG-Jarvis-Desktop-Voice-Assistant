"""Streaming evaluation on held-out audio, the way O.R.I.O.N. runs the model.

* Recall: held-out speakers saying "hey orion" (Piper EN/FR voices it never
  trained on, plus espeak-ng voices from a different TTS family), each placed in
  held-out background noise.
* False wakes: hours of held-out audio that is not the wake phrase
  (sentences, sound-alikes, real environmental sounds, real human speech, music).

usage: evaluate.py MODEL.onnx [threshold ...]
"""
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from openwakeword.model import Model

from audio_lib import (Augmenter, SR, esc_files, files, fsdd_split, load, music_files,
                       to_int16, trim)

model_path = sys.argv[1]
thresholds = [float(t) for t in sys.argv[2:]] or [0.3, 0.5, 0.7, 0.8, 0.9]
rng = random.Random(99)
bg_test = esc_files({5}) + fsdd_split(test=True) + music_files()[-2:]
aug = Augmenter(bg_test, rng)
model = Model(wakeword_models=[model_path], inference_framework="onnx")
name = Path(model_path).stem


def stream_scores(x):
    """Score every 80 ms frame of a 16 kHz float signal."""
    model.reset()
    pcm = to_int16(x)
    return np.array([model.predict(pcm[i:i + 1280])[name]
                     for i in range(0, len(pcm) - 1279, 1280)])


def detections(scores, thr, refractory=25):  # 25 frames = 2 s
    count, last = 0, -refractory
    for i, s in enumerate(scores):
        if s >= thr and i - last >= refractory:
            count, last = count + 1, i
    return count


def espeak_clips():
    out = []
    with tempfile.TemporaryDirectory() as d:
        for i, voice in enumerate(["en-us", "en-gb", "en-us+m3", "en-us+f2", "en-gb+m5", "en-us+f4",
                                   "fr-fr", "en-sc", "en-us+m7", "en-gb-x-rp"]):
            for speed in (130, 160, 190):
                p = f"{d}/{i}_{speed}.wav"
                subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-w", p, "hey orion"],
                               check=True, capture_output=True)
                out.append(trim(load(p)))
    return out


def recall_for(clips):
    peaks = []
    for c in clips:
        lead = np.zeros(int(SR * rng.uniform(1.0, 2.0)), np.float32)
        tail = np.zeros(int(SR * 1.0), np.float32)
        x = aug(np.concatenate([lead, c, tail]), p_noise=0.7, p_rir=0.3)
        peaks.append(stream_scores(x).max())
    return np.array(peaks)


sets = {
    "Piper EN, unseen speakers": [trim(load(p)) for p in files("pos_en_test/**/*.wav")],
    "Piper FR, unseen speakers": [trim(load(p)) for p in files("pos_fr_test/**/*.wav")],
    "espeak-ng (other TTS)": espeak_clips(),
}
peaks = {k: recall_for(v) for k, v in sets.items()}

neg_sets = {
    "sentences EN/FR": files("sent_*_test/**/*.wav"),
    "sound-alikes": files("adv_*_test/**/*.wav"),
    "real sounds (ESC-50)": esc_files({5}),
    "real speech (FSDD)": fsdd_split(test=True),
    "music": music_files()[-2:],
}
neg_scores = {}
for k, paths in neg_sets.items():
    gap = np.zeros(int(SR * 0.3), np.float32)
    x = np.concatenate([np.concatenate([load(p), gap]) for p in paths])
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.3
    neg_scores[k] = (stream_scores(x), len(x) / SR / 3600)

for thr in thresholds:
    print(f"\n== threshold {thr}")
    for k, p in peaks.items():
        print(f"  recall  {k:28s} {np.mean(p >= thr) * 100:5.1f}%  (n={len(p)})")
    total_fa, total_h = 0, 0.0
    for k, (s, hours) in neg_scores.items():
        fa = detections(s, thr)
        total_fa, total_h = total_fa + fa, total_h + hours
        print(f"  false wakes {k:24s} {fa:3d} in {hours * 60:5.1f} min")
    print(f"  false wakes per hour overall: {total_fa / total_h:.2f}  ({total_h * 60:.0f} min tested)")
