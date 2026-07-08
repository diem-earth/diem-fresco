#!/usr/bin/env python3
"""Reproduce diem_master_geometry_v1.tiff from canny_final.tiff.

Deterministic: relabels connected components (8-connectivity, ink = value < 255)
and removes exactly the 24 artifact components listed in removal_manifest.csv,
verified by bounding box + area before deletion. Aborts if anything differs.

Requires: numpy, opencv-python, tifffile, pillow
"""
import csv
import os
import sys

import cv2
import numpy as np
import tifffile
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'canny_final.tiff')
DST = os.path.join(HERE, '..', 'diem_master_geometry_v1.tiff')
MANIFEST = os.path.join(HERE, 'removal_manifest.csv')

src = np.array(Image.open(SRC))
assert src.shape == (5312, 34048) and src.dtype == np.uint8

n, lab, stats, _ = cv2.connectedComponentsWithStats(
    (src < 255).astype(np.uint8), connectivity=8)

out = src.copy()
removed = 0
with open(MANIFEST) as f:
    for row in csv.DictReader(f):
        label = int(row['component'].lstrip('L'))
        x, y, w, h, area = (int(row[k]) for k in ('x', 'y', 'width', 'height', 'area_px'))
        sx, sy, sw, sh, sa = stats[label]
        if (sx, sy, sw, sh, sa) != (x, y, w, h, area):
            sys.exit(f'ABORT: component {label} does not match manifest '
                     f'({(sx, sy, sw, sh, sa)} != {(x, y, w, h, area)})')
        out[lab == label] = 255
        removed += area

assert (out != src).sum() == removed == 8743
assert out.shape == src.shape

desc = ('Diem fresco project - MASTER GEOMETRY v1.0 - Paris Centre street network. '
        'Derived from canny_final.tiff (2025-11-19, author Mathis Koroglu): 24 isolated '
        'artifact components (8743 px, 0.029% of ink) outside the intended map body removed; '
        'all street geometry byte-identical to source. Canvas 34048x5312 px @ 300 dpi. 2026-07-07.')
tifffile.imwrite(DST, out, compression='adobe_deflate', predictor=True,
                 resolution=(300, 300), resolutionunit='INCH', description=desc,
                 software='Diem pipeline / cleanup v1.0',
                 extratags=[(315, 's', None, 'Mathis Koroglu', True)])
print(f'OK: wrote {DST} ({removed} px removed)')
