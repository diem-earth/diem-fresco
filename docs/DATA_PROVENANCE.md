# Data Provenance & Licenses

| Asset | Origin | License / terms |
|---|---|---|
| `canny_final.tiff` | Diem project pipeline: official Paris map → rotation → Canny. Author: Mathis Koroglu (2025-11-19). | project-internal; check upstream map license before public release of derivatives |
| `diem_master_geometry_v1.*` | Derived from `canny_final.tiff` in stage 1 (this repo) | same as above |
| `decomposition/**` | Derived in stage 2 (this repo) from the master + the sources below | same as above + ODbL attribution for OSM-derived boundaries (L5 cuts, L4 units) |
| `pipeline/sources/arrondissements.geojson` | Paris Open Data — dataset “arrondissements” (export 2026-07-08) | [Licence Ouverte v2 (Etalab)](https://opendata.paris.fr) — attribution: *Ville de Paris* |
| `pipeline/sources/quartiers.geojson` | Paris Open Data — dataset “quartier_paris” (export 2026-07-08) | Licence Ouverte v2 — attribution: *Ville de Paris* |
| `pipeline/sources/{major_roads,secondary_roads,parks,rail}.json` | OpenStreetMap via Overpass API (extract 2026-07-08) | [ODbL 1.0](https://www.openstreetmap.org/copyright) — attribution: *© OpenStreetMap contributors* |
| Landmark/plaza coordinates in scripts | public geographic knowledge, hand-curated | n/a |

## Attribution requirements for published work

If fresco materials derived from this repo are published or exhibited, include:

> Administrative boundaries: Ville de Paris (Licence Ouverte v2).
> Road classification and park data: © OpenStreetMap contributors (ODbL).

The street geometry itself derives from the project's upstream official map, not from
OSM — OSM data is used only for *classifying and grouping* regions.
