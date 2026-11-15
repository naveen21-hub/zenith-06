import numpy as np
import os, glob
from pyproj import Transformer
from scipy.ndimage import median_filter, binary_fill_holes
from skimage.measure import label, regionprops

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

npz_files = sorted(glob.glob(os.path.join(DB_DIR, "*.npz")))
ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
dx = 10.0

BOX_LON = (76.445, 76.585)
BOX_LAT = (12.380, 12.530)
ux0, uy0 = to_utm.transform(BOX_LON[0], BOX_LAT[0])
ux1, uy1 = to_utm.transform(BOX_LON[1], BOX_LAT[1])
c0 = max(0, int((ux0 - x_coords[0]) / dx))
c1 = min(len(x_coords), int((ux1 - x_coords[0]) / dx))
r0 = max(0, int((y_coords[0] - uy1) / dx))
r1 = min(len(y_coords), int((y_coords[0] - uy0) / dx))

DATES = ["2025-11-23", "2026-08-14", "2026-11-06"]

masks = []
for i, f in enumerate(npz_files):
    d = np.load(f)
    hh = d['HHHH'][r0:r1, c0:c1].astype(np.float32)
    db = 10.0 * np.log10(np.where(hh > 0, hh, np.nan))
    db = np.nan_to_num(db, nan=-30.0)
    filt = median_filter(db, size=5)
    raw = filt < -16.0
    filled = binary_fill_holes(raw).astype(np.uint8)
    lbl = label(filled)
    props = sorted(regionprops(lbl), key=lambda p: p.area, reverse=True)
    keep = [p.label for p in props if p.area >= props[0].area * 0.05 and p.area >= 500]
    final = np.isin(lbl, keep).astype(bool)
    masks.append(final)

mA, mB, mC = masks

# Check the distribution of detected pixels along columns (east of dam, col > 1300)
print(f"Total water pixels in study box:")
for i, name in enumerate(DATES):
    tot = masks[i].sum()
    east_dam = masks[i][:, 1315:].sum()
    print(f"  {name}: Total = {tot*1e-4:.2f} km², East of col 1315 = {east_dam*1e-4:.4f} km² ({east_dam} px)")

# Breakdown of the 7 classes east of col 1315
only_C = (~mA) & (~mB) & mC
print(f"\nOnly Nov 2026 total: {only_C.sum()*1e-4:.2f} km²")
print(f"Only Nov 2026 east of col 1315: {only_C[:, 1315:].sum()*1e-4:.4f} km² ({only_C[:, 1315:].sum()} px)")
print(f"Only Nov 2026 west of col 1315: {only_C[:, :1315].sum()*1e-4:.4f} km² ({only_C[:, :1315].sum()} px)")

# Find where the pixels in only_C are located!
r_idx, c_idx = np.where(only_C)
lons, lats = [], []
for r, c in zip(r_idx, c_idx):
    ux = x_coords[c0 + c]
    uy = y_coords[r0 + r]
    lon, lat = to_ll.transform(ux, uy)
    lons.append(lon)
    lats.append(lat)

print(f"\nSpatial range of Only Nov 2026 pixels:")
print(f"  Rows (in study box): {r_idx.min()} to {r_idx.max()} (global rows {r0+r_idx.min()} to {r0+r_idx.max()})")
print(f"  Cols (in study box): {c_idx.min()} to {c_idx.max()} (global cols {c0+c_idx.min()} to {c0+c_idx.max()})")
print(f"  Lat range: {min(lats):.4f} to {max(lats):.4f}")
print(f"  Lon range: {min(lons):.4f} to {max(lons):.4f}")
