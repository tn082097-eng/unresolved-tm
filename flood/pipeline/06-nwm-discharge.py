#!/usr/bin/env python3
"""
Step 06 - modelled discharge at the named reaches, from the National Water Model.

Two sources, both anonymous public S3:

  noaa-nwm-retrospective-3-0-pds  hourly zarr, 1979-02 -> ~2023-02  (historical floods)
  noaa-nwm-pds                    hourly NetCDF analysis_assim      (recent events)

NWM output is MODEL, not measurement. It assimilates USGS gauges, so it is
anchored to observations, but it also smooths intense local convective rainfall.
Trust the shapes and ratios more than the absolute magnitudes.

    pip install numpy netCDF4 numcodecs
    python3 06-nwm-discharge.py

Needs nhd_feats.pkl from step 02. Outputs nwm_match.json, event2026.json,
retro_events.json.
"""
import datetime as dt
import json
import pickle

import numpy as np

from nwm_util import coord, streamflow_block  # noqa: E402

CREEKS = ["Stockport Creek", "Kinderhook Creek", "Claverack Creek",
          "Agawamuck Creek", "Taghkanic Creek", "Hudson River"]
BBOX = (-73.90, -73.47, 42.12, 42.45)          # W, E, S, N
KM_PER_DEG_LON, KM_PER_DEG_LAT = 82.0, 111.0   # local scaling at 42 N
CHUNK_W, CHUNK_T = 30000, 672
EPOCH = dt.datetime(1979, 2, 1, 1, 0, 0)

HISTORICAL = {
    "Jan 1996 snowmelt+rain": dt.datetime(1996, 1, 19),
    "TS Floyd 1999":          dt.datetime(1999, 9, 17),
    "Apr 2005":               dt.datetime(2005, 4, 3),
    "TS Irene 2011":          dt.datetime(2011, 8, 29),
    "TS Lee 2011":            dt.datetime(2011, 9, 8),
    "Halloween 2019":         dt.datetime(2019, 11, 1),
}


def match_reaches(feats):
    """Assign each candidate NWM reach to its nearest named creek *exclusively*,
    then take the highest stream order (tie-break: lowest elevation = furthest
    downstream). Without exclusivity, Kinderhook and Claverack both snap to the
    shared post-confluence reach and report identical flow."""
    lat, lon = coord("latitude"), coord("longitude")
    fid, order, elev = coord("feature_id"), coord("order"), coord("elevation")
    w, e, s, n = BBOX
    sel = np.where((lon >= w) & (lon <= e) & (lat >= s) & (lat <= n))[0]
    verts = {c: np.array([p for nm, _, ps in feats if nm == c for p in ps]) for c in CREEKS}

    dist = np.full((len(sel), len(CREEKS)), np.inf)
    for j, creek in enumerate(CREEKS):
        pts = verts[creek]
        if not len(pts):
            continue
        for i, gi in enumerate(sel):
            dist[i, j] = np.min(np.hypot((pts[:, 0] - lon[gi]) * KM_PER_DEG_LON,
                                         (pts[:, 1] - lat[gi]) * KM_PER_DEG_LAT)) * 1000

    owner = np.argmin(dist, axis=1)
    dmin = dist[np.arange(len(sel)), owner]
    out = {}
    for j, creek in enumerate(CREEKS):
        mine = np.where((owner == j) & (dmin < 300))[0]
        if not len(mine):
            print(f"  {creek}: no exclusive reach within 300 m")
            continue
        best = mine[np.lexsort((elev[sel][mine], -order[sel][mine]))][0]
        gi = int(sel[best])
        out[creek] = dict(feature_id=int(fid[gi]), order=int(order[gi]),
                          dist_m=round(float(dmin[best]), 1),
                          elev_m=round(float(elev[gi]), 1),
                          lat=round(float(lat[gi]), 5), lon=round(float(lon[gi]), 5),
                          n_exclusive=int(len(mine)), global_index=gi)
        print(f"  {creek:18s} id {out[creek]['feature_id']:10d} order {out[creek]['order']} "
              f"{out[creek]['dist_m']:6.0f} m  elev {out[creek]['elev_m']:6.1f} m")
    ids = [v["feature_id"] for v in out.values()]
    assert len(set(ids)) == len(ids), "reach collision - exclusivity failed"
    return out


def historical(match):
    """One 672-hour chunk brackets each event. Never pull the full 44-year series:
    that is 574 time-chunks per feature-chunk."""
    gidx = {k: v["global_index"] for k, v in match.items()}
    out, cache = {}, {}
    for name, when in HISTORICAL.items():
        tc = int((when - EPOCH).total_seconds() // 3600) // CHUNK_T
        per = {}
        for fc in sorted({i // CHUNK_W for i in gidx.values()}):
            if (tc, fc) not in cache:
                cache[(tc, fc)] = streamflow_block(tc, fc)
            blk = cache[(tc, fc)]
            for creek, gi in gidx.items():
                if gi // CHUNK_W != fc:
                    continue
                series = blk[:, gi % CHUNK_W]
                k = int(np.nanargmax(series))
                per[creek] = dict(
                    peak_m3s=round(float(series[k]), 2),
                    peak_time=(EPOCH + dt.timedelta(hours=tc * CHUNK_T + k)).isoformat())
        out[name] = per
        print(f"  {name:24s} " + "  ".join(
            f"{c.split()[0][:6]}={v['peak_m3s']:8.1f}" for c, v in per.items()))
        cache = {k: v for k, v in cache.items() if k[0] == tc}
    return out


def event(match, start, n_steps=40, step_h=3):
    """analysis_assim for a recent event. netCDF4 reads these over HTTP with
    '#mode=bytes', so no full download is needed - but streamflow is a single
    chunk, so each file still costs ~11 MB."""
    import netCDF4
    want = {v["feature_id"]: k for k, v in match.items()}
    base = ("https://noaa-nwm-pds.s3.amazonaws.com/nwm.{d}/analysis_assim/"
            "nwm.t{h:02d}z.analysis_assim.channel_rt.tm00.conus.nc")
    idx, rows = None, []
    for k in range(n_steps):
        ts = start + dt.timedelta(hours=step_h * k)
        try:
            ds = netCDF4.Dataset(base.format(d=ts.strftime("%Y%m%d"), h=ts.hour) + "#mode=bytes")
            if idx is None:
                fids = ds.variables["feature_id"][:]
                idx = {f: int(np.where(fids == f)[0][0]) for f in want}
            sf = ds.variables["streamflow"][:]
            rows.append((ts.isoformat(), {want[f]: round(float(sf[i]), 3) for f, i in idx.items()}))
            ds.close()
            print(f"  {ts:%m-%d %H}z  " + "  ".join(
                f"{c.split()[0][:6]}={v:8.2f}" for c, v in rows[-1][1].items()))
        except Exception:
            print(f"  {ts:%m-%d %H}z  not published yet - record ends here")
            break
    return rows


def main():
    feats = pickle.load(open("nhd_feats.pkl", "rb"))
    print("matching reaches...")
    match = match_reaches(feats)
    json.dump(match, open("nwm_match.json", "w"), indent=1)

    print("\nhistorical floods (retrospective v3.0)...")
    json.dump(historical(match), open("retro_events.json", "w"), indent=1)

    print("\n29-30 July 2026 event (analysis_assim)...")
    rows = event(match, dt.datetime(2026, 7, 26, 0))
    names = list(rows[0][1])
    summary = {}
    for nm in names:
        base = rows[0][1][nm]
        peak = max(r[1][nm] for r in rows)
        summary[nm] = dict(
            baseline_m3s=base, peak_m3s=peak, ratio=round(peak / max(base, 1e-6), 1),
            peak_time_utc=max(rows, key=lambda r: r[1][nm])[0],
            still_rising_at_end=bool(rows[-1][1][nm] >= peak - 1e-9))
    json.dump(dict(timesteps=rows, summary=summary), open("event2026.json", "w"), indent=1)

    last = rows[-1][1]
    tot = last["Kinderhook Creek"] + last["Claverack Creek"]
    print(f"\nmass balance: Kinderhook {last['Kinderhook Creek']:.1f} + Claverack "
          f"{last['Claverack Creek']:.1f} = {tot:.1f} vs Stockport "
          f"{last['Stockport Creek']:.1f} ({100*last['Stockport Creek']/tot:.0f}%)")
    print("the deficit is water the flat outlet has not passed on yet")


if __name__ == "__main__":
    main()
