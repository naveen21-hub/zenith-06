import numpy as np
import os, glob
from pyproj import Transformer
from matplotlib.path import Path

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

# Define the dam wall barrier line in (Lon, Lat) from south of the reservoir to north
# The upstream reservoir water must be WEST of this line:
# Any pixel with lon > dam_lon(lat) is downstream and excluded.
dam_barrier_points = [
    (76.5710, 12.380),  # South border of study box
    (76.5710, 12.417),  # South abutment of KRS dam
    (76.5715, 12.422),
    (76.5720, 12.426),  # Central sluice gates
    (76.5728, 12.431),
    (76.5735, 12.435),  # North spillway
    (76.5738, 12.437),  # North abutment of KRS dam
    (76.5740, 12.450),  # North hills
    (76.5740, 12.530)   # North border of study box
]

# Convert barrier points to study-box pixel coordinates (col, row)
barrier_pix = []
for lon, lat in dam_barrier_points:
    ux, uy = to_utm.transform(lon, lat)
    c = (ux - x_coords[0]) / dx - c0
    r = (y_coords[0] - uy) / dx - r0
    barrier_pix.append((c, r))

# Sort by row (north to south)
barrier_pix = sorted(barrier_pix, key=lambda p: p[1])

# Build an exclusion mask for downstream (east of dam line)
# For each row r in the study box, compute the cutoff column c_dam(r)
# by linear interpolation along the barrier segments
h_box = r1 - r0
w_box = c1 - c0
c_cutoff = np.full(h_box, w_box, dtype=np.float32)

for i in range(len(barrier_pix) - 1):
    c_a, r_a = barrier_pix[i]
    c_b, r_b = barrier_pix[i+1]
    
    r_start = max(0, int(np.floor(min(r_a, r_b))))
    r_end = min(h_box, int(np.ceil(max(r_a, r_b))))
    
    if r_end > r_start:
        for r in range(r_start, r_end):
            # Interp c at this r
            t = (r - r_a) / (r_b - r_a) if r_b != r_a else 0
            c_interp = c_a + t * (c_b - c_a)
            c_cutoff[r] = min(c_cutoff[r], c_interp)

# Reservoir mask: keep only col <= c_cutoff[row]
col_grid = np.tile(np.arange(w_box), (h_box, 1))
reservoir_valid_mask = col_grid <= c_cutoff[:, None]

print(f"Study box dimensions: {h_box} rows x {w_box} cols")
print(f"Downstream pixels excluded: {(~reservoir_valid_mask).sum()} ({((~reservoir_valid_mask).sum()*1e-4):.2f} km²)")

# Check how many water pixels are removed for each date
from scipy.ndimage import median_filter, binary_fill_holes
from skimage.measure import label, regionprops

DATES = ["2025-11-23", "2026-08-14", "2026-11-06"]
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
    
    orig_area = final.sum() * 1e-4
    clipped = final & reservoir_valid_mask
    clipped_area = clipped.sum() * 1e-4
    diff = orig_area - clipped_area
    print(f"{DATES[i]}: Before clip = {orig_area:.2f} km² -> After clip = {clipped_area:.2f} km² (Removed downstream = {diff:.4f} km²)")
