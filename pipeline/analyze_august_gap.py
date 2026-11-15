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
pixel_area_km2 = (dx * dx) * 1e-6

BOX_LON = (76.445, 76.585)
BOX_LAT = (12.380, 12.530)
ux0, uy0 = to_utm.transform(BOX_LON[0], BOX_LAT[0])
ux1, uy1 = to_utm.transform(BOX_LON[1], BOX_LAT[1])
c0 = max(0, int((ux0 - x_coords[0]) / dx))
c1 = min(len(x_coords), int((ux1 - x_coords[0]) / dx))
r0 = max(0, int((y_coords[0] - uy1) / dx))
r1 = min(len(y_coords), int((y_coords[0] - uy0) / dx))

# Dam barrier polyline to clip downstream pixels
dam_wall_lonlat = [
    (76.5700, 12.380), (76.5700, 12.415), (76.5705, 12.418), (76.5712, 12.422),
    (76.5718, 12.426), (76.5725, 12.431), (76.5726, 12.435), (76.5722, 12.438),
    (76.5722, 12.530)
]
h_box = r1 - r0
w_box = c1 - c0
barrier_pts = []
for lon, lat in dam_wall_lonlat:
    ux, uy = to_utm.transform(lon, lat)
    c = (ux - x_coords[0]) / dx - c0
    r = (y_coords[0] - uy) / dx - r0
    barrier_pts.append((r, c))
barrier_pts = sorted(barrier_pts, key=lambda p: p[0])

cutoff_col = np.zeros(h_box, dtype=np.float32)
for i in range(len(barrier_pts) - 1):
    r_a, c_a = barrier_pts[i]
    r_b, c_b = barrier_pts[i+1]
    r_start = max(0, int(np.floor(min(r_a, r_b))))
    r_end = min(h_box, int(np.ceil(max(r_a, r_b))))
    if r_end > r_start:
        for r in range(r_start, r_end):
            t = (r - r_a) / (r_b - r_a) if r_b != r_a else 0
            cutoff_col[r] = c_a + t * (c_b - c_a)

col_grid = np.tile(np.arange(w_box), (h_box, 1))
reservoir_mask = col_grid <= cutoff_col[:, None]

DATES = ["2025-11-23", "2026-08-14", "2026-11-06"]

# Load HH and HV data
hh_crops = []
hv_crops = []
hh_db_crops = []
hv_db_crops = []
hh_filt_crops = []
final_masks = []

for f in npz_files:
    d = np.load(f)
    # HH
    hh = d['HHHH'][r0:r1, c0:c1].astype(np.float32)
    hh_db = 10.0 * np.log10(np.where(hh > 0, hh, np.nan))
    hh_db = np.nan_to_num(hh_db, nan=-30.0)
    hh_filt = median_filter(hh_db, size=5)
    
    # HV
    hv = d['HVHV'][r0:r1, c0:c1].astype(np.float32)
    hv_db = 10.0 * np.log10(np.where(hv > 0, hv, np.nan))
    hv_db = np.nan_to_num(hv_db, nan=-35.0)
    
    hh_crops.append(hh)
    hv_crops.append(hv)
    hh_db_crops.append(hh_db)
    hv_db_crops.append(hv_db)
    hh_filt_crops.append(hh_filt)
    
    # Standard mask at -16 dB
    raw = hh_filt < -16.0
    filled = binary_fill_holes(raw).astype(np.uint8)
    lbl = label(filled)
    props = sorted(regionprops(lbl), key=lambda p: p.area, reverse=True)
    keep = [p.label for p in props if p.area >= props[0].area * 0.05 and p.area >= 500]
    final = np.isin(lbl, keep).astype(bool) & reservoir_mask
    final_masks.append(final)

mA, mB, mC = final_masks

# -------------------------------------------------------------
# Part 1: Analysis of the 4.92 km² patch (Water in Nov 25 & Nov 26, NOT in Aug 26)
# -------------------------------------------------------------
patch_492 = mA & (~mB) & mC
patch_px = patch_492.sum()
patch_km2 = patch_px * pixel_area_km2

print("================================================================================")
print(f"PART 1: AUDIT OF THE NEAR-DAM GAP PATCH (Water in Nov '25 & Nov '26, NOT Aug '26)")
print(f"Total Patch Area: {patch_km2:.2f} km² ({patch_px} pixels)")
print("================================================================================")

for i, date in enumerate(DATES):
    vals_filt = hh_filt_crops[i][patch_492]
    vals_raw = hh_db_crops[i][patch_492]
    vals_hv = hv_db_crops[i][patch_492]
    
    med = np.median(vals_filt)
    mean = np.mean(vals_filt)
    p25 = np.percentile(vals_filt, 25)
    p75 = np.percentile(vals_filt, 75)
    std = np.std(vals_filt)
    
    print(f"\n--- {date} ---")
    print(f"  HH (Filtered) dB : Median = {med:.2f} dB, Mean = {mean:.2f} dB, IQR = [{p25:.2f}, {p75:.2f}] dB, Std = {std:.2f} dB")
    print(f"  HH (Raw) dB      : Median = {np.median(vals_raw):.2f} dB, Mean = {np.mean(vals_raw):.2f} dB, Std = {np.std(vals_raw):.2f} dB")
    print(f"  HV (Raw) dB      : Median = {np.median(vals_hv):.2f} dB, Mean = {np.mean(vals_hv):.2f} dB, Std = {np.std(vals_hv):.2f} dB")
    
    # Histogram distribution
    bins = [-np.inf, -22, -20, -18, -16, -14, -12, -10, np.inf]
    counts, _ = np.histogram(vals_filt, bins=bins)
    print("  HH dB Bins (% of patch):")
    for b_idx in range(len(counts)):
        b_low = bins[b_idx]
        b_high = bins[b_idx+1]
        pct = (counts[b_idx] / patch_px) * 100
        print(f"    [{b_low:5.0f} to {b_high:5.0f} dB]: {pct:5.1f}% ({counts[b_idx]} px)")

# Delta comparison
med_A = np.median(hh_filt_crops[0][patch_492])
med_B = np.median(hh_filt_crops[1][patch_492])
med_C = np.median(hh_filt_crops[2][patch_492])

print("\n--- BRIGHTNESS DIFFERENCE IN PATCH ---")
print(f"August 2026 Median: {med_B:.2f} dB")
print(f"Nov 2025 Median   : {med_A:.2f} dB  --> August is brighter by {med_B - med_A:+.2f} dB")
print(f"Nov 2026 Median   : {med_C:.2f} dB  --> August is brighter by {med_B - med_C:+.2f} dB")

print("\n--- THRESHOLD TEST ON THE 4.92 km² PATCH ---")
print("Threshold (dB) | 23 Nov 2025 (%) | 14 Aug 2026 (%) | 06 Nov 2026 (%) | 14 Aug Detected Area")
for t in [-20.0, -18.0, -16.0, -14.0]:
    det_A = (hh_filt_crops[0][patch_492] < t).mean() * 100
    det_B = (hh_filt_crops[1][patch_492] < t).mean() * 100
    det_C = (hh_filt_crops[2][patch_492] < t).mean() * 100
    det_B_km2 = (hh_filt_crops[1][patch_492] < t).sum() * pixel_area_km2
    print(f"   {t:5.1f} dB    |     {det_A:5.1f}%     |     {det_B:5.1f}%     |     {det_C:5.1f}%     |  {det_B_km2:.2f} km²")

# -------------------------------------------------------------
# Part 2: Total Study Box Water Area Sensitivity Table (HH & HV)
# -------------------------------------------------------------
print("\n================================================================================")
print("PART 2: TOTAL WATER AREA (km², WITHIN STUDY BOX) ACROSS THRESHOLDS")
print("================================================================================")

def compute_water_area(grid_db, threshold):
    raw = grid_db < threshold
    filled = binary_fill_holes(raw).astype(np.uint8)
    lbl = label(filled)
    props = sorted(regionprops(lbl), key=lambda p: p.area, reverse=True)
    if not props:
        return 0.0
    keep = [p.label for p in props if p.area >= props[0].area * 0.05 and p.area >= 500]
    final = np.isin(lbl, keep).astype(bool) & reservoir_mask
    return round(float(final.sum()) * pixel_area_km2, 2)

print("\n[HH Polarization] Water Area vs Fixed Threshold:")
print("Threshold | 23 Nov 2025 | 14 Aug 2026 | 06 Nov 2026 | Aug < Nov 2025? | Aug < Nov 2026?")
for t in [-14.0, -16.0, -18.0, -20.0]:
    aA = compute_water_area(hh_filt_crops[0], t)
    aB = compute_water_area(hh_filt_crops[1], t)
    aC = compute_water_area(hh_filt_crops[2], t)
    print(f" {t:5.1f} dB |  {aA:6.2f} km² |  {aB:6.2f} km² |  {aC:6.2f} km² |      {str(aB < aA):5}      |      {str(aB < aC):5}")

print("\n[HV Polarization] Water Area vs Fixed Threshold:")
# HV filter
hv_filt_crops = [median_filter(hv_db, size=5) for hv_db in hv_db_crops]
print("Threshold | 23 Nov 2025 | 14 Aug 2026 | 06 Nov 2026 | Aug < Nov 2025? | Aug < Nov 2026?")
for t in [-14.0, -16.0, -18.0, -20.0, -22.0, -24.0]:
    aA = compute_water_area(hv_filt_crops[0], t)
    aB = compute_water_area(hv_filt_crops[1], t)
    aC = compute_water_area(hv_filt_crops[2], t)
    print(f" {t:5.1f} dB |  {aA:6.2f} km² |  {aB:6.2f} km² |  {aC:6.2f} km² |      {str(aB < aA):5}      |      {str(aB < aC):5}")
