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

d0 = np.load(npz_files[0])
hh = d0['HHHH'][r0:r1, c0:c1].astype(np.float32)
db = 10.0 * np.log10(np.where(hh > 0, hh, np.nan))
db = np.nan_to_num(db, nan=-30.0)
filt = median_filter(db, size=5)
raw = filt < -16.0
filled = binary_fill_holes(raw).astype(np.uint8)
lbl = label(filled)
props = sorted(regionprops(lbl), key=lambda p: p.area, reverse=True)
keep = [p.label for p in props if p.area >= props[0].area * 0.05 and p.area >= 500]
m2025 = np.isin(lbl, keep).astype(bool)

# For each latitude slice between 12.415 and 12.440, find the easternmost water pixel in Nov 2025
print("Nov 2025 easternmost water pixel along dam latitude range:")
for lat in np.arange(12.415, 12.440, 0.002):
    # Find rows corresponding to lat +- 0.001
    ux_ref, uy_ref = to_utm.transform(76.570, lat)
    r_target = int((y_coords[0] - uy_ref) / dx) - r0
    row_slice = m2025[max(0, r_target-5):min(m2025.shape[0], r_target+5), :]
    cols = np.where(row_slice)[1]
    if len(cols) > 0:
        max_c = cols.max()
        ux_max = x_coords[c0 + max_c]
        uy_max = y_coords[r0 + r_target]
        lon_max, lat_actual = to_ll.transform(ux_max, uy_max)
        print(f"  Lat ~ {lat:.3f}: Max Lon = {lon_max:.5f} (c={max_c})")
