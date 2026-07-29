# Where the Water Goes — Flood Exposure, Columbia County NY

A one-off, **qualitative** flood-exposure reading of the mapped area of Columbia County, New York: Kinderhook down to Red Mills, the tidal Hudson east to the Taconic foothills.

**This is not an engineered flood study and not a FEMA determination.** Do not use it for insurance, permitting, purchase, or life-safety decisions.

## Files

- **`index.html`** — the assessment. Single file; the source map is embedded as a base64 data URI so the page carries its own evidence.
- **`source-map.jpeg`** — the original supplied screenshot (1206 × 1067), kept for provenance.

## What it argues

The organising observation is a **drainage constriction**:

- Kinderhook Creek (49 mi) and Claverack Creek (17.5 mi) converge to form Stockport Creek — which runs only **2.4 mi** to the Hudson.
- Nearly all the channel length sits *upstream* of the junction, which is the worst arrangement for attenuating a peak.
- That short outlet is **tidal** (the Hudson is an estuary to the Troy dam, mean range 4.7 ft there), so discharge capacity depends on tidal stage. The coincidence of runoff peak with tide is a decisive variable that rainfall totals alone do not capture.
- The regional gradient runs east→west, so the eastern uplands generate and the western lowlands receive — and steep upland terrain means short concentration times, hence short warning.

Four areas are called out: the Stockport confluence and reaches above it; **Philmont**, where NYSDEC rated the Summit Street Lake Dam *"Deficiently Maintained"* with inadequate spillway capacity; Hudson and Lorenz Park on low riverfront ground; and the Kinderhook Creek corridor.

The **late-July 2025** event calibrates all of it — Columbia County under a state of emergency, with **8.31 in recorded at Kinderhook**, a town labelled on the supplied map.

## Method

The screenshot carried EXIF but **no GPS tags**, so the location came from the map's printed labels. The visible stream network and water bodies were read as drainage structure; published sources supplied creek geometry, tidal behaviour, county topography, dam condition, and the 2025 precedent.

Every claim in the page is tagged **sourced** (published, linked), **inference** (reasoned from the map), or **not obtained** (would require blocked data). Overlay geometry is hand-placed and schematic — not georeferenced.

## What was blocked

Every authoritative geospatial service was denied at the network layer (`403` at CONNECT) in the environment this was produced in:

| Service | Would have provided |
|---|---|
| `epqs.nationalmap.gov` | USGS 3DEP point elevations |
| `hazards.fema.gov` | FEMA National Flood Hazard Layer |
| `portal.opentopography.org` | LiDAR / DEM rasters |
| `api.open-elevation.com` | Elevation fallback |
| `nominatim.openstreetmap.org` | Geocoding |
| `waterdata.usgs.gov` | Creek stage & discharge gauges |

So there is **no** delineated flood extent, **no** modelled depth, **no** return-period assignment, and **no** verified FEMA zone anywhere in the document. Those gaps are marked in the text rather than filled with estimates.

Re-running this with network access to 3DEP and the NFHL would allow actual terrain analysis. That is the obvious next step if the work is worth extending.

## For real determinations

- [FEMA Flood Map Service Center](https://msc.fema.gov/portal/search) — authoritative, searchable by address
- [NY GIS — FEMA Flood Hazard Zones](https://opdgig.dos.ny.gov/datasets/fema-flood-hazard-zones/about)
- [USGS 3D Elevation Program](https://www.usgs.gov/3d-elevation-program)
- [USGS gauge — Agawamuck Creek at Philmont](https://waterdata.usgs.gov/monitoring-location/USGS-01361050/)
- [NWS Albany](https://www.weather.gov/aly/) — during an actual event
