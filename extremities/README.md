# Convex Partition Optimizer

> Part of the **diem-fresco** repository: these are the fresco's left/right extremity
> panels (French regions) flanking the Paris Centre street map. For how the three
> panels join into the full 34 048 × 5 312 px fresco, see [../docs/PIPELINE.md](../docs/PIPELINE.md).

Optimizes a hexagonal tiling of two mural panels so that each convex region's pixel area is **proportional to the real-world surface** of the French administrative region it represents.

![Left panel convergence](outputs/left/annotated_convergence.gif)
![Right panel convergence](outputs/right/annotated_convergence.gif)

## The problem

A large fresco (11 088 × 5 312 px) is divided into two adjacent panels sharing a zigzag boundary. Each panel is tiled into 6 convex polygons (partial hexagons), one per French region. The challenge: adjust the interior vertices so that every polygon's area matches its region's real-world surface proportion — while keeping all polygons convex and preserving the hexagonal aesthetic.

### Left panel (5 088 × 5 312)

| Region | Real area (km²) | Target |
|---|---|---|
| Bretagne | 27 208 | 9.5% |
| Normandie | 29 875 | 10.5% |
| Pays de la Loire | 32 082 | 11.3% |
| Centre-Val de Loire | 39 151 | 13.7% |
| Nouvelle-Aquitaine | 84 036 | 29.5% |
| Occitanie | 72 724 | 25.5% |

### Right panel (6 000 × 5 312)

| Region | Real area (km²) | Target |
|---|---|---|
| Hauts-de-France | 31 813 | 12.9% |
| Grand Est | 57 441 | 23.3% |
| Auvergne-Rhône-Alpes | 69 711 | 28.2% |
| Bourgogne-Franche-Comté | 47 784 | 19.4% |
| PACA | 31 400 | 12.7% |
| Corse | 8 680 | 3.5% |

## Approach

### Optimization

Each panel has **8 movable vertices** (12 scalar variables: 4 edge-constrained points with 1 DOF each, 4 free interior points with 2 DOF each) and **5–6 fixed vertices** forming the shared zigzag boundary.

The objective function minimizes the sum of squared relative errors between current and target area fractions:

$$\min \sum_{i=1}^{6} \left(\frac{f_i - t_i}{t_i}\right)^2$$

subject to:
- **Convexity**: every region must remain a convex polygon
- **Anti-collinearity**: no controllable interior angle may exceed 155° (prevents degenerate "rectangular" shapes; preserves hexagonal aesthetic)
- **Edge constraints**: boundary points stay on their respective canvas edges

A multi-phase solver is used:
1. **L-BFGS-B** — fast gradient-based convergence
2. **Nelder-Mead** — handles the non-smooth convexity/angle landscape
3. **L-BFGS-B** — final polish
4. **Extra Nelder-Mead + L-BFGS-B passes** — ensure global convergence

Both panels converge to **0.00% relative error** on all fractions.

### Anti-collinearity constraint

Without this constraint, the optimizer tends to align three consecutive vertices, making edges "disappear" and polygons look rectangular. The constraint penalizes any interior angle above 155°, except at vertices where all three relevant points are fixed (immovable by the optimizer).

## Usage

```bash
pip install -r requirements.txt

# Optimize both panels
python optimize.py both

# Or just one
python optimize.py left
python optimize.py right
```

## Repository structure

```
├── optimize.py                     # Main script — both panels
├── requirements.txt
├── README.md
├── inputs/
│   ├── left/
│   │   ├── whole.png               # Starting partition
│   │   ├── vertices_map.png        # Annotated vertex map
│   │   └── masks/                  # Original region masks
│   └── right/
│       ├── whole.png
│       ├── vertices_map.png
│       └── masks/
└── outputs/
    ├── left/
    │   ├── whole.png               # Optimized partition (lines only)
    │   ├── vertices_map.png        # Optimized vertex map
    │   ├── final_positions.json    # Coordinates + diagnostics
    │   ├── simple_convergence.gif  # B&W animation
    │   ├── annotated_convergence.gif
    │   ├── frames/                 # Individual PNG frames
    │   │   └── frame_000.png … frame_NNN.png
    │   └── masks/                  # Final pixel-perfect masks
    │       ├── mask_1_bretagne.png
    │       ├── mask_1_bretagne_transparent.png
    │       └── …
    └── right/
        └── … (same structure)
```

### Output files

| File | Description |
|---|---|
| `whole.png` | Black lines on white, 5088×5312 or 6000×5312 |
| `vertices_map.png` | Annotated: red=fixed, blue=edge-constrained, grey=free |
| `final_positions.json` | All vertex coordinates, area fractions, angles |
| `simple_convergence.gif` | B&W step-by-step construction + optimization |
| `annotated_convergence.gif` | Colored regions with live % and bar chart |
| `masks/mask_N_name.png` | Black filled region on white (8-bit grayscale) |
| `masks/mask_N_name_transparent.png` | Black filled region on transparent (RGBA) |

## Results

Both panels achieve **perfect convergence** (0.00% error on all 12 regions) while maintaining:
- Full convexity of all polygons
- No controllable interior angle above 155°
- The hexagonal aesthetic of the original design

The only angles above 155° are at vertices where all three points in the triplet are fixed — these are geometrically immutable.

## License

MIT
