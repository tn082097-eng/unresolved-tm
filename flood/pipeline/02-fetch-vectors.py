#!/usr/bin/env python3
"""
Step 02 - fetch the vector reference layers.

  NHD  (HUC4 0202, Hudson basin) -> named watercourses, so channels are named
                                    from the authoritative source, not by eye
  GNIS (DomesticNames_NY)        -> place coordinates, since geocoding APIs were
                                    unreachable from the build environment

    pip install fiona numpy
    python3 02-fetch-vectors.py

Outputs: nhd_feats.pkl, places.json
"""
import csv
import io
import json
import pickle
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import fiona
import numpy as np

WEST, EAST, SOUTH, NORTH = -73.86, -73.51, 42.16, 42.41
BASE = "https://prd-tnm.s3.amazonaws.com/StagedProducts"
NHD_URL = f"{BASE}/Hydrography/NHD/HU4/Shape/NHD_H_0202_HU4_Shape.zip"
GNIS_URL = f"{BASE}/GeographicNames/DomesticNames/DomesticNames_NY_Text.zip"

# The places labelled on the supplied map screenshot.
WANTED = {
    "Kinderhook", "Sunnyside", "Stockport", "Lorenz Park", "Hudson", "Red Mills",
    "Ghent", "Philmont", "Harlemville", "Spencertown", "Claverack", "Coxsackie",
    "Stottville",
}


def download(url, dest):
    if Path(dest).exists():
        print(f"  {dest} already present")
        return
    print(f"  fetching {url}")
    urllib.request.urlretrieve(url, dest)


def flowlines():
    """Extract flowline parts inside the frame, keeping GNIS names."""
    feats = []
    lengths = defaultdict(float)
    with fiona.open(f"zip://{Path('nhd0202.zip').resolve()}!Shape/NHDFlowline.shp") as src:
        for feat in src.filter(bbox=(WEST, SOUTH, EAST, NORTH)):
            props, geom = feat["properties"], feat["geometry"]
            name = (props.get("gnis_name") or "").strip()
            coords = geom["coordinates"]
            parts = coords if geom["type"] == "MultiLineString" else [coords]
            for part in parts:
                pts = [(c[0], c[1]) for c in part]
                if len(pts) < 2:
                    continue
                feats.append((name, props.get("ftype"), pts))
                arr = np.array(pts)
                # crude local scaling: ~82 km per degree lon at 42N, 111 per lat
                lengths[name] += float(
                    np.sum(np.hypot(np.diff(arr[:, 0]) * 82.0, np.diff(arr[:, 1]) * 111.0))
                )
    print(f"  {len(feats)} flowline parts in frame")
    for name, km in sorted(lengths.items(), key=lambda kv: -kv[1])[:10]:
        print(f"    {km:7.2f} km  {name or '(unnamed, aggregate)'}")
    return feats


def places():
    out = []
    with zipfile.ZipFile("gnis_ny.zip") as zf:
        member = next(n for n in zf.namelist() if n.lower().endswith(".txt"))
        with zf.open(member) as fh:
            reader = csv.DictReader(
                io.TextIOWrapper(fh, "utf-8", errors="replace"), delimiter="|"
            )
            for row in reader:
                name = row.get("feature_name", "").strip()
                if name not in WANTED:
                    continue
                if row.get("feature_class") not in ("Populated Place", "Civil"):
                    continue
                try:
                    lat = float(row["prim_lat_dec"])
                    lon = float(row["prim_long_dec"])
                except (KeyError, TypeError, ValueError):
                    continue
                if SOUTH - 0.05 < lat < NORTH + 0.05 and WEST - 0.05 < lon < EAST + 0.05:
                    out.append((name, lat, lon))
    seen, uniq = set(), []
    for name, lat, lon in sorted(out):
        key = (name, round(lat, 3))
        if key not in seen:
            seen.add(key)
            uniq.append((name, lat, lon))
    print(f"  {len(uniq)} places resolved")
    return uniq


def main():
    download(NHD_URL, "nhd0202.zip")
    download(GNIS_URL, "gnis_ny.zip")
    pickle.dump(flowlines(), open("nhd_feats.pkl", "wb"))
    json.dump(places(), open("places.json", "w"))
    print("wrote nhd_feats.pkl, places.json")


if __name__ == "__main__":
    main()
