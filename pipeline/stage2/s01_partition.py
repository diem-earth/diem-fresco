"""Stage 2 / step 01 — atomic-cell segmentation and seamless partition.

As run 2026-07-08 (paths adapted to repo layout). Deterministic.

Ink = value < 255 (anti-aliasing counts as wall — preserves the 72 nearly-collapsed
parallel-street channels). The canvas border acts as a virtual closing wall (a
segmentation convention; the master raster is never modified). White regions >= 50 px
become the 2,560 atomic cells; smaller slivers and all ink pixels are absorbed into
the nearest cell by iterative label propagation, yielding a complete partition of all
180,862,976 canvas pixels.

Outputs:
  work/partition_L6.npy        int32 label map, values 1..2560   (heavy, gitignored)
  checkpoints/props_L6.json    per-cell area / open area / bbox / centroid
"""
import gc
import json

import cv2
import numpy as np
from PIL import Image

from _paths import MASTER, CKPT, WORK

Image.MAX_IMAGE_PIXELS = None

a = np.array(Image.open(MASTER))
H, W = a.shape
assert (H, W) == (5312, 34048)

# --- closed-region segmentation ---
walls = (a < 255).copy()
walls[0, :] = True; walls[-1, :] = True; walls[:, 0] = True; walls[:, -1] = True
n, lab, stats, cent = cv2.connectedComponentsWithStats((~walls).astype(np.uint8), connectivity=4)
areas = stats[:, cv2.CC_STAT_AREA]

# --- seeds: regions >= 50 px, compactly relabeled 1..N ---
keep = np.zeros(n, bool)
keep[1:] = areas[1:] >= 50
n_cells = int(keep.sum())
remap = np.zeros(n, np.int32)
remap[keep] = np.arange(1, n_cells + 1, dtype=np.int32)
seeds = remap[lab]
del lab; gc.collect()
print('atomic cells:', n_cells)
assert n_cells == 2560, f'expected 2560 cells, got {n_cells} (master changed?)'

# --- label propagation into ink + slivers (float32 max-dilation) ---
labf = seeds.astype(np.float32); del seeds; gc.collect()
unassigned = labf == 0
k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
it = 0
while unassigned.any():
    it += 1
    d = cv2.dilate(labf, k)
    labf[unassigned] = d[unassigned]
    unassigned = labf == 0
    if it > 300:
        raise RuntimeError('propagation did not converge')
part = labf.astype(np.int32); del labf, unassigned; gc.collect()
np.save(WORK / 'partition_L6.npy', part)
print(f'partition complete in {it} iterations')

# --- per-cell properties ---
N = n_cells
lab_flat = part.ravel()
part_area = np.bincount(lab_flat, minlength=N + 1)
white_area = np.bincount(lab_flat[(a == 255).ravel()], minlength=N + 1)
xs_idx = np.arange(W)
minx = np.full(N + 1, W); maxx = np.zeros(N + 1)
miny = np.full(N + 1, H); maxy = np.zeros(N + 1)
sumx = np.zeros(N + 1); sumy = np.zeros(N + 1)
for y in range(H):
    row = part[y]
    for L in np.unique(row):
        m = row == L
        xm = xs_idx[m]
        if xm[0] < minx[L]: minx[L] = xm[0]
        if xm[-1] > maxx[L]: maxx[L] = xm[-1]
        if y < miny[L]: miny[L] = y
        if y > maxy[L]: maxy[L] = y
    sumx += np.bincount(row, weights=xs_idx, minlength=N + 1)
    sumy += np.bincount(row, weights=np.full(W, y), minlength=N + 1)
props = {}
for L in range(1, N + 1):
    props[L] = dict(part_area=int(part_area[L]), white_area=int(white_area[L]),
                    bbox=[int(minx[L]), int(miny[L]), int(maxx[L]), int(maxy[L])],
                    centroid=[round(sumx[L] / part_area[L], 1), round(sumy[L] / part_area[L], 1)])
json.dump(props, open(CKPT / 'props_L6.json', 'w'))
print('props_L6.json written')
