"""Stage 2 / step 06 — export label maps + binary masks (as run 2026-07-08; paths adapted)."""
import numpy as np, json, collections, os, cv2

from _paths import CKPT, WORK, OUT as OUTP, MASTER
SC = str(CKPT)
OUT = str(OUTP)
part = np.load(WORK / 'partition_L6.npy')
H, W = part.shape; N = 2560
c2u = json.load(open(f'{SC}/cell2unit.json'))

os.makedirs(f'{OUT}/masks/labelmaps', exist_ok=True)

# ---- L6 label map (16-bit PNG, value = cell id 1..2560, 0 never used) ----
cv2.imwrite(f'{OUT}/masks/labelmaps/L6_cells_labelmap16.png', part.astype(np.uint16))

# ---- build integer codes per level; save labelmap + code table ----
def export_level(lvl_key, fname):
    mapping = c2u[lvl_key]
    unit_ids = sorted(set(mapping.values()))
    code_of = {u: i+1 for i, u in enumerate(unit_ids)}
    lut = np.zeros(N+1, np.uint16)
    for cell_str, u in mapping.items():
        lut[int(cell_str)] = code_of[u]
    lm = lut[part]
    depth = np.uint8 if len(unit_ids) < 255 else np.uint16
    cv2.imwrite(f'{OUT}/masks/labelmaps/{fname}_labelmap.png', lm.astype(depth))
    json.dump({str(v): k for k, v in code_of.items()},
              open(f'{OUT}/masks/labelmaps/{fname}_codes.json', 'w'), indent=1)
    return lm, code_of

masks_done = 0
for lvl_key, fname, do_binary in (('l1', 'L1_macro', True), ('l2', 'L2_arrondissements', True),
                                  ('l3', 'L3_quartiers', True), ('l4', 'L4_semantic', True),
                                  ('l5', 'L5_superblocks', True)):
    lm, code_of = export_level(lvl_key, fname)
    if do_binary:
        d = f'{OUT}/masks/{fname}'
        os.makedirs(d, exist_ok=True)
        for u, code in code_of.items():
            if u.endswith('_outside'): continue
            m = (lm == code)
            if not m.any(): continue
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            img = Image.fromarray(m)   # bool -> mode '1' internally via convert
            img = img.convert('L').point(lambda v: 255 if v else 0).convert('1')
            img.save(f'{d}/{u}.png', optimize=True)
            masks_done += 1
    del lm
print('binary masks written:', masks_done)

# ink mask (utility for consumers: AND with region mask to clip strokes)
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
a = np.array(Image.open(MASTER))
ink = a < 255
Image.fromarray(ink).convert('L').point(lambda v: 255 if v else 0).convert('1')\
     .save(f'{OUT}/masks/ink_mask.png', optimize=True)
print('ink mask written')
