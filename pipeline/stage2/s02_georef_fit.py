"""Stage 2 / step 02 — georeference: lon/lat <-> pixel similarity transform.

As run 2026-07-08 (paths adapted). The committed checkpoints/georef_final.json is the
authoritative record of the transform actually used by all later steps.

Method: five plaza anchors (Étoile, Nation, Concorde, Vendôme, Victoires). Each anchor
pixel position is refined as the centroid of the enclosed white plaza region containing
the predicted point; a rigid similarity (rotation + uniform scale + translation, no
reflection) is then fit by complex least squares. Result: 0.4219 m/px (1:4983 at
300 dpi), rotation -20.32°, RMS residual 38 px ≈ 16 m.

Output: checkpoints/georef_final.json
"""
import json

import cv2
import numpy as np
from PIL import Image

from _paths import MASTER, CKPT

Image.MAX_IMAGE_PIXELS = None
LON0, LAT0 = 2.35, 48.86
MN = 111320.0
ME = MN * np.cos(np.radians(LAT0))

a = np.array(Image.open(MASTER))
H, W = a.shape

# initial 2-point seed (Étoile / Nation, visually identified star plazas)
SEED_PX = {'etoile': (6974, 2692), 'nation': (25700, 2888)}
ANCHORS = [  # name, lon, lat  (plaza geometric centers)
    ('etoile',     2.295028, 48.873792),
    ('nation',     2.395890, 48.848422),
    ('concorde',   2.321475, 48.865633),
    ('vendome',    2.329420, 48.867320),
    ('victoires',  2.341000, 48.865700),
]


def refine(seed_x, seed_y, r=350, max_area=200000):
    """Centroid of the enclosed white region containing (seed_x, seed_y)."""
    seed_x, seed_y = int(seed_x), int(seed_y)
    x0, y0 = max(0, seed_x - r), max(0, seed_y - r)
    x1, y1 = min(W, seed_x + r), min(H, seed_y + r)
    win = np.ascontiguousarray(a[y0:y1, x0:x1])
    n, lab = cv2.connectedComponents((win == 255).astype(np.uint8), connectivity=4)
    sy, sx = seed_y - y0, seed_x - x0
    L = lab[sy, sx]
    if L == 0:
        ys, xs = np.where(lab > 0)
        i = np.argmin((ys - sy) ** 2 + (xs - sx) ** 2)
        L = lab[ys[i], xs[i]]
    m = lab == L
    if m.sum() > max_area or m[0, :].any() or m[-1, :].any() or m[:, 0].any() or m[:, -1].any():
        return None
    ys, xs = np.nonzero(m)
    return float(x0 + xs.mean()), float(y0 + ys.mean())


# bootstrap: exact 2-point similarity from Étoile/Nation predicts the other anchors
e = refine(*SEED_PX['etoile']); n_ = refine(*SEED_PX['nation'])
z1 = complex((2.295028 - LON0) * ME, -(48.873792 - LAT0) * MN)
z2 = complex((2.395890 - LON0) * ME, -(48.848422 - LAT0) * MN)
w1, w2 = complex(*e), complex(*n_)
alpha = (w2 - w1) / (z2 - z1); beta = w1 - alpha * z1

pairs = []
for name, lon, lat in ANCHORS:
    w_ = alpha * complex((lon - LON0) * ME, -(lat - LAT0) * MN) + beta
    r = refine(w_.real, w_.imag)
    if r is None:
        print(f'  {name}: refine failed, skipped')
        continue
    pairs.append((lon, lat, *r))
    print(f'  {name}: ({r[0]:.0f}, {r[1]:.0f})')

z = np.array([complex((lon - LON0) * ME, -(lat - LAT0) * MN) for lon, lat, _, _ in pairs])
w = np.array([complex(px, py) for _, _, px, py in pairs])
A = np.vstack([z, np.ones_like(z)]).T
coef, *_ = np.linalg.lstsq(A, w, rcond=None)
alpha, beta = coef
resid = w - (alpha * z + beta)
rms = float(np.sqrt((np.abs(resid) ** 2).mean()))
scale = 1 / abs(alpha)
print(f'scale {scale:.4f} m/px | rotation {np.degrees(np.angle(alpha)):.3f} deg | RMS {rms:.1f} px')

json.dump({'alpha': [alpha.real, alpha.imag], 'beta': [beta.real, beta.imag],
           'lon0': LON0, 'lat0': LAT0, 'me': ME, 'mn': MN, 'rms_px': rms,
           'scale_m_per_px': scale, 'rotation_deg': float(np.degrees(np.angle(alpha)))},
          open(CKPT / 'georef_final.json', 'w'))
print('georef_final.json written')
