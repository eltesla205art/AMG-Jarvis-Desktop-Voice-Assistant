"""Generate synthetic speech clips with Piper's multi-speaker generators.

Wraps piper_sample_generator: phonemizes with the system espeak-ng CLI (the
bundled bridge fails to find its data here) and picks random speaker pairs
instead of the library's sequential order, so even small runs are diverse.

usage: gen.py MODEL.pt OUT_DIR COUNT SEED SPEAKER_LO SPEAKER_HI TEXT [TEXT...]
       (TEXT may be @file with one phrase per line)
"""
import random
import subprocess
import sys
import types
import unicodedata
import wave
from pathlib import Path


class CliPhonemizer:
    def __init__(self, *a, **k):
        self.cache = {}

    def phonemize(self, voice, text):
        key = (voice, text)
        if key not in self.cache:
            out = subprocess.run(["espeak-ng", "-q", "--ipa", "-v", voice, text],
                                 capture_output=True, text=True, check=True).stdout
            ipa = " ".join(out.split())
            self.cache[key] = [list(unicodedata.normalize("NFD", ipa))]
        return self.cache[key]


stub = types.ModuleType("piper.phonemize_espeak")
stub.EspeakPhonemizer = CliPhonemizer
stub.ESPEAK_DATA_DIR = None
sys.modules["piper.phonemize_espeak"] = stub

import json  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from piper_sample_generator import __main__ as psg  # noqa: E402


def main():
    model_path, out_dir, count, seed, lo, hi = sys.argv[1:7]
    texts = []
    for t in sys.argv[7:]:
        texts += Path(t[1:]).read_text().split("\n") if t.startswith("@") else [t]
    texts = [t.strip() for t in texts if t.strip()]
    count, lo, hi = int(count), int(lo), int(hi)
    rng = random.Random(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)

    model = torch.load(model_path, weights_only=False).eval()
    config = json.load(open(f"{model_path}.json"))
    voice, rate = config["espeak"]["voice"], config["audio"]["sample_rate"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    batch = int(__import__("os").environ.get("GEN_BATCH", 8))
    done = len(list(out.glob("*.wav")))
    while done < count:
        n = min(batch, count - done)
        s1 = torch.LongTensor([rng.randrange(lo, hi) for _ in range(n)])
        s2 = torch.LongTensor([rng.randrange(lo, hi) for _ in range(n)])
        ids = [psg.get_phonemes(voice, config, rng.choice(texts)) for _ in range(n)]
        width = max(map(len, ids))
        ids = [i + [1] * (width - len(i)) for i in ids]
        with torch.no_grad():
            audio, samples = psg.generate_audio(
                model, s1, s2, ids,
                slerp_weight=rng.choice([0.0, 0.25, 0.5, 0.75, 1.0]),
                noise_scale=rng.choice([0.667, 0.75, 0.85, 0.9, 1.0]),
                noise_scale_w=rng.choice([0.6, 0.8, 1.0]),
                length_scale=rng.choice([0.75, 0.85, 1.0, 1.15, 1.3]),
                max_len=None)
        for i in range(n):
            last = int(samples[i].flatten().sum().item())
            audio[i, 0, last + 1:] = 0
        pcm = psg.audio_float_to_int16(audio.numpy())
        for i in range(n):
            data = np.trim_zeros(pcm[i].flatten())
            with wave.open(str(out / f"{seed}_{done}.wav"), "wb") as w:
                w.setframerate(rate)
                w.setsampwidth(2)
                w.setnchannels(1)
                w.writeframes(data.tobytes())
            done += 1


if __name__ == "__main__":
    main()
