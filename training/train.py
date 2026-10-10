"""Train the hey_orion head: balanced sampling over clip windows plus
continuous streams, then two rounds of hard-negative mining (windows the model
still scores high get more weight) with fine-tuning. Exports hey_orion.onnx.

usage: [FRPOS=0] [OUT=hey_orion.onnx] python train.py [steps]"""
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_head import Head

ROOT = Path(__file__).resolve().parent
FEAT = ROOT / "features"
torch.manual_seed(0)
rng = np.random.default_rng(0)
torch.set_num_threads(4)

def load(n):
    return torch.from_numpy(np.load(FEAT / f"{n}.npy").astype(np.float32))

import os
# Share of French-voice "hey orion" examples to train on. The shipped model
# uses 0: said the French way ("è-orion") the phrase is nearly identical to
# everyday French ("et aurions"), and including it caused constant false wakes.
keep_fr = float(os.environ.get("FRPOS", "0"))
fr = load("pos_fr")
fr = fr[torch.from_numpy(rng.permutation(len(fr))[:int(len(fr) * keep_fr)])]
pos = torch.cat([load("pos_en"), fr])
OUT_NAME = os.environ.get("OUT", "hey_orion.onnx")
neg_parts = {"neg_partial": 2.0, "neg_adv": 3.0, "neg_sent": 1.0, "neg_real": 1.0, "neg_noise": 0.5,
             "stream_sent": 1.0, "stream_real": 1.0, "stream_adv": 3.0}
negs = [load(n) for n in neg_parts]
neg = torch.cat(negs)
neg_w = torch.cat([torch.full((len(x),), w) for x, w in zip(negs, neg_parts.values())])
print("pos", len(pos), "neg", len(neg), {n: len(x) for n, x in zip(neg_parts, negs)}, flush=True)

# hold out 5% of each for validation
pv = torch.from_numpy(rng.permutation(len(pos)))
nv = torch.from_numpy(rng.permutation(len(neg)))
pos_val, pos_tr = pos[pv[:len(pos) // 20]], pos[pv[len(pos) // 20:]]
neg_val, neg_tr = neg[nv[:len(neg) // 20]], neg[nv[len(neg) // 20:]]
w_tr = neg_w[nv[len(neg) // 20:]]

model = Head()


def run(steps, lr, w_tr, neg_scale_end):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps)
    probs = (w_tr / w_tr.sum()).numpy().astype(np.float64)
    probs /= probs.sum()
    for step in range(steps):
        model.train()
        pi = torch.from_numpy(rng.integers(0, len(pos_tr), 256))
        ni = torch.from_numpy(rng.choice(len(neg_tr), 768, p=probs))
        xb = torch.cat([pos_tr[pi], neg_tr[ni]])
        xb = xb + 0.05 * torch.randn_like(xb)
        yb = torch.cat([torch.ones(256), torch.zeros(768)])
        scale = 1.0 + (neg_scale_end - 1.0) * step / steps
        wb = torch.cat([torch.ones(256), torch.full((768,), scale)])
        loss = (nn.functional.binary_cross_entropy(model(xb).squeeze(1), yb, reduction="none") * wb).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        if step % 1000 == 999 or step == steps - 1:
            report(step)


@torch.no_grad()
def scores(x):
    model.eval()
    return torch.cat([model(x[i:i + 8192]).squeeze(1) for i in range(0, len(x), 8192)])


def report(step):
    sp, sn = scores(pos_val), scores(neg_val)
    msg = " ".join(f"t{t}: rec {(sp >= t).float().mean():.3f} fp {(sn >= t).float().mean():.5f}" for t in (0.5, 0.8))
    print(f"step {step + 1}: {msg}", flush=True)


steps = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
run(steps, 2e-3, w_tr, 6.0)
# Hard-negative mining: boost whatever still scores high.
for rnd in range(2):
    s = scores(neg_tr)
    hard = s > 0.2
    print(f"mining round {rnd + 1}: {int(hard.sum())} hard negatives", flush=True)
    w_tr = w_tr * torch.where(hard, 8.0, 1.0)
    run(steps // 2, 7e-4, w_tr, 4.0)

model.eval()
out = ROOT / OUT_NAME
torch.onnx.export(model, torch.zeros(1, 16, 96), str(out), input_names=["x"], output_names=["score"],
                  opset_version=13, dynamo=False)
print("saved", out)
