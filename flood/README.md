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

## Discharge confirmed the mechanism

The two-mechanism claim was made from terrain alone. Modelled discharge through the 29–30 July 2026 storm separates along exactly that line:

| Reach | Base m³/s | Peak m³/s | Rise | At end of record |
|---|---|---|---|---|
| Stockport Ck | 4.57 | 319.6 | 70× | still rising |
| Kinderhook Ck | 3.17 | 190.0 | 60× | still rising |
| Claverack Ck | 1.38 | 149.1 | 108× | still rising |
| **Agawamuck Ck** | 0.13 | 45.0 | **346×** | **peaked 21z, falling** |
| Taghkanic Ck | 0.64 | 20.6 | 32× | still rising |
| Hudson River | 117.43 | 151.9 | 1.3× | still rising |

The Agawamuck — steepest gradient, narrowest floodplain — had the largest relative response and was the **only** reach to peak and turn over. Stockport Creek, flattest and widest, rose monotonically with no peak in the record at all.

**The constriction shows up as arithmetic.** At the last timestep Kinderhook (190.0) + Claverack (149.1) = 339.1, but Stockport Creek immediately below their junction carried **319.6** — the missing **6%** is water the 0.32 m/km outlet had not passed on yet.

**Is it Irene-class? Not on this evidence.** Peak modelled discharge at Stockport Creek: Irene 2011 **2,021**; Lee 2011 726; Floyd 1999 568; Jan 1996 471; Halloween 2019 400; **2026 so far 320**; Apr 2005 229. Irene was 6.3× higher. An Irene-class *rainfall* on dry late-July ground yields far less runoff than Irene's rain did on catchments already saturated in late August — but note the 2026 record was cut short mid-event, so 320 is a floor.

**No inundation map, deliberately.** Synthetic rating curves (HAND geometry + Manning, n = 0.035–0.08) give plausible stages — Stockport 1.5–2.3 m against a 9.1 m valley depth. But that stage is the same order as the Hudson's 1.4 m mean tidal range, so at 0.32 m/km the downstream boundary governs, not the channel slope. The arithmetic returns reasonable numbers for the wrong physics; mapping an extent from it would imply authority it hasn't earned. Stages are reported; no map is drawn.

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
pip install rasterio numpy scipy pysheds fiona pillow netCDF4 numcodecs

python3 pipeline/01-build-dem.py      # 3DEP 1 m -> 10 m mosaic (windowed HTTP reads)
python3 pipeline/02-fetch-vectors.py  # NHD flowlines + GNIS place names
python3 pipeline/03-hydrology.py      # fill -> D8 -> accumulation -> HAND
python3 pipeline/04-render-region.py  # regional figure
python3 pipeline/05-render-insets.py  # 1 m detail insets
python3 pipeline/06-nwm-discharge.py  # NWM reach matching + discharge
```

The 1 m tiles are internally tiled with overviews, so GDAL's `/vsicurl` driver reads only the byte ranges needed — the 10 m mosaic takes ~11 s and tens of megabytes, against ~2 GB for the full tiles.

Data sources, all anonymous public S3:

- [3DEP 1 m LiDAR](https://www.usgs.gov/3d-elevation-program) project `NY_ColumbiaRensselaer_2016_C18` (16 tiles), [NHD](https://www.usgs.gov/national-hydrography) HUC4 0202, and [GNIS](https://www.usgs.gov/tools/geographic-names-information-system-gnis) `DomesticNames_NY` — `prd-tnm.s3.amazonaws.com`
- National Water Model — `noaa-nwm-retrospective-3-0-pds` (hourly zarr, 1979–2023) and `noaa-nwm-pds` (hourly `analysis_assim` NetCDF, read over HTTP byte ranges)

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
- **Discharge is modelled, not measured.** NWM is a 1 km land-surface model; it assimilates USGS gauges but smooths intense local convective rainfall — the kind that drives flash flooding. Trust the shapes and ratios over the absolute magnitudes.
- **The 2026 event record is incomplete** — it stops at 30 July 00z because later files were unpublished. Every 2026 peak is a lower bound.
- **No FEMA NFHL, and it was chased hard.** Beyond `hazards.fema.gov`: every Esri host (`arcgis.com`, `services*.arcgis.com`, `services.arcgisonline.com`, `fema.maps.arcgis.com`), New York's own GIS servers (`gisservices.dhses.ny.gov`, `opdgig.dos.ny.gov`), and `msc.fema.gov` all refused. No NFHL mirror exists on public S3, and NOAA's HAND-based FIM bucket answers 403 on every key. The regulatory layer is **unobtainable here, not skipped** — so nothing in this project is a flood-zone determination.
- **Observed gauge series remain unreachable**, so the runoff/tide coincidence is quantified only through the model.

## The precedent storm

**29–30 July 2026.** Columbia County declared a [State of Emergency effective 10:00 am on Wednesday 29 July 2026](https://www.columbiacountyny.gov/AlertCenter.aspx?AID=July-29-2026-State-of-Emergency-12), citing flooding of local, county and state roadways "in many areas" and warning it would worsen *"especially in areas along the Hudson River and the west side of the county"* — independently the same ground this analysis identifies as lowest relative to its drainage. Kinderhook recorded 8.31 in and Schodack 9.22 in; Kinderhook Creek went over its banks, flooding Routes 9, 9H and County Route 21.

## Corrections

§ 07 of the page records what the measurements overturned, including my own errors worth flagging here:

1. An earlier version claimed no elevation data was obtainable. It tested six elevation *APIs*, found them blocked, and wrongly generalised — the bulk/tiled sources on `prd-tnm.s3.amazonaws.com` were reachable throughout.
2. A floodplain width of 3,612 m for Stockport Creek was an artifact of dividing area by raw NHD *vertex count* instead of measured channel length. Densifying to 8 m spacing gives 354 m. The 1 m hillshade is what caught it.
3. Lorenz Park was described as low riverfront ground. Measured: 176 ft, HAND 12.5 m, 0.0% of surroundings within 2 m of drainage. Withdrawn.
4. The precedent storm was dated to **late July 2025**. It is **29–30 July 2026**. The error came from reading dates out of search-result summaries rather than a primary source — and it was caught by the data: modelled discharge across 18 July – 7 August 2025 showed no flood signal at any of the six reaches, and a state-of-emergency flood cannot be invisible in the discharge record of the basin it flooded.

## For real determinations

- [FEMA Flood Map Service Center](https://msc.fema.gov/portal/search) — authoritative, searchable by address
- [NY GIS — FEMA Flood Hazard Zones](https://opdgig.dos.ny.gov/datasets/fema-flood-hazard-zones/about)
- [USGS gauge — Agawamuck Creek at Philmont](https://waterdata.usgs.gov/monitoring-location/USGS-01361050/)
- [NWS Albany](https://www.weather.gov/aly/) — during an actual event
