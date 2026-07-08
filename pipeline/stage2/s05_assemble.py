"""Stage 2 / step 05 — assemble label metadata (as run 2026-07-08; paths adapted)."""
import numpy as np, json, collections, re, unicodedata

from _paths import CKPT, WORK, OUT as OUTP, MASTER
SC = str(CKPT)
OUT = str(OUTP)
M_PER_PX = 0.4219

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]

part = np.load(WORK / 'partition_L6.npy')
H, W = part.shape; N = 2560
props = json.load(open(f'{SC}/props_L6.json'))
edges = json.load(open(f'{SC}/edges_L6_v2.json'))
special = json.load(open(f'{SC}/special_cells.json'))
levels = json.load(open(f'{SC}/levels_l123.json'))
u4 = json.load(open(f'{SC}/units_L4.json'))
sb = json.load(open(f'{SC}/superblocks_L5.json'))
admin = json.load(open(f'{SC}/admin_names.json'))
g = json.load(open(f'{SC}/georef_final.json'))
alpha = complex(*g['alpha']); beta = complex(*g['beta'])
LON0, LAT0, ME, MN = g['lon0'], g['lat0'], g['me'], g['mn']

def px2geo(x, y):
    z = (complex(x, y) - beta)/alpha
    return round(z.real/ME + LON0, 6), round(-z.imag/MN + LAT0, 6)

water = set(special['water']); exterior = set(special['exterior'])
bridges = set(special['bridges']); cite = set(special['ile_cite']); stl = set(special['ile_st_louis'])
l1 = {int(k): v for k, v in levels['l1'].items()}
l2 = {int(k): v for k, v in levels['l2'].items()}
l3 = {int(k): v for k, v in levels['l3'].items()}

# ---------- L5 unit table ----------
sb_items = sorted(sb.items(), key=lambda kv: -sum(props[str(m)]['part_area'] for m in kv[1]))
cell2unit5 = {}
units5 = {}   # uid -> dict
sid = 0
for root, members in sb_items:
    sid += 1
    uid = f'L5_sb{sid:03d}'
    for m in members: cell2unit5[m] = uid
    units5[uid] = dict(type='superblock', cells=members)
# seine corridor: water + bridges (+ pockets adjacent only to water/bridges)
seine_members = sorted(water | bridges)
pockets = [c for c in range(1, N+1) if l1[c] == 'pocket']
adjmap = collections.defaultdict(set)
for e in edges: adjmap[e['a']].add(e['b']); adjmap[e['b']].add(e['a'])
for c in pockets:
    if adjmap[c] and adjmap[c] <= (water | bridges | set(pockets)):
        seine_members.append(c)
seine_members = sorted(set(seine_members))
units5['L5_seine_corridor'] = dict(type='seine_corridor', cells=seine_members)
for m in seine_members:
    prev = cell2unit5.get(m)
    if prev and prev != 'L5_seine_corridor':
        units5[prev]['cells'] = [c for c in units5[prev]['cells'] if c != m]
    cell2unit5[m] = 'L5_seine_corridor'
# drop superblocks emptied by the corridor adoption
units5 = {k: v for k, v in units5.items() if v['cells']}
units5['L5_exterior_west'] = dict(type='exterior', cells=[1]); cell2unit5[1] = 'L5_exterior_west'
units5['L5_exterior_east'] = dict(type='exterior', cells=[95]); cell2unit5[95] = 'L5_exterior_east'
for c in range(1, N+1):
    if c not in cell2unit5:
        uid = f'L5_orphan_{c}'
        units5[uid] = dict(type='orphan', cells=[c]); cell2unit5[c] = uid

# ---------- L4 unit table ----------
cell2unit4 = {}
units4 = {}
for name, typ, cells in u4['parks']:
    uid = f'L4_{typ}_{slug(name)}'
    units4[uid] = dict(type=typ, name=name, cells=cells)
    for c in cells: cell2unit4.setdefault(c, uid)
for i, cells in enumerate(u4['rail'], 1):
    uid = f'L4_rail_{i}'
    units4[uid] = dict(type='rail', name=f'Rail corridor {i}', cells=cells)
    for c in cells: cell2unit4.setdefault(c, uid)
for name, typ, cells in u4['plazas']:
    uid = f'L4_plaza_{slug(name)}'
    units4[uid] = dict(type='plaza', name=name, cells=cells)
    for c in cells: cell2unit4.setdefault(c, uid)
units4['L4_island_ile_de_la_cite'] = dict(type='island', name='Île de la Cité', cells=sorted(cite))
units4['L4_island_ile_saint_louis'] = dict(type='island', name='Île Saint-Louis', cells=sorted(stl))
for c in cite: cell2unit4.setdefault(c, 'L4_island_ile_de_la_cite')
for c in stl: cell2unit4.setdefault(c, 'L4_island_ile_saint_louis')
units4['L4_water_seine'] = dict(type='water', name='La Seine + Bassin de l\'Arsenal', cells=sorted(water))
for c in water: cell2unit4.setdefault(c, 'L4_water_seine')
units4['L4_bridges'] = dict(type='bridge', name='Seine bridges (decks)', cells=sorted(bridges))
for c in bridges: cell2unit4.setdefault(c, 'L4_bridges')

# ---------- helper: aggregate unit geometry ----------
def unit_geom(cells):
    A = sum(props[str(c)]['part_area'] for c in cells)
    cx = sum(props[str(c)]['centroid'][0]*props[str(c)]['part_area'] for c in cells)/A
    cy = sum(props[str(c)]['centroid'][1]*props[str(c)]['part_area'] for c in cells)/A
    bx0 = min(props[str(c)]['bbox'][0] for c in cells); by0 = min(props[str(c)]['bbox'][1] for c in cells)
    bx1 = max(props[str(c)]['bbox'][2] for c in cells); by1 = max(props[str(c)]['bbox'][3] for c in cells)
    return A, (round(cx,1), round(cy,1)), (bx0, by0, bx1, by1)

# ---------- adjacency aggregation ----------
def aggregate_adj(cell2unit):
    agg = collections.Counter()
    for e in edges:
        ua, ub = cell2unit.get(e['a']), cell2unit.get(e['b'])
        if ua and ub and ua != ub:
            agg[(min(ua,ub), max(ua,ub))] += e['boundary_px']
    nb = collections.defaultdict(dict)
    for (ua, ub), l_ in agg.items():
        nb[ua][ub] = int(l_); nb[ub][ua] = int(l_)
    return nb

# L1 mapping
cell2unit1 = {c: f'L1_{l1[c]}' if l1[c] not in ('exterior',) else
              ('L1_exterior_west' if c == 1 else 'L1_exterior_east') for c in range(1, N+1)}
# L2/L3 mapping (0 = outside)
cell2unit2 = {c: (f'L2_arr{l2[c]:02d}' if l2[c] > 0 else 'L2_outside') for c in range(1, N+1)}
cell2unit3 = {c: (f'L3_q{l3[c]:02d}' if l3[c] > 0 else 'L3_outside') for c in range(1, N+1)}

REG = {}   # all regions all levels
def emit(uid, level, typ, cells, name=None, parent=None, extra=None):
    A, cen, bbox = unit_geom(cells)
    lon, lat = px2geo(*cen)
    rec = dict(id=uid, level=level, type=typ, name=name,
               area_px=int(A), area_m2=round(A*M_PER_PX**2, 1),
               centroid_px=list(cen), centroid_lonlat=[lon, lat],
               bbox_px=list(bbox), n_cells=len(cells), parent=parent)
    if extra: rec.update(extra)
    if level >= 4 or level == -1: rec['cells'] = sorted(cells)
    REG[uid] = rec

# L0
emit('L0_canvas', 0, 'canvas', list(range(1, N+1)), name='Diem band — Paris Centre 1:5000')

# L1
for cls, cells in [(k, [c for c in range(1, N+1) if cell2unit1[c] == k])
                   for k in sorted(set(cell2unit1.values()))]:
    if not cells: continue
    nm = {'L1_right_bank': 'Rive Droite', 'L1_left_bank': 'Rive Gauche', 'L1_seine': 'La Seine',
          'L1_ile_de_la_cite': 'Île de la Cité', 'L1_ile_saint_louis': 'Île Saint-Louis',
          'L1_bridge': 'Ponts (bridge decks)', 'L1_pocket': 'Enclosed pockets',
          'L1_exterior_west': 'Exterior margin W', 'L1_exterior_east': 'Exterior margin E'}.get(cls, cls)
    emit(cls, 1, cls.replace('L1_',''), cells, name=nm, parent='L0_canvas')

# L2
for k in sorted(set(cell2unit2.values())):
    cells = [c for c in range(1, N+1) if cell2unit2[c] == k]
    if not cells: continue
    if k == 'L2_outside':
        emit(k, 2, 'outside', cells, name='Outside Paris limits', parent='L0_canvas'); continue
    code = int(k[-2:])
    bank = 'L1_left_bank' if code in (5,6,7,13,14,15) else 'L1_right_bank'
    if code in (1, 4):  # islands belong partly; parent by majority bank anyway
        pass
    emit(k, 2, 'arrondissement', cells, name=f'{code}e — {admin["arrondissements"][str(code)]}',
         parent=bank, extra=dict(insee=75100+code))

# L3
q2arr = {}
qj_names = admin['quartiers']
for k in sorted(set(cell2unit3.values())):
    cells = [c for c in range(1, N+1) if cell2unit3[c] == k]
    if not cells: continue
    if k == 'L3_outside':
        emit(k, 3, 'outside', cells, name='Outside Paris limits', parent='L2_outside'); continue
    code = int(k[-2:])
    arr = (code + 3)//4
    emit(k, 3, 'quartier', cells, name=qj_names[str(code)], parent=f'L2_arr{arr:02d}')

# L4
for uid, u in units4.items():
    par = 'L1_seine' if u['type'] in ('water', 'bridge') else None
    if par is None:
        b = collections.Counter(cell2unit1[c] for c in u['cells'])
        par = b.most_common(1)[0][0]
    emit(uid, 4, u['type'], u['cells'], name=u.get('name'), parent=par)

# L5 (parent = dominant quartier; purity recorded)
for uid, u in units5.items():
    cnt = collections.Counter(cell2unit3[c] for c in u['cells'])
    dom, domn = cnt.most_common(1)[0]
    purity = domn/len(u['cells'])
    emit(uid, 5, u['type'], u['cells'], parent=dom if u['type']=='superblock' else 'L0_canvas',
         extra=dict(quartier_purity=round(purity, 3)))

# L6 cells
adj_l6 = collections.defaultdict(dict)
for e in edges:
    adj_l6[e['a']][e['b']] = e['boundary_px']; adj_l6[e['b']][e['a']] = e['boundary_px']
cells6 = {}
for c in range(1, N+1):
    p = props[str(c)]
    lon, lat = px2geo(*p['centroid'])
    cells6[f'L6_c{c:04d}'] = dict(
        id=f'L6_c{c:04d}', level=6, type=l1[c] if l1[c] in
            ('seine','bridge','exterior','pocket') else 'block',
        area_px=p['part_area'], open_area_px=p['white_area'],
        area_m2=round(p['part_area']*M_PER_PX**2, 1),
        centroid_px=p['centroid'], centroid_lonlat=[lon, lat],
        bbox_px=p['bbox'],
        parent=cell2unit5[c], l1=cell2unit1[c], l2=cell2unit2[c], l3=cell2unit3[c],
        l4=cell2unit4.get(c),
        neighbors={f'L6_c{n:04d}': int(l_) for n, l_ in sorted(adj_l6[c].items())})

# neighbors for levels 1-5
for lvl, c2u in ((1, cell2unit1), (2, cell2unit2), (3, cell2unit3), (4, cell2unit4), (5, cell2unit5)):
    nb = aggregate_adj(c2u)
    for uid, nbrs in nb.items():
        if uid in REG: REG[uid]['neighbors'] = dict(sorted(nbrs.items()))

json.dump(REG, open(f'{OUT}/meta/regions_L0_L5.json', 'w'), ensure_ascii=False, indent=1)
json.dump(cells6, open(f'{OUT}/meta/cells_L6.json', 'w'), ensure_ascii=False)
json.dump(dict(georef=g, m_per_px=M_PER_PX, canvas=[W, H],
               note='similarity transform lon/lat->px; see georef fields'),
          open(f'{OUT}/meta/georeference.json', 'w'), indent=1)

# save cell->unit lookup tables for mask rendering
json.dump({'l1': {str(k): v for k, v in cell2unit1.items()},
           'l2': {str(k): v for k, v in cell2unit2.items()},
           'l3': {str(k): v for k, v in cell2unit3.items()},
           'l4': {str(k): v for k, v in cell2unit4.items()},
           'l5': {str(k): v for k, v in cell2unit5.items()}},
          open(f'{SC}/cell2unit.json', 'w'))
print('regions:', len(REG), '| L6 cells:', len(cells6))
lv = collections.Counter(r['level'] for r in REG.values())
print('per level:', dict(sorted(lv.items())))
