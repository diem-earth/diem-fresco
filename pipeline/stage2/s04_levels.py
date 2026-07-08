"""Stage 2 / step 04 — build all decomposition levels (consolidated).

As run 2026-07-08, consolidated from the working session into one script
(paths adapted; logic identical). Produces every decision checkpoint:

  1. special cells:  Seine water (centerline waypoint voting), Île de la Cité /
     Île Saint-Louis (explicit footprint polygons — narrow island cells touch both
     Seine arms and would otherwise be misclassified as bridges), bridge decks
     (small cells adjacent to >= 2 water cells), exterior margins.
  2. L1 macro geography: graph reachability with water+bridge+island cells removed
     separates Rive Droite / Rive Gauche; islands and Seine are their own classes.
  3. L2/L3: arrondissement / quartier assignment by cell centroid inside the
     official polygons projected through the georeference (cell-snapped).
  4. L4 semantic units: named OSM parks/cemeteries >= 1 ha, surface rail corridors
     (tunnels excluded — underground RER is invisible in the artwork), curated plazas.
  5. L5 superblocks: cell-adjacency graph cut where a shared wall lies >= 55% inside
     the major+secondary road corridor; islands never merge with banks; fragments
     < 2.5 ha absorbed into the neighbor with the longest shared boundary.
     (Stroke-thickness merging was tried and FAILED — 75% of streets are drawn at a
     uniform ~25 px, thin walls percolate; see PHASE2_TOPOLOGY.md.)

Outputs (checkpoints/): special_cells.json, levels_l123.json, admin_names.json,
                        units_L4.json, superblocks_L5.json
         (work/):       cutmask_all.npy
"""
import collections
import json

import cv2
import numpy as np
from shapely.affinity import affine_transform
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union

from _paths import CKPT, SOURCES, WORK

N = 2560
part = np.load(WORK / 'partition_L6.npy')
H, W = part.shape
props = json.load(open(CKPT / 'props_L6.json'))
edges = json.load(open(CKPT / 'edges_L6_v2.json'))
g = json.load(open(CKPT / 'georef_final.json'))
alpha = complex(*g['alpha']); beta = complex(*g['beta'])
LON0, LAT0, ME, MN = g['lon0'], g['lat0'], g['me'], g['mn']
ar, ai = alpha.real, alpha.imag
PARAMS = [ar * ME, ai * MN, ai * ME, -ar * MN,
          -ar * ME * LON0 - ai * MN * LAT0 + beta.real,
          -ai * ME * LON0 + ar * MN * LAT0 + beta.imag]


def geo2px(lon, lat):
    w_ = alpha * complex((lon - LON0) * ME, -(lat - LAT0) * MN) + beta
    return w_.real, w_.imag


def geo2px_arr(lon, lat):
    e = (np.asarray(lon) - LON0) * ME; n = (np.asarray(lat) - LAT0) * MN
    return ar * e + ai * n + beta.real, ai * e - ar * n + beta.imag


centroids = {c: props[str(c)]['centroid'] for c in range(1, N + 1)}
adj = collections.defaultdict(set)
for e in edges:
    if e['boundary_px'] >= 4:
        adj[e['a']].add(e['b']); adj[e['b']].add(e['a'])

# ---------------- 1. special cells ----------------
SEINE = [(2.2875, 48.8560), (2.2930, 48.8595), (2.3000, 48.8630), (2.3080, 48.8635),
         (2.3160, 48.8625), (2.3260, 48.8605), (2.3330, 48.8590), (2.3400, 48.8575), (2.3435, 48.8570)]
NORTH_ARM = [(2.3435, 48.8570), (2.3470, 48.8578), (2.3510, 48.8568), (2.3550, 48.8555),
             (2.3585, 48.8542), (2.3620, 48.8500)]
SOUTH_ARM = [(2.3435, 48.8570), (2.3460, 48.8545), (2.3500, 48.8532), (2.3540, 48.8520),
             (2.3580, 48.8512), (2.3620, 48.8500)]
EAST = [(2.3620, 48.8500), (2.3650, 48.8470), (2.3700, 48.8440), (2.3760, 48.8400), (2.3820, 48.8360)]
ARSENAL = [(2.3670, 48.8520), (2.3676, 48.8505), (2.3684, 48.8488)]


def sample_polyline(pts_geo, step=15):
    pts = [geo2px(*p) for p in pts_geo]
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(np.hypot(x1 - x0, y1 - y0) / step))
        for t in np.linspace(0, 1, n):
            x, y = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            if 0 <= x < W and 0 <= y < H:
                out.append((int(x), int(y)))
    return out


water_votes = collections.Counter()
for pl in (SEINE, NORTH_ARM, SOUTH_ARM, EAST, ARSENAL):
    for x, y in sample_polyline(pl):
        water_votes[int(part[y, x])] += 1
water = {L for L, v in water_votes.items() if v >= 3 and props[str(L)]['part_area'] > 15000}

EXTERIOR = {int(part[2600, 50]), int(part[2600, W - 50])}   # giant west/east margins

CITE = Polygon([geo2px(*p) for p in [(2.3392, 48.8568), (2.3435, 48.8582), (2.3495, 48.8574),
                                     (2.3535, 48.8553), (2.3512, 48.8532), (2.3450, 48.8527), (2.3398, 48.8551)]])
STL = Polygon([geo2px(*p) for p in [(2.3505, 48.8532), (2.3560, 48.8540), (2.3630, 48.8514),
                                    (2.3612, 48.8492), (2.3545, 48.8496), (2.3502, 48.8514)]])
island_cite, island_stl, bridges = set(), set(), set()
for cell in range(1, N + 1):
    if cell in water or cell in EXTERIOR:
        continue
    p = Point(*centroids[cell])
    if CITE.contains(p):
        island_cite.add(cell); continue
    if STL.contains(p):
        island_stl.add(cell); continue
    if len(adj[cell] & water) >= 2 and props[str(cell)]['part_area'] < 80000:
        bridges.add(cell)
json.dump({'water': sorted(water), 'exterior': sorted(EXTERIOR), 'bridges': sorted(bridges),
           'ile_cite': sorted(island_cite), 'ile_st_louis': sorted(island_stl)},
          open(CKPT / 'special_cells.json', 'w'))
print(f'water {len(water)} | bridges {len(bridges)} | cite {len(island_cite)} | st-louis {len(island_stl)}')

# ---------------- 2. L1 macro geography ----------------
blocked = water | bridges | island_cite | island_stl
comp = {}
for start in range(1, N + 1):
    if start in comp or start in blocked:
        continue
    stack = [start]; comp[start] = start
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in comp and v not in blocked:
                comp[v] = start; stack.append(v)
rb_root = comp.get(int(part[int(geo2px(2.33, 48.868)[1]), int(geo2px(2.33, 48.868)[0])]))
lb_root = comp.get(int(part[int(geo2px(2.335, 48.8535)[1]), int(geo2px(2.335, 48.8535)[0])]))

arrj = json.load(open(SOURCES / 'arrondissements.geojson'))
city = unary_union([affine_transform(shape(f['geometry']), PARAMS) for f in arrj['features']]).buffer(40)
l1 = {}
for cell in range(1, N + 1):
    if cell in water: l1[cell] = 'seine'
    elif cell in island_cite: l1[cell] = 'ile_de_la_cite'
    elif cell in island_stl: l1[cell] = 'ile_saint_louis'
    elif cell in bridges: l1[cell] = 'bridge'
    elif not city.contains(Point(*centroids[cell])): l1[cell] = 'exterior'
    elif comp.get(cell) == rb_root: l1[cell] = 'right_bank'
    elif comp.get(cell) == lb_root: l1[cell] = 'left_bank'
    else: l1[cell] = 'pocket'
print('L1:', dict(collections.Counter(l1.values()).most_common()))

# ---------------- 3. L2 / L3 administrative ----------------
arr_polys = [(int(f['properties']['c_ar']), affine_transform(shape(f['geometry']), PARAMS))
             for f in arrj['features']]
qj = json.load(open(SOURCES / 'quartiers.geojson'))
q_polys = [(int(f['properties']['c_qu']), affine_transform(shape(f['geometry']), PARAMS))
           for f in qj['features']]
l2, l3 = {}, {}
for cell in range(1, N + 1):
    p = Point(*centroids[cell])
    l2[cell] = 0; l3[cell] = 0
    if l1[cell] == 'exterior':
        continue
    for c_ar, poly in arr_polys:
        if poly.contains(p): l2[cell] = c_ar; break
    for c_qu, poly in q_polys:
        if poly.contains(p): l3[cell] = c_qu; break
json.dump({'l1': {str(k): v for k, v in l1.items()},
           'l2': {str(k): v for k, v in l2.items()},
           'l3': {str(k): v for k, v in l3.items()}}, open(CKPT / 'levels_l123.json', 'w'))
json.dump({'quartiers': {str(int(f['properties']['c_qu'])): f['properties']['l_qu'] for f in qj['features']},
           'arrondissements': {str(int(f['properties']['c_ar'])): f['properties']['l_aroff'] for f in arrj['features']}},
          open(CKPT / 'admin_names.json', 'w'))

# ---------------- 4. L4 semantic units ----------------
d = json.load(open(SOURCES / 'parks.json'))
byname = collections.defaultdict(list)
for way in d['elements']:
    if way['type'] != 'way':
        continue
    geom = way.get('geometry', [])
    if len(geom) < 4 or geom[0] != geom[-1]:
        continue
    poly = Polygon([geo2px(p['lon'], p['lat']) for p in geom])
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area < 56000:      # >= 1 ha
        continue
    name = way.get('tags', {}).get('name')
    if not name:
        continue
    byname[(name, way.get('tags', {}).get('landuse') == 'cemetery')].append(poly)
parks = []
for (name, cem), polys in byname.items():
    u = unary_union(polys)
    if u.area < 56000:
        continue
    cells = [c for c in range(1, N + 1) if u.contains(Point(*centroids[c]))]
    if cells:
        parks.append((name, 'cemetery' if cem else 'park', cells))

dr = json.load(open(SOURCES / 'rail.json'))
rail_votes = collections.Counter()
for way in dr['elements']:
    if way['type'] != 'way' or way.get('tags', {}).get('tunnel') in ('yes', 'building_passage', 'covered'):
        continue
    pts = [geo2px(p['lon'], p['lat']) for p in way['geometry']]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(np.hypot(x1 - x0, y1 - y0) / 20))
        for t in np.linspace(0, 1, n):
            x, y = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            if 0 <= x < W and 0 <= y < H:
                rail_votes[int(part[int(y), int(x)])] += 1
rail_cells = {c for c, v in rail_votes.items() if v >= 8 and c not in (water | EXTERIOR) and c != 0}
adjr = collections.defaultdict(set)
for e in edges:
    if e['a'] in rail_cells and e['b'] in rail_cells:
        adjr[e['a']].add(e['b']); adjr[e['b']].add(e['a'])
seen, corridors = set(), []
for c in sorted(rail_cells):
    if c in seen:
        continue
    stack, grp = [c], []; seen.add(c)
    while stack:
        u = stack.pop(); grp.append(u)
        for v in adjr[u]:
            if v not in seen:
                seen.add(v); stack.append(v)
    if len(grp) >= 2:
        corridors.append(sorted(grp))

PLAZAS = {
    'Place Charles-de-Gaulle (Etoile)': (2.295028, 48.873792),
    'Place de la Concorde': (2.321475, 48.865633),
    'Place Vendome': (2.329420, 48.867320),
    'Place des Victoires': (2.341000, 48.865700),
    'Place de la Bastille': (2.369030, 48.853160),
    'Place de la Nation': (2.395890, 48.848422),
    'Place de la Republique': (2.363800, 48.867500),
    'Place du Chatelet': (2.347180, 48.857610),
    "Place de l'Hotel-de-Ville": (2.351400, 48.856400),
    'Place des Vosges': (2.365750, 48.855570),
    'Rond-point des Champs-Elysees': (2.312800, 48.869000),
    "Place de l'Opera": (2.331800, 48.870600),
}
plazas = []
for name, (lon, lat) in PLAZAS.items():
    x, y = geo2px(lon, lat)
    if 0 <= x < W and 0 <= y < H:
        c = int(part[int(y), int(x)])
        if c > 0:
            plazas.append((name, 'plaza', [c]))
json.dump({'parks': parks, 'rail': corridors, 'plazas': plazas}, open(CKPT / 'units_L4.json', 'w'))
print(f'parks {len(parks)} | rail corridors {len(corridors)} | plazas {len(plazas)}')

# ---------------- 5. L5 superblocks ----------------
cutS = np.zeros((H, W), np.uint8)
ds = json.load(open(SOURCES / 'secondary_roads.json'))
for way in ds['elements']:
    if way['type'] != 'way':
        continue
    lons = [p['lon'] for p in way['geometry']]; lats = [p['lat'] for p in way['geometry']]
    xs, ys = geo2px_arr(lons, lats)
    pts = np.stack([xs, ys], 1)
    if not ((pts[:, 0] > -500) & (pts[:, 0] < W + 500) & (pts[:, 1] > -500) & (pts[:, 1] < H + 500)).any():
        continue
    cv2.polylines(cutS, [pts.astype(np.int32)], False, 1, 1)
cutS = cv2.dilate(cutS, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
cutM = np.load(WORK / 'cutmask_major.npy')
cut = ((cutM > 0) | (cutS > 0)).astype(np.uint8)
np.save(WORK / 'cutmask_all.npy', cut)

acc_cut = collections.defaultdict(float); acc_cnt = collections.Counter()
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
        lo = np.minimum(A_[m], B_[m]).astype(np.int64)
        hi = np.maximum(A_[m], B_[m]).astype(np.int64)
        packed = lo * (N + 1) + hi
        u, inv = np.unique(packed, return_inverse=True)
        cnt = np.bincount(inv); sc = np.bincount(inv, weights=CA[m].astype(np.float64))
        for k_, c1, s1 in zip(u, cnt, sc):
            acc_cut[k_] += s1; acc_cnt[k_] += int(c1)
cutfrac = {k_: acc_cut[k_] / acc_cnt[k_] for k_ in acc_cnt}

island = island_cite | island_stl
mergeable = lambda c: c not in water and c not in EXTERIOR and c not in bridges
parent = list(range(N + 1))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x


for e in edges:
    i, j = e['a'], e['b']
    if not (mergeable(i) and mergeable(j)) or e['boundary_px'] < 8:
        continue
    if (i in island) != (j in island):
        continue
    k_ = min(i, j) * (N + 1) + max(i, j)
    if cutfrac.get(k_, 0) > 0.55:
        continue
    ri, rj = find(i), find(j)
    if ri != rj:
        parent[ri] = rj

comps = collections.defaultdict(list)
for L in range(1, N + 1):
    if mergeable(L):
        comps[find(L)].append(L)
areas = {k: sum(props[str(m)]['part_area'] for m in v) for k, v in comps.items()}
comp_of = {L: find(L) for L in range(1, N + 1) if mergeable(L)}
kind = {k: ('island' if v[0] in island else 'bank') for k, v in comps.items()}
blen = collections.Counter()
for e in edges:
    i, j = e['a'], e['b']
    if i in comp_of and j in comp_of:
        ci, cj = comp_of[i], comp_of[j]
        if ci != cj and kind[ci] == kind[cj]:
            blen[(min(ci, cj), max(ci, cj))] += e['boundary_px']
MIN_AREA = int(2.5e4 / (0.4219 ** 2))
changed, it = True, 0
while changed and it < 60:
    changed = False; it += 1
    for c in [c for c, a_ in list(areas.items()) if a_ < MIN_AREA]:
        best, bl = None, 0
        for (x_, y_), l_ in blen.items():
            if x_ == c and y_ in areas and l_ > bl: best, bl = y_, l_
            elif y_ == c and x_ in areas and l_ > bl: best, bl = x_, l_
        if best is None:
            continue
        areas[best] += areas.pop(c); comps[best].extend(comps.pop(c))
        nb = collections.Counter()
        for (x_, y_), l_ in blen.items():
            if c in (x_, y_):
                o = y_ if x_ == c else x_
                if o != best and o in areas:
                    nb[(min(best, o), max(best, o))] += l_
        blen = collections.Counter({k_: v for k_, v in blen.items() if c not in k_})
        blen.update(nb); changed = True
json.dump({str(k): v for k, v in comps.items()}, open(CKPT / 'superblocks_L5.json', 'w'))
print(f'L5: {len(comps)} raw superblock components')
