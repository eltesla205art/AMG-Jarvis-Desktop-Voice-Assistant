from torch import nn


class Head(nn.Module):
    """Same shape as openWakeWord's own heads: 16 x 96 embeddings -> score."""

    def __init__(self, dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(16 * 96, dim), nn.LayerNorm(dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(dim, dim), nn.LayerNorm(dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(dim, 1), nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x)
