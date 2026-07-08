"""Stage 2 / step 07 — visualizations, SVG masks, hierarchy diagram (as run 2026-07-08; paths adapted)."""
import numpy as np, json, collections, os, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from _paths import CKPT, WORK, OUT as OUTP, MASTER
SC = str(CKPT)
OUT = str(OUTP)
LM = f'{OUT}/masks/labelmaps'
part = np.load(WORK / 'partition_L6.npy')
H, W = part.shape
REG = json.load(open(f'{OUT}/meta/regions_L0_L5.json'))
a = np.array(Image.open(MASTER))
S = 6  # viz downscale
a_s = a[::S, ::S]

def render_level(fname, title, label_prefix, fontscale=1.4, seed=11):
    lm = cv2.imread(f'{LM}/{fname}_labelmap.png', cv2.IMREAD_UNCHANGED)
    codes = json.load(open(f'{LM}/{fname}_codes.json'))
    small = lm[::S, ::S]
    K = int(small.max())
    rng = np.random.RandomState(seed)
    lut = np.zeros((K+1, 3), np.uint8); lut[1:] = rng.randint(70, 240, (K, 3))
    # fixed colors for special classes
    for code, uid in codes.items():
        c = int(code)
        if 'seine' in uid or 'water' in uid: lut[c] = (210, 130, 40)
        elif 'exterior' in uid or uid.endswith('_outside'): lut[c] = (242, 242, 242)
        elif 'bridge' in uid: lut[c] = (60, 200, 230)
    img = lut[small]
    img[a_s < 128] = (30, 30, 30)
    hdr = np.full((70, img.shape[1], 3), 255, np.uint8)
    cv2.putText(hdr, title, (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3, cv2.LINE_AA)
    for code, uid in codes.items():
        if uid.endswith('_outside') or 'exterior' in uid: continue
        r = REG.get(uid)
        if not r or r['area_px'] < 200000: continue
        cx, cy = r['centroid_px']
        label = uid.replace(label_prefix, '')
        sz, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 3)
        x = int(cx/S) - sz[0]//2; y = int(cy/S) + 70 + sz[1]//2
        cv2.putText(img, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, fontscale, (255,255,255), 5, cv2.LINE_AA)
        cv2.putText(img, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, fontscale, (0,0,0), 2, cv2.LINE_AA)
    full = np.vstack([hdr, img])
    cv2.imwrite(f'{OUT}/viz/{fname}_map.png', full)
    print('viz', fname, full.shape)

render_level('L1_macro', 'L1 — Macro geography: banks / Seine / islands / bridges', 'L1_', 1.6)
render_level('L2_arrondissements', 'L2 — Arrondissements (cell-snapped)', 'L2_', 1.6)
render_level('L3_quartiers', 'L3 — Quartiers administratifs (cell-snapped)', 'L3_', 1.1)
render_level('L4_semantic', 'L4 — Semantic units: parks, rail, plazas, islands, water', 'L4_', 1.0)
render_level('L5_superblocks', 'L5 — Superblocks (major-road bounded generation tiles)', 'L5_', 1.0)

# ---- L5 adjacency graph overlay ----
lm5 = cv2.imread(f'{LM}/L5_superblocks_labelmap.png', cv2.IMREAD_UNCHANGED)
img = cv2.cvtColor(255 - ((a_s < 128)*110).astype(np.uint8), cv2.COLOR_GRAY2BGR)
drawn = set()
for uid, r in REG.items():
    if r['level'] != 5 or r['type'] != 'superblock': continue
    x0, y0 = r['centroid_px']
    for nb in r.get('neighbors', {}):
        if nb in drawn or not nb.startswith('L5_sb'): continue
        r2 = REG[nb]
        x1, y1 = r2['centroid_px']
        cv2.line(img, (int(x0/S), int(y0/S)), (int(x1/S), int(y1/S)), (180, 120, 60), 2, cv2.LINE_AA)
    drawn.add(uid)
for uid, r in REG.items():
    if r['level'] != 5 or r['type'] != 'superblock': continue
    x0, y0 = int(r['centroid_px'][0]/S), int(r['centroid_px'][1]/S)
    cv2.circle(img, (x0, y0), 9, (0, 0, 200), -1, cv2.LINE_AA)
    cv2.putText(img, uid.replace('L5_sb',''), (x0+10, y0-6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,200), 2, cv2.LINE_AA)
cv2.imwrite(f'{OUT}/viz/L5_adjacency_graph.png', img)
print('adjacency overlay done')

# ---- SVG outlines for L1/L2/L5 ----
os.makedirs(f'{OUT}/masks/svg', exist_ok=True)
def to_svg(fname, out_name, min_area=5000, eps=3.0):
    lm = cv2.imread(f'{LM}/{fname}_labelmap.png', cv2.IMREAD_UNCHANGED)
    codes = json.load(open(f'{LM}/{fname}_codes.json'))
    rng = np.random.RandomState(5)
    parts_svg = []
    for code, uid in sorted(codes.items(), key=lambda kv: int(kv[0])):
        c = int(code)
        if uid.endswith('_outside') or 'exterior' in uid: continue
        m = (lm == c).astype(np.uint8)
        if m.sum()*1.0 < min_area: continue
        cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        col = '#%02x%02x%02x' % tuple(rng.randint(60, 220, 3))
        paths = []
        for cnt in cs:
            if cv2.contourArea(cnt) < min_area: continue
            ap = cv2.approxPolyDP(cnt, eps, True)[:, 0, :]
            d = 'M' + ' L'.join(f'{x},{y}' for x, y in ap) + ' Z'
            paths.append(d)
        if paths:
            parts_svg.append(f'<path id="{uid}" d="{" ".join(paths)}" fill="{col}" '
                             f'fill-opacity="0.45" stroke="{col}" stroke-width="6"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}">\n<!-- Diem decomposition {fname}; coordinates are '
           f'master-raster pixels (34048x5312). Derived from raster; raster is canonical. -->\n'
           + '\n'.join(parts_svg) + '\n</svg>')
    open(f'{OUT}/masks/svg/{out_name}.svg', 'w').write(svg)
    print('svg', out_name, len(parts_svg), 'regions')

to_svg('L1_macro', 'L1_macro')
to_svg('L2_arrondissements', 'L2_arrondissements')
to_svg('L5_superblocks', 'L5_superblocks')

# ---- hierarchy diagram (SVG) ----
counts = collections.Counter(r['level'] for r in REG.values())
rows = [
 ('L0', 'Canvas — full band', '1 region', '#888888'),
 ('L1', 'Macro geography (banks, Seine, islands, bridges, exterior)', f"{counts[1]} regions", '#2166ac'),
 ('L2', 'Arrondissements (cell-snapped, official boundaries)', f"{counts[2]} regions", '#4393c3'),
 ('L3', 'Quartiers administratifs (cell-snapped)', f"{counts[3]} regions", '#92c5de'),
 ('L4', 'Semantic units (parks, plazas, rail, islands, water) — overlay', f"{counts[4]} units", '#5aae61'),
 ('L5', 'Superblocks (major-road bounded tiles) — RECOMMENDED generation level', f"{counts[5]} regions", '#d6604d'),
 ('L6', 'Atomic enclosed street cells (city blocks)', '2560 cells', '#f4a582'),
]
y = 40; els = []
for i, (lid, desc, cnt, col) in enumerate(rows):
    els.append(f'<rect x="60" y="{y}" width="1080" height="72" rx="10" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="2.5"/>')
    els.append(f'<text x="84" y="{y+30}" font-family="Helvetica" font-size="24" font-weight="bold" fill="#111">{lid} — {desc}</text>')
    els.append(f'<text x="84" y="{y+58}" font-family="Helvetica" font-size="20" fill="#444">{cnt}</text>')
    if i < len(rows)-1:
        els.append(f'<line x1="600" y1="{y+72}" x2="600" y2="{y+94}" stroke="#666" stroke-width="2.5" marker-end="url(#ar)"/>')
    y += 96
els.append('<text x="84" y="' + str(y+18) + '" font-family="Helvetica" font-size="19" fill="#333">'
           'Nesting: L6 ⊂ L5 ⊂ L3 ⊂ L2 ⊂ L1 ⊂ L0 (L5→L3 by dominant quartier; purity in metadata). '
           'L4 is a semantic overlay on L6 groups.</text>')
svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 ' + str(y+50) + '">'
       '<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
       '<path d="M0,0 L10,4 L0,8 Z" fill="#666"/></marker></defs>'
       '<rect width="1200" height="' + str(y+50) + '" fill="white"/>' + ''.join(els) + '</svg>')
open(f'{OUT}/viz/hierarchy_diagram.svg', 'w').write(svg)
print('hierarchy diagram done')
