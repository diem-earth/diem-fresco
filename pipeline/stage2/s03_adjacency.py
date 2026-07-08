"""Stage 2 / step 03 — cell adjacency graph with boundary statistics.

As run 2026-07-08 (paths adapted). For every pair of adjacent cells in the seamless
partition: shared-boundary length (px), boundary centroid, and the fraction of the
boundary lying inside the major-road cut corridor (used later for L5 graph cuts).

Inputs:  work/partition_L6.npy, checkpoints/georef_final.json, sources/major_roads.json
Outputs: work/cutmask_major.npy, checkpoints/edges_L6_v2.json
"""
import collections
import json

import cv2
import numpy as np

from _paths import CKPT, SOURCES, WORK

part = np.load(WORK / 'partition_L6.npy')
H, W = part.shape
N = int(part.max())

g = json.load(open(CKPT / 'georef_final.json'))
alpha = complex(*g['alpha']); beta = complex(*g['beta'])
LON0, LAT0, ME, MN = g['lon0'], g['lat0'], g['me'], g['mn']


def geo2px_arr(lon, lat):
    e = (np.asarray(lon) - LON0) * ME; n = (np.asarray(lat) - LAT0) * MN
    return alpha.real * e + alpha.imag * n + beta.real, alpha.imag * e - alpha.real * n + beta.imag


# --- rasterize major roads (motorway/trunk/primary) into ±30 px cut corridors ---
d = json.load(open(SOURCES / 'major_roads.json'))
cut = np.zeros((H, W), np.uint8)
for way in d['elements']:
    if way['type'] != 'way':
        continue
    lons = [p['lon'] for p in way['geometry']]; lats = [p['lat'] for p in way['geometry']]
    xs, ys = geo2px_arr(lons, lats)
    pts = np.stack([xs, ys], 1)
    if not ((pts[:, 0] > -500) & (pts[:, 0] < W + 500) & (pts[:, 1] > -500) & (pts[:, 1] < H + 500)).any():
        continue
    cv2.polylines(cut, [pts.astype(np.int32)], False, 1, 1)
cut = cv2.dilate(cut, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
np.save(WORK / 'cutmask_major.npy', cut)

# --- chunked adjacency scan ---
acc = {}
CH = 512
for y0 in range(0, H, CH):
    y1 = min(H, y0 + CH + 1)
    p = part[y0:y1]; c_ = cut[y0:y1]
    for axis in (1, 0):
        if axis == 1:
            A_, B_ = p[:, :-1], p[:, 1:]; CA = c_[:, :-1]
        else:
            A_, B_ = p[:-1, :], p[1:, :]; CA = c_[:-1, :]
        m = A_ != B_
        if not m.any():
            continue
        yy, xx = np.nonzero(m)
        lo = np.minimum(A_[m], B_[m]).astype(np.int64)
        hi = np.maximum(A_[m], B_[m]).astype(np.int64)
        packed = lo * (N + 1) + hi
        u, inv = np.unique(packed, return_inverse=True)
        cnt = np.bincount(inv)
        sx = np.bincount(inv, weights=xx.astype(np.float64))
        sy = np.bincount(inv, weights=(yy + y0).astype(np.float64))
        sc = np.bincount(inv, weights=CA[m].astype(np.float64))
        for k_, c1, x1, y1_, s1 in zip(u, cnt, sx, sy, sc):
            if k_ in acc:
                r = acc[k_]; r[0] += int(c1); r[1] += x1; r[2] += y1_; r[3] += s1
            else:
                acc[k_] = [int(c1), x1, y1_, s1]

edges = []
for k_, (c1, x1, y1_, s1) in acc.items():
    i, j = divmod(k_, N + 1)
    edges.append(dict(a=int(i), b=int(j), boundary_px=c1,
                      bx=round(x1 / c1, 1), by=round(y1_ / c1, 1),
                      cut_frac=round(s1 / c1, 3)))
json.dump(edges, open(CKPT / 'edges_L6_v2.json', 'w'))
print('edges:', len(edges))
