"""Minimal anonymous-S3 zarr v2 reader: fetch a chunk, zstd-decode, reshape."""
import json, urllib.request, numpy as np, numcodecs

RETRO = "https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/CONUS/zarr/chrtout.zarr"
_meta = None

def meta():
    global _meta
    if _meta is None:
        with urllib.request.urlopen(f"{RETRO}/.zmetadata", timeout=60) as r:
            _meta = json.load(r)["metadata"]
    return _meta

def get(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "flood-analysis"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def chunk(var, key="0"):
    m = meta()[f"{var}/.zarray"]
    raw = get(f"{RETRO}/{var}/{key}")
    dec = numcodecs.get_codec(m["compressor"]).decode(raw)
    a = np.frombuffer(dec, dtype=np.dtype(m["dtype"]))
    return a, m

def coord(var):
    a, m = chunk(var)
    return a[: m["shape"][0]]

def streamflow_block(t_chunk, f_chunk):
    """One [672 x 30000] int32 block, scaled to m3/s with missing -> nan."""
    m = meta()["streamflow/.zarray"]
    a, _ = chunk("streamflow", f"{t_chunk}.{f_chunk}")
    a = a.reshape(m["chunks"]).astype(np.float32)
    a[a == -999900] = np.nan
    return a * 0.009999999776482582
