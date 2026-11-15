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

# Define dam crest wall vertices
dam_wall_lonlat = [
    (76.5700, 12.380),   # South boundary of study box
    (76.5700, 12.415),   # South approach
    (76.5705, 12.418),   # South abutment
    (76.5712, 12.422),   
    (76.5718, 12.426),   # Main sluices
    (76.5725, 12.431),   
    (76.5726, 12.435),   # North spillway
    (76.5722, 12.438),   # North abutment / hill contact
    (76.5722, 12.530)    # North boundary of study box
]

# Interpolate dam wall column for every row in the study box
h_box = r1 - r0
w_box = c1 - c0

# Convert vertices to row, col
pts = []
for lon, lat in dam_wall_lonlat:
    ux, uy = to_utm.transform(lon, lat)
    c = (ux - x_coords[0]) / dx - c0
    r = (y_coords[0] - uy) / dx - r0
    pts.append((r, c))

pts = sorted(pts, key=lambda p: p[0]) # North to south (row 0 to h_box)

cutoff_col = np.zeros(h_box, dtype=np.float32)
for i in range(len(pts) - 1):
    r_a, c_a = pts[i]
    r_b, c_b = pts[i+1]
    r_start = max(0, int(np.floor(min(r_a, r_b))))
    r_end = min(h_box, int(np.ceil(max(r_a, r_b))))
    if r_end > r_start:
        for r in range(r_start, r_end):
            t = (r - r_a) / (r_b - r_a) if r_b != r_a else 0
            cutoff_col[r] = c_a + t * (c_b - c_a)

col_grid = np.tile(np.arange(w_box), (h_box, 1))
reservoir_mask = col_grid <= cutoff_col[:, None]

DATES = ["2025-11-23", "2026-08-14", "2026-11-06"]
clipped_masks = []
orig_masks = []

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
    orig_masks.append(final)
    
    # Clip to reservoir side only
    clipped = final & reservoir_mask
    clipped_masks.append(clipped)
    
    orig_area = final.sum() * 1e-4
    clip_area = clipped.sum() * 1e-4
    print(f"{DATES[i]}: Before clip = {orig_area:.2f} km² -> After clip = {clip_area:.2f} km² (Downstream removed: {orig_area - clip_area:.4f} km²)")

mA, mB, mC = clipped_masks

print("\n--- RECOMPUTED DISJOINT PARTITIONS (AFTER DAM CLIP) ---")
print(f"Total Date A (2025-11-23): {mA.sum()*1e-4:.2f} km²")
print(f"Total Date B (2026-08-14): {mB.sum()*1e-4:.2f} km²")
print(f"Total Date C (2026-11-06): {mC.sum()*1e-4:.2f} km²")

# 7 classes
c1 = mA & (~mB) & (~mC)
c2 = (~mA) & mB & (~mC)
c3 = (~mA) & (~mB) & mC
c4 = mA & mB & (~mC)
c5 = mA & (~mB) & mC
c6 = (~mA) & mB & mC
c7 = mA & mB & mC

print("\n7 Disjoint Classes:")
print(f"  1. Only 23 Nov 2025:                  {c1.sum()*1e-4:.2f} km²")
print(f"  2. Only 14 Aug 2026:                  {c2.sum()*1e-4:.2f} km²")
print(f"  3. Only 06 Nov 2026:                  {c3.sum()*1e-4:.2f} km²")
print(f"  4. Both 23 Nov 2025 & 14 Aug 2026:    {c4.sum()*1e-4:.2f} km²")
print(f"  5. Both 23 Nov 2025 & 06 Nov 2026:    {c5.sum()*1e-4:.2f} km²")
print(f"  6. Both 14 Aug 2026 & 06 Nov 2026:    {c6.sum()*1e-4:.2f} km²")
print(f"  7. In all three dates (Core):         {c7.sum()*1e-4:.2f} km²")

# Check sums
sumA = (c1.sum() + c4.sum() + c5.sum() + c7.sum()) * 1e-4
sumB = (c2.sum() + c4.sum() + c6.sum() + c7.sum()) * 1e-4
sumC = (c3.sum() + c5.sum() + c6.sum() + c7.sum()) * 1e-4

print(f"\nSum Check: Date A = {sumA:.2f} km², Date B = {sumB:.2f} km², Date C = {sumC:.2f} km²")

# Pairwise
print("\nPairwise Partitions:")
print(f"Pair A & B: Only A = {(mA & ~mB).sum()*1e-4:.2f}, Only B = {(~mA & mB).sum()*1e-4:.2f}, Both = {(mA & mB).sum()*1e-4:.2f}")
print(f"Pair A & C: Only A = {(mA & ~mC).sum()*1e-4:.2f}, Only C = {(~mA & mC).sum()*1e-4:.2f}, Both = {(mA & mC).sum()*1e-4:.2f}")
print(f"Pair B & C: Only B = {(mB & ~mC).sum()*1e-4:.2f}, Only C = {(~mB & mC).sum()*1e-4:.2f}, Both = {(mB & mC).sum()*1e-4:.2f}")
