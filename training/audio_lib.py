"""Audio loading and augmentation shared by the prep and eval scripts."""
import glob
import random
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly, butter, sosfilt

SR = 16000
WIN = 32000  # 2.0 s -> exactly 16 openWakeWord embedding frames
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CLIPS = ROOT / "clips"


def load(path) -> np.ndarray:
    """Mono float32 in [-1, 1] at 16 kHz."""
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return x


def trim(x, thresh=0.01):
    idx = np.where(np.abs(x) > thresh)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x


def files(pattern):
    return sorted(glob.glob(str(CLIPS / pattern), recursive=True))


def esc_files(folds):
    import csv
    rows = list(csv.DictReader(open(DATA / "esc50/meta/esc50.csv")))
    return [str(DATA / "esc50/audio" / r["filename"]) for r in rows if int(r["fold"]) in folds]


def fsdd_files(speakers):
    return [p for p in sorted(glob.glob(str(DATA / "fsdd/recordings/*.wav")))
            if Path(p).stem.split("_")[1] in speakers]


FSDD_TEST = {"yweweler", "nicolas"}


def fsdd_split(test=False):
    all_s = {Path(p).stem.split("_")[1] for p in glob.glob(str(DATA / "fsdd/recordings/*.wav"))}
    return fsdd_files(FSDD_TEST if test else all_s - FSDD_TEST)


def music_files():
    return sorted(p for p in glob.glob(str(DATA / "librosa_data/audio/*.ogg")) if ".hq." not in p)


def colored_noise(n, rng, kind):
    white = rng.standard_normal(n).astype(np.float32)
    if kind == "white":
        return white
    f = np.fft.rfft(white)
    freqs = np.arange(len(f)) + 1.0
    f /= np.sqrt(freqs) if kind == "pink" else freqs
    out = np.fft.irfft(f, n).astype(np.float32)
    return out / (np.std(out) + 1e-9)


def synthetic_rir(rng):
    """Exponentially decaying noise burst: cheap stand-in for room reverb."""
    rt60 = rng.uniform(0.15, 0.8)
    n = int(SR * rt60)
    t = np.arange(n) / SR
    rir = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)
    rir[0] = 1.0 + abs(rir[0])
    rir *= rng.uniform(0.3, 1.0)
    rir[0] = 1.0
    return (rir / np.sqrt(np.sum(rir ** 2))).astype(np.float32)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


class Augmenter:
    def __init__(self, background_files, rng: random.Random):
        self.bg_files = background_files
        self.rng = rng
        self.nprng = np.random.default_rng(rng.randrange(1 << 30))
        self.cache = {}

    def background(self, n):
        r = self.rng.random()
        if r < 0.3 or not self.bg_files:
            return colored_noise(n, self.nprng, self.rng.choice(["white", "pink", "brown"]))
        path = self.rng.choice(self.bg_files)
        if path not in self.cache:
            if len(self.cache) > 400:
                self.cache.clear()
            self.cache[path] = load(path)
        x = self.cache[path]
        if len(x) < n:
            x = np.tile(x, n // max(len(x), 1) + 1)
        start = self.rng.randrange(0, len(x) - n + 1)
        return x[start:start + n]

    def __call__(self, x, p_noise=0.75, p_rir=0.4):
        x = x.copy()
        if self.rng.random() < p_rir:
            x = fftconvolve(x, synthetic_rir(self.nprng))[:len(x)].astype(np.float32)
        if self.rng.random() < 0.1:  # cheap mic / phone band limit
            lo, hi = self.rng.uniform(150, 400), self.rng.uniform(3000, 7000)
            x = sosfilt(butter(4, [lo, hi], btype="band", fs=SR, output="sos"), x).astype(np.float32)
        if self.rng.random() < p_noise:
            bg = self.background(len(x))
            snr = self.rng.uniform(0, 30)
            speech = rms(x[np.abs(x) > 0.01]) if np.any(np.abs(x) > 0.01) else rms(x)
            x = x + bg * (speech / rms(bg)) / (10 ** (snr / 20))
        level = 10 ** (self.rng.uniform(-30, -6) / 20)  # final loudness
        x = x / (np.max(np.abs(x)) + 1e-9) * level
        return x.astype(np.float32)


def place_end(clip, rng, jitter=(0.0, 0.3)):
    """Window of WIN samples with the clip ending ``jitter`` seconds before the end."""
    out = np.zeros(WIN, dtype=np.float32)
    gap = int(rng.uniform(*jitter) * SR)
    clip = clip[-(WIN - gap):]
    end = WIN - gap
    out[end - len(clip):end] = clip
    return out


def random_crop(x, rng):
    if len(x) <= WIN:
        out = np.zeros(WIN, dtype=np.float32)
        start = rng.randrange(0, WIN - len(x) + 1)
        out[start:start + len(x)] = x
        return out
    start = rng.randrange(0, len(x) - WIN + 1)
    return x[start:start + WIN].copy()


def to_int16(x):
    return np.clip(x * 32767, -32768, 32767).astype(np.int16)
