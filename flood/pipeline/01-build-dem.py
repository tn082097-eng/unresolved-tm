#!/usr/bin/env python3
"""
Step 01 - build a 10 m DEM mosaic for the mapped area from USGS 3DEP 1 m LiDAR.

Reads windowed, decimated blocks straight out of the remote GeoTIFFs over HTTP
(GDAL /vsicurl + range requests). The tiles are internally tiled with overviews,
so this pulls tens of megabytes rather than the ~2 GB the full tiles would cost.

    pip install rasterio numpy
    python3 01-build-dem.py

Outputs: dem10.tif, dem10.npy, grid.txt, extent.txt
"""
import math
import warnings

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import transform as warp_transform
from rasterio.windows import from_bounds

warnings.filterwarnings("ignore")

# Extent of the supplied map screenshot, from the places labelled on it.
WEST, EAST, SOUTH, NORTH = -73.86, -73.51, 42.16, 42.41
RES = 10.0  # target resolution, metres
UTM = "EPSG:26918"  # UTM 18N - the projection the 3DEP tiles ship in

PROJECT = "NY_ColumbiaRensselaer_2016_C18"
TILE_URL = (
    "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/"
    f"Projects/{PROJECT}/TIFF/USGS_1M_18_{{}}_{PROJECT}.tif"
)


def tiles_for(min_x, max_x, min_y, max_y):
    """3DEP 1 m tiles are named x{left/10km}y{TOP/10km} - note y is the *top* edge."""
    out = []
    for xi in range(int(min_x // 10000), int(max_x // 10000) + 1):
        for yi in range(int(math.ceil(min_y / 10000)), int(math.ceil(max_y / 10000)) + 1):
            out.append(f"x{xi}y{yi}")
    return out


def main():
    xs, ys = warp_transform(
        "EPSG:4326", UTM, [WEST, EAST, WEST, EAST], [SOUTH, SOUTH, NORTH, NORTH]
    )
    min_x = np.floor(min(xs) / RES) * RES
    max_x = np.ceil(max(xs) / RES) * RES
    min_y = np.floor(min(ys) / RES) * RES
    max_y = np.ceil(max(ys) / RES) * RES

    width = int((max_x - min_x) / RES)
    height = int((max_y - min_y) / RES)
    dst_transform = from_origin(min_x, max_y, RES, RES)
    mosaic = np.full((height, width), np.nan, dtype=np.float32)
    print(f"target grid {width} x {height} @ {RES} m")

    for name in tiles_for(min_x, max_x, min_y, max_y):
        try:
            src = rasterio.open(TILE_URL.format(name))
        except Exception as exc:  # tile not part of the project
            print(f"  {name}: unavailable ({type(exc).__name__})")
            continue
        with src:
            b = src.bounds
            ix0, ix1 = max(min_x, b.left), min(max_x, b.right)
            iy0, iy1 = max(min_y, b.bottom), min(max_y, b.top)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            c0, c1 = int(round((ix0 - min_x) / RES)), int(round((ix1 - min_x) / RES))
            r0, r1 = int(round((max_y - iy1) / RES)), int(round((max_y - iy0) / RES))
            block = src.read(
                1,
                window=from_bounds(ix0, iy0, ix1, iy1, src.transform),
                out_shape=(r1 - r0, c1 - c0),
                resampling=Resampling.average,
                boundless=True,
                fill_value=src.nodata,
            ).astype(np.float32)
            block[block <= -9999] = np.nan  # 3DEP nodata is -999999
            target = mosaic[r0:r1, c0:c1]
            fill = np.isnan(target) & ~np.isnan(block)
            target[fill] = block[fill]
            print(f"  {name}: {100 * np.mean(~np.isnan(block)):5.1f}% valid")

    print(
        f"coverage {100 * np.mean(~np.isnan(mosaic)):.1f}%  "
        f"elevation {np.nanmin(mosaic):.1f}..{np.nanmax(mosaic):.1f} m"
    )
    np.save("dem10.npy", mosaic)
    with open("grid.txt", "w") as fh:
        fh.write(f"{min_x} {max_x} {min_y} {max_y} {RES} {width} {height}")
    with rasterio.open(
        "dem10.tif", "w", driver="GTiff", height=height, width=width, count=1,
        dtype="float32", crs=UTM, transform=dst_transform, nodata=np.nan,
        compress="lzw", tiled=True,
    ) as dst:
        dst.write(mosaic, 1)
    print("wrote dem10.tif, dem10.npy, grid.txt")


if __name__ == "__main__":
    main()
