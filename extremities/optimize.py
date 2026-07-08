#!/usr/bin/env python3
"""
Convex Partition Optimizer
==========================
Optimizes the positions of movable vertices in a hexagonal tiling so that
each convex region's pixel area matches a target proportion derived from
real-world French administrative region surfaces.

Two panels share a zigzag boundary:
  - LEFT  panel (5088×5312): Bretagne, Normandie, Pays de la Loire,
    Centre-Val de Loire, Nouvelle-Aquitaine, Occitanie
  - RIGHT panel (6000×5312): Hauts-de-France, Grand Est, Auvergne-Rhône-Alpes,
    Bourgogne-Franche-Comté, PACA, Corse

Usage:
    python optimize.py left
    python optimize.py right
    python optimize.py both
"""

import argparse, json, math, os, shutil, sys
import numpy as np
from scipy.optimize import minimize
from PIL import Image, ImageDraw, ImageFont
import imageio

# ═════════════════════════════════════════════════════════════════════════════
# PANEL DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

PANELS = {}

# ── Left panel ──────────────────────────────────────────────────────────────
PANELS['left'] = {
    'canvas': (5088, 5312),
    'fixed': {
        'Q0': (4707, 0), 'Q1': (4078, 1531), 'Q2': (4118, 2481),
        'Q3': (3741, 3547), 'Q4': (3408, 5311),
    },
    'corners': {'TL': (0, 0), 'BL': (0, 5311)},
    'movable_start': {
        'P1': (2212, 0), 'P2': (2619, 1518), 'P3': (0, 1592),
        'P4': (1777, 2038), 'P5': (0, 3814), 'P6': (2197, 3202),
        'P7': (1960, 5311), 'P8': (1269, 3800),
    },
    'edge_constraints': {
        'P1': ('x', 0),     # y=0, x varies
        'P3': ('y', 0),     # x=0, y varies
        'P5': ('y', 0),     # x=0, y varies
        'P7': ('x', 5311),  # y=5311, x varies
    },
    'regions': [
        ('Bretagne',            ['TL','P3','P4','P2','P1'],        27207.9),
        ('Normandie',           ['P1','P2','Q1','Q0'],             29875.1),
        ('Pays de la Loire',    ['P3','P5','P8','P6','P4'],        32081.8),
        ('Centre-Val de Loire', ['P4','P6','Q3','Q2','Q1','P2'],   39150.9),
        ('Nouvelle-Aquitaine',  ['P8','P5','BL','P7'],             84035.7),
        ('Occitanie',           ['P8','P7','Q4','Q3','P6'],        72723.6),
    ],
    'fixed_chain': ['Q0','Q1','Q2','Q3','Q4'],  # for drawing
    'chain_side': 'right',
    'mask_names': ['bretagne','normandie','pays_de_la_loire',
                   'centre_val_de_loire','nouvelle_aquitaine','occitanie'],
    'short_names': ['BRE','NOR','PdL','CVL','NAQ','OCC'],
}

# ── Right panel ─────────────────────────────────────────────────────────────
PANELS['right'] = {
    'canvas': (6000, 5312),
    'fixed': {
        'P0': (124, 0), 'P0b': (187, 458), 'P7': (836, 1523),
        'P9': (758, 2358), 'P11': (1370, 3674), 'P4': (1479, 5311),
    },
    'corners': {'TR': (6000, 0), 'BR': (6000, 5312)},
    'movable_start': {
        'P1': (3600, 0), 'P6': (3268, 1236), 'P8': (3704, 1864),
        'P10': (3012, 3197), 'P12': (4116, 4092), 'P2': (5999, 2324),
        'P3': (5999, 3683), 'P5': (3848, 5311),
    },
    'edge_constraints': {
        'P1': ('x', 0),      # y=0
        'P2': ('y', 5999),   # x=5999
        'P3': ('y', 5999),   # x=5999
        'P5': ('x', 5311),   # y=5311
    },
    'regions': [
        ('Hauts-de-France',         ['P0','P0b','P7','P6','P1'],        12.9),
        ('Grand Est',               ['P1','P6','P8','P2','TR'],         23.3),
        ('Auvergne-Rhône-Alpes',    ['P6','P7','P9','P11','P10','P8'],  28.2),
        ('Bourgogne-Franche-Comté', ['P8','P10','P12','P3','P2'],       19.4),
        ('PACA',                    ['P11','P4','P5','P12','P10'],       12.7),
        ('Corse',                   ['P12','P5','BR','P3'],              3.5),
    ],
    'fixed_chain': ['P0','P0b','P7','P9','P11','P4'],
    'chain_side': 'left',
    'mask_names': ['hauts_de_france','grand_est','auvergne_rhone_alpes',
                   'bourgogne_franche_comte','paca','corse'],
    'short_names': ['HdF','GE','ARA','BFC','PACA','Cor'],
}


# ═════════════════════════════════════════════════════════════════════════════
# GEOMETRY ENGINE
# ═════════════════════════════════════════════════════════════════════════════

MAX_ANGLE = 155.0
MIN_ANGLE = 25.0
MARGIN = 50

def shoelace(poly):
    """Polygon area via shoelace formula."""
    n = len(poly)
    a = sum(poly[i][0]*poly[(i+1)%n][1] - poly[(i+1)%n][0]*poly[i][1]
            for i in range(n))
    return abs(a) / 2.0

def is_convex(poly):
    """Check convexity via cross-product sign consistency."""
    n = len(poly)
    sign = None
    for i in range(n):
        p0, p1, p2 = poly[i], poly[(i+1)%n], poly[(i+2)%n]
        cross = (p1[0]-p0[0])*(p2[1]-p1[1]) - (p1[1]-p0[1])*(p2[0]-p1[0])
        if abs(cross) < 1e-10:
            continue
        if sign is None:
            sign = cross > 0
        elif (cross > 0) != sign:
            return False
    return True

def interior_angles(poly):
    """Compute interior angles in degrees for each vertex."""
    n = len(poly)
    angles = []
    for i in range(n):
        A = np.array(poly[(i-1)%n], dtype=float)
        B = np.array(poly[i], dtype=float)
        C = np.array(poly[(i+1)%n], dtype=float)
        ba, bc = A - B, C - B
        nba, nbc = np.linalg.norm(ba), np.linalg.norm(bc)
        if nba < 1e-10 or nbc < 1e-10:
            angles.append(180.0)
            continue
        cos_a = np.clip(np.dot(ba, bc) / (nba * nbc), -1, 1)
        angles.append(math.degrees(math.acos(cos_a)))
    return angles


# ═════════════════════════════════════════════════════════════════════════════
# OPTIMIZER
# ═════════════════════════════════════════════════════════════════════════════

class PanelOptimizer:
    """Handles packing/unpacking, objective, and optimization for one panel."""

    def __init__(self, panel_key):
        self.cfg = PANELS[panel_key]
        self.W, self.H = self.cfg['canvas']
        self.regions = self.cfg['regions']
        total = sum(r[2] for r in self.regions)
        self.targets = [r[2] / total for r in self.regions]
        self.immovable = set(self.cfg['fixed'].keys()) | set(self.cfg['corners'].keys())

        # Build pack/unpack maps
        self._build_variable_map()

        self.history = []  # ALL states from callbacks (for smooth GIF)

    def _build_variable_map(self):
        """Build the mapping from movable points to flat optimization vector."""
        self.var_indices = {}  # point_key -> (start_idx, n_vars, constraint_info)
        idx = 0
        ec = self.cfg['edge_constraints']
        self._var_count = 0

        # Sorted for deterministic order
        for k in sorted(self.cfg['movable_start'].keys()):
            if k in ec:
                axis, fixed_val = ec[k]
                if axis == 'x':  # y is fixed, x varies
                    self.var_indices[k] = (idx, 1, ('x_free', fixed_val))
                    idx += 1
                else:  # x is fixed, y varies
                    self.var_indices[k] = (idx, 1, ('y_free', fixed_val))
                    idx += 1
            else:
                self.var_indices[k] = (idx, 2, ('free',))
                idx += 2
        self._var_count = idx

    def pack(self, pts):
        v = np.zeros(self._var_count)
        for k, (i, n, info) in self.var_indices.items():
            if n == 1:
                if info[0] == 'x_free':
                    v[i] = pts[k][0]
                else:
                    v[i] = pts[k][1]
            else:
                v[i] = pts[k][0]
                v[i+1] = pts[k][1]
        return v

    def unpack(self, v):
        pts = {}
        ec = self.cfg['edge_constraints']
        for k, (i, n, info) in self.var_indices.items():
            if n == 1:
                if info[0] == 'x_free':
                    pts[k] = (v[i], info[1])
                else:
                    pts[k] = (info[1], v[i])
            else:
                pts[k] = (v[i], v[i+1])
        return pts

    def bounds(self):
        b = []
        for k in sorted(self.cfg['movable_start'].keys()):
            _, n, info = self.var_indices[k]
            if n == 1:
                if info[0] == 'x_free':
                    b.append((MARGIN, self.W - MARGIN))
                else:
                    b.append((MARGIN, self.H - MARGIN))
            else:
                b.append((MARGIN, self.W - MARGIN))
                b.append((MARGIN, self.H - MARGIN))
        return b

    def all_points(self, movable):
        pts = dict(self.cfg['fixed'])
        pts.update(self.cfg['corners'])
        pts.update(movable)
        return pts

    def fractions(self, movable):
        pts = self.all_points(movable)
        areas = [shoelace([pts[k] for k in verts]) for _, verts, _ in self.regions]
        t = sum(areas)
        return ([a/t for a in areas] if t > 1e-10 else [1.0/len(self.regions)]*len(self.regions)), areas

    def objective(self, v):
        mov = self.unpack(v)
        pts = self.all_points(mov)
        penalty = 0.0

        for _, verts, _ in self.regions:
            poly = [pts[k] for k in verts]
            n = len(verts)

            if not is_convex(poly):
                penalty += 1000.0

            angles = interior_angles(poly)
            for i, ang in enumerate(angles):
                triplet = {verts[(i-1)%n], verts[i], verts[(i+1)%n]}
                if triplet <= self.immovable:  # all three immovable
                    continue
                if ang > MAX_ANGLE:
                    penalty += 2.0 * ((ang - MAX_ANGLE) / 5.0) ** 2
                if ang < MIN_ANGLE:
                    penalty += 2.0 * ((MIN_ANGLE - ang) / 5.0) ** 2

        fr, _ = self.fractions(mov)
        err = sum(((f - t) / t) ** 2 for f, t in zip(fr, self.targets))
        return err + penalty

    def optimize(self):
        """Multi-phase optimization with dense history recording."""
        self.history = []
        v0 = self.pack(self.cfg['movable_start'])
        b = self.bounds()

        # Record EVERY callback for smooth animation
        def record(v):
            self.history.append(v.copy())

        # Also record start
        self.history.append(v0.copy())

        print("  Phase 1: L-BFGS-B ...")
        r1 = minimize(self.objective, v0, method='L-BFGS-B', bounds=b,
                       callback=record, options={'maxiter': 3000, 'ftol': 1e-15, 'gtol': 1e-12})
        print(f"    obj = {r1.fun:.10f}  ({len(self.history)} states)")

        print("  Phase 2: Nelder-Mead ...")
        r2 = minimize(self.objective, r1.x, method='Nelder-Mead',
                       callback=record, options={'maxiter': 20000, 'xatol': 0.01, 'fatol': 1e-15,
                                                  'adaptive': True})
        print(f"    obj = {r2.fun:.10f}  ({len(self.history)} states)")

        print("  Phase 3: L-BFGS-B polish ...")
        r3 = minimize(self.objective, r2.x, method='L-BFGS-B', bounds=b,
                       callback=record, options={'maxiter': 3000, 'ftol': 1e-15, 'gtol': 1e-12})
        print(f"    obj = {r3.fun:.10f}  ({len(self.history)} states)")

        best = r3
        for i in range(2):
            rn = minimize(self.objective, best.x, method='Nelder-Mead',
                           callback=record,
                           options={'maxiter': 20000, 'xatol': 0.001, 'fatol': 1e-16, 'adaptive': True})
            rl = minimize(self.objective, rn.x, method='L-BFGS-B', bounds=b,
                           callback=record,
                           options={'maxiter': 3000, 'ftol': 1e-16, 'gtol': 1e-13})
            if rl.fun < best.fun:
                best = rl
            print(f"    Extra pass {i+1}: obj = {best.fun:.12f}  ({len(self.history)} states)")

        # Append final
        self.history.append(best.x.copy())
        return best.x

    def print_report(self, final_v):
        """Print final fractions and angles."""
        mov = self.unpack(final_v)
        pts = self.all_points(mov)
        fr, areas = self.fractions(mov)

        print("\n  ┌─────────────────────────────────┬────────┬────────┬────────┐")
        print("  │ Region                          │ Target │ Actual │  Error │")
        print("  ├─────────────────────────────────┼────────┼────────┼────────┤")
        for i, (name, _, _) in enumerate(self.regions):
            err = abs(fr[i] - self.targets[i]) / self.targets[i] * 100
            print(f"  │ {name:31s} │ {self.targets[i]*100:5.1f}% │ {fr[i]*100:5.1f}% │ {err:5.2f}% │")
        print("  └─────────────────────────────────┴────────┴────────┴────────┘")

        print("\n  Angles (* = immutable triplet of fixed vertices):")
        for name, verts, _ in self.regions:
            poly = [pts[k] for k in verts]
            angles = interior_angles(poly)
            n = len(verts)
            parts = []
            for i, a in enumerate(angles):
                triplet = {verts[(i-1)%n], verts[i], verts[(i+1)%n]}
                star = "*" if triplet <= self.immovable else ""
                parts.append(f"{a:.0f}°{star}")
            print(f"    {name:31s}: {', '.join(parts)}  (max {max(angles):.0f}°)")


# ═════════════════════════════════════════════════════════════════════════════
# RENDERING
# ═════════════════════════════════════════════════════════════════════════════

PASTEL = [(173,216,230),(255,218,185),(144,238,144),(255,255,186),(221,160,221),(255,182,193)]

def get_font(size):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()


class PanelRenderer:
    """Renders frames, GIFs, masks, and final outputs for a panel."""

    def __init__(self, opt: PanelOptimizer, panel_key: str, output_dir: str):
        self.opt = opt
        self.cfg = opt.cfg
        self.W, self.H = opt.W, opt.H
        self.panel_key = panel_key
        self.odir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _draw_partition(self, draw, movable, lw=3, dr=15, show_dots=True):
        pts = self.opt.all_points(movable)
        for _, verts, _ in self.cfg['regions']:
            poly = [pts[k] for k in verts]
            for i in range(len(poly)):
                j = (i + 1) % len(poly)
                draw.line([tuple(map(int, poly[i])), tuple(map(int, poly[j]))],
                          fill='black', width=lw)
        # Fixed chain
        chain = self.cfg['fixed_chain']
        for i in range(len(chain) - 1):
            p1, p2 = pts[chain[i]], pts[chain[i+1]]
            draw.line([tuple(map(int, p1)), tuple(map(int, p2))], fill='black', width=lw)
        if show_dots:
            for k in self.cfg['fixed']:
                x, y = int(pts[k][0]), int(pts[k][1])
                draw.ellipse([x-dr, y-dr, x+dr, y+dr], fill='red')
            for k in self.cfg['movable_start']:
                if k in movable:
                    x, y = int(movable[k][0]), int(movable[k][1])
                    draw.ellipse([x-dr, y-dr, x+dr, y+dr], fill='grey')

    def generate_frames(self, final_v):
        """Generate step-by-step construction + optimization frames."""
        fdir = os.path.join(self.odir, 'frames')
        os.makedirs(fdir, exist_ok=True)
        paths = []
        idx = 0

        def save(img):
            nonlocal idx
            p = os.path.join(fdir, f'frame_{idx:03d}.png')
            img.save(p); paths.append(p); idx += 1

        # Frame 0: blank
        save(Image.new('RGB', (self.W, self.H), 'white'))

        # Fixed vertices one by one
        chain = self.cfg['fixed_chain']
        placed = []
        for k in chain:
            placed.append(k)
            img = Image.new('RGB', (self.W, self.H), 'white')
            d = ImageDraw.Draw(img)
            for i in range(len(placed) - 1):
                p1, p2 = self.cfg['fixed'][placed[i]], self.cfg['fixed'][placed[i+1]]
                d.line([tuple(map(int, p1)), tuple(map(int, p2))], fill='black', width=3)
            for pk in placed:
                x, y = self.cfg['fixed'][pk]
                d.ellipse([x-15, y-15, x+15, y+15], fill='red')
            save(img)

        # Movable vertices one by one
        mov_keys = sorted(self.cfg['movable_start'].keys())
        placed_m = []
        for k in mov_keys:
            placed_m.append(k)
            img = Image.new('RGB', (self.W, self.H), 'white')
            d = ImageDraw.Draw(img)
            for i in range(len(chain) - 1):
                p1, p2 = self.cfg['fixed'][chain[i]], self.cfg['fixed'][chain[i+1]]
                d.line([tuple(map(int, p1)), tuple(map(int, p2))], fill='black', width=3)
            for pk in chain:
                x, y = self.cfg['fixed'][pk]
                d.ellipse([x-15, y-15, x+15, y+15], fill='red')
            for pk in placed_m:
                x, y = int(self.cfg['movable_start'][pk][0]), int(self.cfg['movable_start'][pk][1])
                d.ellipse([x-15, y-15, x+15, y+15], fill='grey')
            save(img)

        n_construction = idx  # remember where construction ends

        # Starting partition (all edges)
        img = Image.new('RGB', (self.W, self.H), 'white')
        d = ImageDraw.Draw(img)
        self._draw_partition(d, self.cfg['movable_start'])
        save(img)

        # Optimization frames: select ~40 evenly spaced from full history
        hist = self.opt.history
        n_opt_frames = min(40, len(hist))
        if len(hist) > n_opt_frames:
            indices = np.linspace(0, len(hist) - 1, n_opt_frames, dtype=int)
            selected = [hist[i] for i in indices]
        else:
            selected = hist

        for v in selected:
            img = Image.new('RGB', (self.W, self.H), 'white')
            d = ImageDraw.Draw(img)
            self._draw_partition(d, self.opt.unpack(v))
            save(img)

        # Final frame
        img = Image.new('RGB', (self.W, self.H), 'white')
        d = ImageDraw.Draw(img)
        self._draw_partition(d, self.opt.unpack(final_v))
        save(img)

        print(f"    {idx} frames ({n_construction} construction + {idx - n_construction} optimization)")
        return paths, n_construction

    def make_simple_gif(self, paths, n_construction, out_path):
        """B&W GIF: slow construction, medium optimization, long hold on final."""
        sc = 4
        sw, sh = self.W // sc, self.H // sc
        imgs = [np.array(Image.open(p).resize((sw, sh), Image.LANCZOS)) for p in paths]
        durations = []
        for i in range(len(paths)):
            if i <= n_construction:
                durations.append(0.5)
            elif i == len(paths) - 1:
                durations.append(3.0)
            else:
                durations.append(0.12)
        imageio.mimsave(out_path, imgs, duration=durations, loop=0)
        print(f"    Saved {out_path}")

    def make_annotated_gif(self, final_v, out_path):
        """Colored GIF with live fractions, progress bar, and bar chart."""
        sc = 4
        sw, sh = self.W // sc, self.H // sc
        hdr, bar_h = 80, 120
        th = sh + hdr + bar_h
        fnt, fs, fh = get_font(14), get_font(11), get_font(16)
        short = self.cfg['short_names']

        # Build state sequence: start + subsampled history + final
        hist = self.opt.history
        states = [self.opt.pack(self.cfg['movable_start'])]
        n_anim = min(40, len(hist))
        if len(hist) > n_anim:
            states += [hist[i] for i in np.linspace(0, len(hist)-1, n_anim, dtype=int)]
        else:
            states += list(hist)
        states.append(final_v)

        frames = []
        for si, v in enumerate(states):
            mov = self.opt.unpack(v)
            pts = self.opt.all_points(mov)
            fr, _ = self.opt.fractions(mov)
            mx = max(abs(f-t)/t for f, t in zip(fr, self.opt.targets)) * 100
            prog = si / max(len(states)-1, 1)

            img = Image.new('RGB', (sw, th), 'white')
            d = ImageDraw.Draw(img)

            # Header
            d.rectangle([0, 0, sw, hdr], fill=(240, 240, 240))
            d.text((10, 8), f"Step {si}/{len(states)-1}", fill='black', font=fh)
            col = 'red' if mx > 1 else 'green'
            d.text((10, 30), f"Max error: {mx:.1f}%", fill=col, font=fnt)
            bw2 = sw - 20
            d.rectangle([10, 55, 10+bw2, 70], outline='grey')
            d.rectangle([10, 55, 10+int(bw2*prog), 70], fill=(70, 130, 180))

            # Filled regions
            for ri, (_, verts, _) in enumerate(self.cfg['regions']):
                poly = [(int(pts[k][0]/sc), int(pts[k][1]/sc)+hdr) for k in verts]
                d.polygon(poly, fill=PASTEL[ri], outline='black')

            # Labels
            for ri, (_, verts, _) in enumerate(self.cfg['regions']):
                poly = [(pts[k][0]/sc, pts[k][1]/sc+hdr) for k in verts]
                cx = sum(p[0] for p in poly) / len(poly)
                cy = sum(p[1] for p in poly) / len(poly)
                d.text((cx-25, cy-12), f"{fr[ri]*100:.1f}%", fill='black', font=fnt)
                d.text((cx-25, cy+4), f"({self.opt.targets[ri]*100:.1f}%)", fill='grey', font=fs)

            # Bar chart
            bt = sh + hdr + 10
            bwe = (sw - 40) / len(self.cfg['regions'])
            for ri in range(len(self.cfg['regions'])):
                bx = 20 + ri * bwe
                d.rectangle([bx+2, bt+80-self.opt.targets[ri]*250, bx+bwe-4, bt+80], outline='grey')
                d.rectangle([bx+4, bt+80-fr[ri]*250, bx+bwe-6, bt+80], fill=PASTEL[ri])
                d.text((bx+4, bt+85), short[ri], fill='black', font=fs)

            frames.append(np.array(img))

        durations = [1.5 if i == 0 else (4.0 if i == len(frames)-1 else 0.12)
                     for i in range(len(frames))]
        imageio.mimsave(out_path, frames, duration=durations, loop=0)
        print(f"    Saved {out_path}")

    def generate_masks(self, final_v):
        """Generate filled masks (white-bg + transparent-bg) for each region."""
        mdir = os.path.join(self.odir, 'masks')
        os.makedirs(mdir, exist_ok=True)
        mov = self.opt.unpack(final_v)
        pts = self.opt.all_points(mov)

        for ri, (name, verts, _) in enumerate(self.cfg['regions']):
            poly = [(int(round(pts[k][0])), int(round(pts[k][1]))) for k in verts]
            fname = self.cfg['mask_names'][ri]

            # White background, black fill
            img = Image.new('L', (self.W, self.H), 255)
            ImageDraw.Draw(img).polygon(poly, fill=0)
            img.save(os.path.join(mdir, f'mask_{ri+1}_{fname}.png'))

            # Transparent background, black fill
            img2 = Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))
            ImageDraw.Draw(img2).polygon(poly, fill=(0, 0, 0, 255))
            img2.save(os.path.join(mdir, f'mask_{ri+1}_{fname}_transparent.png'))

            print(f"      {ri+1}. {name}")

    def generate_whole(self, final_v):
        """Generate whole.png — black lines on white, no dots."""
        mov = self.opt.unpack(final_v)
        pts = self.opt.all_points(mov)
        img = Image.new('RGB', (self.W, self.H), 'white')
        d = ImageDraw.Draw(img)

        for _, verts, _ in self.cfg['regions']:
            poly = [pts[k] for k in verts]
            for i in range(len(poly)):
                j = (i+1) % len(poly)
                d.line([tuple(map(lambda c: int(round(c)), poly[i])),
                        tuple(map(lambda c: int(round(c)), poly[j]))], fill='black', width=3)
        chain = self.cfg['fixed_chain']
        for i in range(len(chain)-1):
            p1, p2 = pts[chain[i]], pts[chain[i+1]]
            d.line([tuple(map(int, p1)), tuple(map(int, p2))], fill='black', width=3)

        path = os.path.join(self.odir, 'whole.png')
        img.save(path)
        print(f"    Saved {path}")

    def generate_vertices_map(self, final_v):
        """Generate annotated vertex map with color-coded dots."""
        mov = self.opt.unpack(final_v)
        pts = self.opt.all_points(mov)
        img = Image.new('RGB', (self.W, self.H), 'white')
        d = ImageDraw.Draw(img)
        fnt, fs = get_font(48), get_font(30)
        BLUE, GREY = (50, 120, 220), (140, 140, 140)
        r = 25

        # Fixed chain in red
        chain = self.cfg['fixed_chain']
        for i in range(len(chain)-1):
            p1, p2 = pts[chain[i]], pts[chain[i+1]]
            d.line([tuple(map(int, p1)), tuple(map(int, p2))], fill='red', width=5)

        # All edges in grey
        for _, verts, _ in self.cfg['regions']:
            poly = [pts[k] for k in verts]
            for i in range(len(poly)):
                j = (i+1) % len(poly)
                d.line([tuple(map(lambda c: int(round(c)), poly[i])),
                        tuple(map(lambda c: int(round(c)), poly[j]))], fill=(80,80,80), width=3)

        # Fixed dots (red)
        for k in self.cfg['fixed']:
            x, y = int(pts[k][0]), int(pts[k][1])
            d.ellipse([x-r, y-r, x+r, y+r], fill='red', outline='darkred', width=2)
            d.text((x+r+5, y-15), k, fill='red', font=fnt)

        # Edge-constrained (blue)
        for k in self.cfg['edge_constraints']:
            x, y = int(mov[k][0]), int(mov[k][1])
            d.ellipse([x-r, y-r, x+r, y+r], fill=BLUE, outline=(30,80,180), width=2)
            lx = x-r-120 if x > self.W-200 else x+r+5
            d.text((lx, y-15), k, fill=BLUE, font=fnt)

        # Free movable (grey)
        free_keys = [k for k in self.cfg['movable_start'] if k not in self.cfg['edge_constraints']]
        for k in free_keys:
            x, y = int(mov[k][0]), int(mov[k][1])
            d.ellipse([x-r, y-r, x+r, y+r], fill=GREY, outline=(100,100,100), width=2)
            d.text((x+r+5, y-15), k, fill=GREY, font=fnt)

        # Corner dots
        for k in self.cfg['corners']:
            x, y = int(pts[k][0]), int(pts[k][1])
            d.ellipse([x-18, y-18, x+18, y+18], fill=(60,60,60))

        # Legend
        n_fixed = len(self.cfg['fixed'])
        n_edge = len(self.cfg['edge_constraints'])
        n_free = len(self.cfg['movable_start']) - n_edge
        lx, ly = 100, self.H - 350
        d.rectangle([lx, ly, lx+950, ly+290], fill='white', outline='grey', width=2)
        d.ellipse([lx+20, ly+25, lx+50, ly+55], fill='red')
        d.text((lx+70, ly+25), f"FIXED: {self.cfg['chain_side']} boundary ({n_fixed} pts)", fill='red', font=fs)
        d.ellipse([lx+20, ly+75, lx+50, ly+105], fill=BLUE)
        d.text((lx+70, ly+75), f"MOVABLE: edge-constrained ({n_edge} pts)", fill=BLUE, font=fs)
        d.ellipse([lx+20, ly+125, lx+50, ly+155], fill=GREY)
        d.text((lx+70, ly+125), f"MOVABLE: free 2D ({n_free} pts)", fill=GREY, font=fs)
        d.text((lx+20, ly+185), f"Canvas: {self.W}×{self.H} | max angle ≤ {MAX_ANGLE}°", fill='black', font=fs)
        d.text((lx+20, ly+225), "OPTIMIZED POSITIONS", fill='green', font=fs)

        path = os.path.join(self.odir, 'vertices_map.png')
        img.save(path)
        print(f"    Saved {path}")

    def save_json(self, final_v):
        """Save final positions and diagnostics to JSON."""
        mov = self.opt.unpack(final_v)
        pts = self.opt.all_points(mov)
        fr, areas = self.opt.fractions(mov)

        region_data = []
        for i, (name, verts, _) in enumerate(self.cfg['regions']):
            poly = [pts[k] for k in verts]
            angles = interior_angles(poly)
            region_data.append({
                'name': name, 'vertices': verts,
                'target_fraction': round(self.opt.targets[i], 6),
                'achieved_fraction': round(fr[i], 6),
                'relative_error_pct': round(abs(fr[i]-self.opt.targets[i])/self.opt.targets[i]*100, 4),
                'pixel_area': round(areas[i], 1),
                'interior_angles_deg': [round(a, 1) for a in angles],
                'max_angle_deg': round(max(angles), 1),
            })

        data = {
            'panel': self.panel_key,
            'canvas': {'width': self.W, 'height': self.H},
            'constraints': {'max_angle_deg': MAX_ANGLE, 'min_angle_deg': MIN_ANGLE},
            'fixed_vertices': {k: list(v) for k, v in self.cfg['fixed'].items()},
            'optimized_vertices': {k: [round(v[0], 2), round(v[1], 2)] for k, v in mov.items()},
            'implicit_corners': {k: list(v) for k, v in self.cfg['corners'].items()},
            'regions': region_data,
            'total_objective': round(self.opt.objective(final_v), 10),
            'optimization_steps_recorded': len(self.opt.history),
        }
        path = os.path.join(self.odir, 'final_positions.json')
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"    Saved {path}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def run_panel(panel_key, base_dir):
    print(f"\n{'═'*70}")
    print(f"  PANEL: {panel_key.upper()}")
    print(f"{'═'*70}")

    odir = os.path.join(base_dir, 'outputs', panel_key)
    opt = PanelOptimizer(panel_key)
    renderer = PanelRenderer(opt, panel_key, odir)

    # Starting state
    fr0, _ = opt.fractions(opt.cfg['movable_start'])
    print(f"\n  Starting fractions:")
    for i, (n, _, _) in enumerate(opt.regions):
        print(f"    {n:31s}: {fr0[i]*100:5.1f}%  (target {opt.targets[i]*100:5.1f}%)")

    # Optimize
    print(f"\n  Optimizing ({opt._var_count} variables, {MAX_ANGLE}° max angle) ...")
    final_v = opt.optimize()

    # Report
    opt.print_report(final_v)
    print(f"\n  Final objective: {opt.objective(final_v):.12f}")
    print(f"  Total optimizer states recorded: {len(opt.history)}")

    # Generate all outputs
    print(f"\n  Generating outputs → {odir}/")

    print("    Frames:")
    fpaths, n_con = renderer.generate_frames(final_v)

    print("    Simple GIF:")
    renderer.make_simple_gif(fpaths, n_con, os.path.join(odir, 'simple_convergence.gif'))

    print("    Annotated GIF:")
    renderer.make_annotated_gif(final_v, os.path.join(odir, 'annotated_convergence.gif'))

    print("    Masks:")
    renderer.generate_masks(final_v)

    print("    Final outputs:")
    renderer.generate_whole(final_v)
    renderer.generate_vertices_map(final_v)
    renderer.save_json(final_v)

    print(f"\n  ✓ Panel {panel_key} complete.\n")


def main():
    parser = argparse.ArgumentParser(description='Convex Partition Optimizer')
    parser.add_argument('panels', nargs='?', default='both',
                        choices=['left', 'right', 'both'],
                        help='Which panel(s) to optimize (default: both)')
    parser.add_argument('--output-dir', default='.',
                        help='Base directory for outputs (default: current dir)')
    args = parser.parse_args()

    panels = ['left', 'right'] if args.panels == 'both' else [args.panels]

    for p in panels:
        run_panel(p, args.output_dir)

    print("═" * 70)
    print("  ALL DONE")
    print("═" * 70)


if __name__ == '__main__':
    main()
