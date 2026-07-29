# Where the Water Goes — Flood Terrain, Columbia County NY

A terrain flood-susceptibility analysis of the area in a supplied map screenshot: Columbia County, New York, from Kinderhook down to Red Mills, tidal Hudson east to the Taconic foothills.

Built from **USGS 3DEP 1-metre LiDAR**. Elevations, gradients and floodplain widths are measured, not inferred.

**Not a hydraulic model and not a FEMA determination.** Do not use it for insurance, permitting, purchase, or life-safety decisions.

## The finding

Channel gradients across the frame differ by a factor of 67:

| Watercourse | Gradient | Floodplain width (HAND ≤ 2 m) |
|---|---|---|
| Agawamuck Creek | 21.38 m/km | 147 m |
| Taghkanic Creek | 13.81 m/km | 251 m |
| Kinderhook Creek | 5.72 m/km | 258 m |
| Claverack Creek | 5.10 m/km | 183 m |
| **Stockport Creek** | **0.32 m/km** | **354 m** |
| Hudson River | tidal | 590 m |

Kinderhook Creek and Claverack Creek converge to form Stockport Creek, whose **entire 4.09 km length sits between 0.10 and 1.10 m elevation** — already at sea level, 16–18× flatter than the two creeks feeding it. The flow-direction grid located that confluence independently, 28 m from NHD's Claverack Creek and 477 m from the head of NHD's Stockport Creek, at 1.1 m elevation.

The outlet is tidal, and the Hudson's 4.7 ft mean range at Troy exceeds the total fall available along Stockport Creek — so the tide, not the channel slope, can govern whether the creek discharges at all.

This produces **two distinct flood mechanisms**: Stockport Creek spreads (broad, flat, tidal — hazard is extent and duration), while the Agawamuck concentrates (steep, confined — hazard is a short violent pulse, in the corridor below Philmont's impoundment, whose dam NYSDEC rated *"Deficiently Maintained"*).

A pattern the villages share: they are sited **above** their creeks. Stockport sits 41.4 m up with ground falling to 6.8 m within 250 m. Absolute elevation says little about exposure — Harlemville at 700 ft has the lowest HAND of any settlement here (3.1 m, 45.5% of surroundings within 2 m of drainage).

## Files

```
index.html              the analysis
source-map.jpeg         the original supplied screenshot (provenance)
figures/                rendered maps
data/                   every number quoted, as JSON
pipeline/               the scripts, in order
```

## Reproducing

All inputs are public; no credentials needed.

```sh
pip install rasterio numpy scipy pysheds fiona pillow

python3 pipeline/01-build-dem.py      # 3DEP 1 m -> 10 m mosaic (windowed HTTP reads)
python3 pipeline/02-fetch-vectors.py  # NHD flowlines + GNIS place names
python3 pipeline/03-hydrology.py      # fill -> D8 -> accumulation -> HAND
python3 pipeline/04-render-region.py  # regional figure
python3 pipeline/05-render-insets.py  # 1 m detail insets
```

The 1 m tiles are internally tiled with overviews, so GDAL's `/vsicurl` driver reads only the byte ranges needed — the 10 m mosaic takes ~11 s and tens of megabytes, against ~2 GB for the full tiles.

Data sources: [3DEP 1 m](https://www.usgs.gov/3d-elevation-program) project `NY_ColumbiaRensselaer_2016_C18` (16 tiles), [NHD](https://www.usgs.gov/national-hydrography) HUC4 0202, [GNIS](https://www.usgs.gov/tools/geographic-names-information-system-gnis) `DomesticNames_NY` — all from `prd-tnm.s3.amazonaws.com`.

## Method

10 m grid, 2930 × 2822 cells, 29.3 × 28.2 km, EPSG:26918, 90.5% coverage (the west bank is outside the LiDAR project). Depressions filled, flats resolved, D8 flow direction and accumulation, streams at a 0.25 km² threshold, then **Height Above Nearest Drainage** per cell.

HAND ≤ 1 m covers 12.5% of the analysable area; ≤ 2 m, 17.6%; ≤ 3 m, 21.7%; ≤ 5 m, 28.3%.

Claims in the page are tagged **measured** (from the DEM), **sourced** (published, linked), **inference** (reasoning on top), or **not obtained**.

## Limits

- **HAND is not inundation.** It ranks ground by height above its drainage — no depth, velocity, return period, or hydraulic routing.
- **Accumulation is frame-truncated.** Max in-frame contributing area is 111.8 km²; Kinderhook Creek's real watershed reaches into Massachusetts.
- **LiDAR is a 2016 surface model.** Returns over open water are unreliable; channel beds are not bathymetry.
- **90.5% coverage.** Dark on the map means unmeasured, not safe.
- **HAND at 10 m.** Insets show 1 m hillshade under a 10 m HAND surface, so blue edges are coarser than the relief beneath.
- **No FEMA NFHL** and **no USGS gauge data** — both unreachable from the build environment. The runoff/tide coincidence stays qualitative, and nothing here is a flood-zone determination.

## Corrections

§ 07 of the page records what the measurements overturned, including two of my own errors worth flagging here:

1. An earlier version claimed no elevation data was obtainable. It tested six elevation *APIs*, found them blocked, and wrongly generalised — the bulk/tiled sources on `prd-tnm.s3.amazonaws.com` were reachable throughout.
2. A floodplain width of 3,612 m for Stockport Creek was an artifact of dividing area by raw NHD *vertex count* instead of measured channel length. Densifying to 8 m spacing gives 354 m. The 1 m hillshade is what caught it.
3. Lorenz Park was described as low riverfront ground. Measured: 176 ft, HAND 12.5 m, 0.0% of surroundings within 2 m of drainage. Withdrawn.

## For real determinations

- [FEMA Flood Map Service Center](https://msc.fema.gov/portal/search) — authoritative, searchable by address
- [NY GIS — FEMA Flood Hazard Zones](https://opdgig.dos.ny.gov/datasets/fema-flood-hazard-zones/about)
- [USGS gauge — Agawamuck Creek at Philmont](https://waterdata.usgs.gov/monitoring-location/USGS-01361050/)
- [NWS Albany](https://www.weather.gov/aly/) — during an actual event
