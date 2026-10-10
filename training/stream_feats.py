"""Negative features the way the model sees audio when running: every 80 ms
slice of long, continuous, augmented recordings (not just clip-shaped windows).

usage: stream_feats.py NAME STRIDE GLOB_OR_SOURCE...
"""
import random
import sys
import time

import numpy as np
from openwakeword.utils import AudioFeatures

from audio_lib import (Augmenter, SR, esc_files, files, fsdd_split, load, music_files,
                       to_int16, ROOT)

CHUNK = 30 * SR
name, stride = sys.argv[1], int(sys.argv[2])
sources = sys.argv[3:]
rng = random.Random(hash(name) & 0xFFFF)
features = AudioFeatures(inference_framework="onnx", ncpu=4)
bg = esc_files({1, 2, 3, 4}) + fsdd_split() + music_files() + files("sent_*_train/**/*.wav")[::5]
aug = Augmenter(bg, rng)

paths = []
for s in sources:
    if s == "esc":  # ESC-10 is small, so it is replayed with fresh augmentation
        paths += esc_files({1, 2, 3, 4}) * 4
    elif s == "fsdd":
        paths += fsdd_split()
    elif s == "music":
        paths += music_files()
    else:
        paths += files(s)
rng.shuffle(paths)
print(name, len(paths), "files", flush=True)

chunks, cur = [], []
cur_len = 0
for p in paths:
    x = load(p)
    gap = np.zeros(int(SR * rng.uniform(0.1, 1.0)), np.float32)
    cur += [x, gap]
    cur_len += len(x) + len(gap)
    while cur_len >= CHUNK:
        stream = np.concatenate(cur)
        chunks.append(stream[:CHUNK])
        rest = stream[CHUNK:]
        cur, cur_len = [rest], len(rest)

t = time.time()
windows = []
for b in range(0, len(chunks), 16):
    batch = np.stack([to_int16(aug(c, p_noise=0.6, p_rir=0.3)) for c in chunks[b:b + 16]])
    emb = features.embed_clips(batch, batch_size=16)  # (n, frames, 96)
    for e in emb:
        for i in range(0, e.shape[0] - 16 + 1, stride):
            windows.append(e[i:i + 16])
out = np.stack(windows).astype(np.float16)
np.save(ROOT / "features" / f"{name}.npy", out)
print(f"{name}: {out.shape} from {len(chunks)} x 30 s in {time.time() - t:.0f}s", flush=True)
