import numpy as np, warnings, time, sys
warnings.filterwarnings('ignore')
# pysheds still calls np.in1d, removed in NumPy 2.x; np.isin is the direct
# replacement for the 1-D ravel()'d call it makes.
if not hasattr(np, 'in1d'):
    np.in1d = np.isin
from pysheds.grid import Grid

t0=time.time()
grid = Grid.from_raster('dem10.tif')
dem  = grid.read_raster('dem10.tif')
arr  = np.asarray(dem)
print("dem", arr.shape, "nan frac", round(float(np.isnan(arr).mean()),4))

# pysheds needs a real nodata sentinel, not NaN
NOD = -32768.0
filled_in = np.where(np.isnan(arr), NOD, arr).astype('float32')
dem2 = dem.copy(); dem2[:] = filled_in
dem2.nodata = NOD

print("fill pits...");      pit  = grid.fill_pits(dem2)
print("fill depressions..."); flo = grid.fill_depressions(pit)
print("resolve flats...");  inf  = grid.resolve_flats(flo)
print("flow direction..."); fdir = grid.flowdir(inf)
print("accumulation...");   acc  = grid.accumulation(fdir)
print(f"  acc max {float(np.asarray(acc).max()):.0f} cells "
      f"= {float(np.asarray(acc).max())*100/1e6:.1f} km2")

for thresh in (1000, 2500, 5000, 10000):
    net = np.asarray(acc) > thresh
    print(f"  threshold {thresh:6d} cells ({thresh*100/1e6:5.2f} km2) -> "
          f"{net.sum():7d} stream cells ({100*net.mean():.2f}% of grid)")

THRESH = int(sys.argv[1]) if len(sys.argv)>1 else 2500
mask = acc > THRESH   # keep as pysheds Raster (carries viewfinder)
print(f"computing HAND at threshold {THRESH} ...")
hand = grid.compute_hand(fdir, inf, mask)
h = np.asarray(hand).astype('float32')
h[np.isnan(arr)] = np.nan
h[h<0] = 0
print("HAND stats: valid", int(np.isfinite(h).sum()),
      " median", round(float(np.nanmedian(h)),2),
      " p95", round(float(np.nanpercentile(h,95)),2),
      " max", round(float(np.nanmax(h)),1))
for band in (1,2,3,5,10):
    frac = 100*np.nanmean(h<=band)
    print(f"   HAND <= {band:2d} m : {frac:5.2f}% of mapped area")
np.save('fdir.npy', np.asarray(fdir).astype('int16'))
np.save('hand.npy', h)
np.save('acc.npy', np.asarray(acc).astype('float32'))
np.save('streams.npy', np.asarray(mask))
np.save('dem_filled.npy', np.where(np.isnan(arr), np.nan, np.asarray(inf)).astype('float32'))
print("elapsed", round(time.time()-t0,1), "s")
