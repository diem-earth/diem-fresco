# Phase 1 — Understanding the Map

**Asset:** `diem_master_geometry_v1.tiff` (34 048 × 5 312 px, 300 dpi, canonical — untouched by this stage)

## What the map represents

A **14.37 km × 2.24 km band through the heart of Paris**, at an exact cartographic scale of
**1:5000** (0.4219 m/px at 300 dpi, measured 1:4983 ±0.4%), **rotated 20.3° clockwise from
north-up** so that the *Grand Axis* of Paris — **Étoile → Champs-Élysées → Concorde →
Tuileries/Louvre → Rivoli/Saint-Antoine → Bastille → Cours de Vincennes → Nation** — runs
horizontally along the fresco. The rotation choice is clearly deliberate and gives the band its
narrative spine: the ceremonial east–west traverse of the city.

Georeferencing was performed by matching plaza geometries (Étoile, Nation, Concorde, Vendôme,
Victoires) to their known coordinates and fitting a rigid similarity transform:
**RMS residual 38 px ≈ 16 m** — at 1:5000 within about one street width. The projected official
city limit tracks the drawn périphérique, and the projected 16e/17e boundary runs exactly along
the drawn Avenue de la Grande-Armée. Full transform in `meta/georeference.json`.

## Arrondissement coverage (by fraction of arrondissement area inside the band)

| Complete | Mostly | Partial band | Absent |
|---|---|---|---|
| **1er, 2e, 3e, 4e** (100%) | 8e (89%), 11e (80%) | 12e (35%), 7e (31%), 20e (29%), 17e (28%), 9e (26%), 6e (22%), 16e (22%), 5e (14%), 10e (3%) | 13e, 14e, 15e, 18e, 19e |

The band is, in essence, **"Paris Centre plus its east–west continuation"**: the entire
pre-Haussmann historical core, the full Marais, the grands boulevards' southern flank, the
Faubourg Saint-Antoine, and the western beaux-quartiers along the axis.

## Landmarks identified and visually confirmed on the raster

- **Place Charles-de-Gaulle (Étoile)** — 12-avenue star, double concentric circle (x≈6 974, y≈2 692)
- **Place de la Nation** — radial star + wide Cours de Vincennes (x≈25 700, y≈2 888)
- **Place de la Concorde** — octagon on the Seine (x≈11 981)
- **Place de la Bastille** + **Bassin de l'Arsenal** descending to the Seine
- **Opéra Garnier** diamond block; **Place Vendôme**; **Place des Victoires**
- **Les Halles / Bourse de Commerce** (circular building) and the Forum complex
- **Jardin des Tuileries** (single 0.246 km² enclosed cell), **Jardin du Palais-Royal**
- **La Seine** with **Île de la Cité** and **Île Saint-Louis**, ~35 bridge decks
- **Gare de Lyon** with its surface track fan (bottom edge); Gare Saint-Lazare at the top edge
- **Père-Lachaise** southern part (0.246 km² in band)
- **Boulevard périphérique** with interchange ramps at both tips (Porte Maillot; Porte de Vincennes)
- **Place de la République** (top edge), **Place des Vosges**, **Hôtel de Ville**, **Châtelet**

Annotated overlay: `viz/phase1_annotated_map.png`.

## Fidelity assessment

The network is planimetrically faithful: five independent plaza anchors fit a rigid similarity
at 6–23 m residuals each — consistent with a professionally drawn 1:5000 base map plus the
±10–20 m uncertainty of the reference coordinates themselves. No systematic distortion
(shear/anisotropy) was detectable above the noise floor. Street pattern, plaza shapes, island
outlines, park path networks and the périphérique interchange geometry all match reality at
the rendered generalization level. **Verdict: the extraction corresponds faithfully to the
real city; it can be treated as a geometric ground truth for the pipeline.**
