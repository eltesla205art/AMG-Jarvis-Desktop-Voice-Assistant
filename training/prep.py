"""Build augmented 2 s training windows and turn them into openWakeWord features.

Writes features/{name}.npy with shape (N, 16, 96).
"""
import random
import sys
import time

import numpy as np
from openwakeword.utils import AudioFeatures

from audio_lib import (Augmenter, esc_files, files, fsdd_split, load, music_files,
                       place_end, random_crop, to_int16, trim, colored_noise, WIN, ROOT)

OUT = ROOT / "features"
OUT.mkdir(exist_ok=True)
rng = random.Random(1234)
features = AudioFeatures(inference_framework="onnx", ncpu=4)

speech_bg = files("sent_*_train/**/*.wav")
bg_train = esc_files({1, 2, 3, 4}) + fsdd_split() + music_files() + speech_bg[::4]
aug = Augmenter(bg_train, rng)


def embed(name, windows):
    arr = np.stack([to_int16(w) for w in windows])
    t = time.time()
    feats = features.embed_clips(arr, batch_size=256)
    np.save(OUT / f"{name}.npy", feats.astype(np.float16))
    print(f"{name}: {feats.shape} in {time.time() - t:.0f}s", flush=True)


def clip_windows(paths, copies, end_aligned=True, p_noise=0.75, cut=None):
    out = []
    for p in paths:
        x = trim(load(p))
        if cut:  # keep only the start, e.g. just "hey" of "hey orion"
            x = x[:int(len(x) * rng.uniform(*cut))]
        for _ in range(copies):
            w = place_end(x, rng) if end_aligned else random_crop(x, rng)
            out.append(aug(w, p_noise=p_noise))
    return out


def crops(paths, per_file, p_noise=0.3):
    out = []
    for p in paths:
        x = load(p)
        for _ in range(per_file):
            out.append(aug(random_crop(x, rng), p_noise=p_noise, p_rir=0.2))
    return out


jobs = sys.argv[1:] or ["pos", "pos_partial", "adv", "sent", "real", "noise"]
pos = files("pos_*_train/**/*.wav")
if "pos" in jobs:
    embed("pos_en", clip_windows(files("pos_en_train/**/*.wav"), 3))
    embed("pos_fr", clip_windows(files("pos_fr_train/**/*.wav"), 3))
if "pos_partial" in jobs:
    embed("neg_partial", clip_windows(rng.sample(pos, 2500), 1, cut=(0.3, 0.55)))
if "adv" in jobs:
    embed("neg_adv", clip_windows(files("adv_*_train/**/*.wav"), 3))
if "sent" in jobs:
    s = files("sent_*_train/**/*.wav")
    embed("neg_sent", clip_windows(s, 1) + clip_windows(s, 1, end_aligned=False))
if "real" in jobs:
    embed("neg_real", crops(esc_files({1, 2, 3, 4}), 15) + crops(fsdd_split(), 1)
          + crops(music_files(), 150))  # ESC-10 is small: 15 crops per clip
if "noise" in jobs:
    npr = np.random.default_rng(5)
    noise = [colored_noise(WIN, npr, k) * 10 ** (rng.uniform(-50, -10) / 20)
             for k in ["white", "pink", "brown"] * 700]
    embed("neg_noise", noise + [np.zeros(WIN, np.float32)] * 200)
