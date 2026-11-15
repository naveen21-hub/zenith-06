"""
Stage 1: Multi-Epoch Overlap Pipeline for Karnataka Water Watch
Generates:
1. Single-date fills in distinct Wong/Okabe-Ito colors (#0072B2, #E69F00, #009E73)
2. 2px outline PNGs per date
3. Pairwise overlap classification PNGs (3 files)
4. Full three-epoch 7-class disjoint partition PNG (1 file)
5. web/data/overlap.json with complete metadata, areas, legends, and sanity checks.
"""
import numpy as np
import os, glob, json, time
from PIL import Image
from scipy.ndimage import median_filter, binary_fill_holes, binary_dilation
from skimage.measure import label, regionprops
from skimage.segmentation import find_boundaries
from pyproj import Transformer

t0 = time.time()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")
OVERLAYS_DIR = os.path.join(BASE_DIR, "web", "overlays")
DATA_DIR = os.path.join(BASE_DIR, "web", "data")
PLOTS_DIR = os.path.join(BASE_DIR, "web", "plots")

os.makedirs(OVERLAYS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# Coords & study box
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

BOX_LON = (76.445, 76.585)
BOX_LAT = (12.380, 12.530)
THRESHOLD_DB = -16.0

npz_files = sorted(glob.glob(os.path.join(DB_DIR, "*.npz")))
assert len(npz_files) == 3, f"Expected 3 npz files, found {len(npz_files)}"

ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
ny, nx = len(y_coords), len(x_coords)
dx = abs(float(x_coords[1] - x_coords[0]))  # 10m
pixel_area_km2 = (dx * dx) * 1e-6  # 0.0001 km²

ux0, uy0 = to_utm.transform(BOX_LON[0], BOX_LAT[0])
ux1, uy1 = to_utm.transform(BOX_LON[1], BOX_LAT[1])
c0 = max(0, int((ux0 - x_coords[0]) / dx))
c1 = min(nx, int((ux1 - x_coords[0]) / dx))
r0 = max(0, int((y_coords[0] - uy1) / dx))
r1 = min(ny, int((y_coords[0] - uy0) / dx))

# Dam barrier polyline to clip downstream pixels east of the dam wall
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
LABELS = ["23 Nov 2025", "14 Aug 2026", "06 Nov 2026"]

# Exact Palette (Hex -> RGBA with opacity 215/255 for fill, 255 for outline)
COLORS = {
    "date1": {"hex": "#0072B2", "rgb": [0, 114, 178], "alpha": 215},    # Deep Blue
    "date2": {"hex": "#E69F00", "rgb": [230, 159, 0], "alpha": 215},    # Orange
    "date3": {"hex": "#009E73", "rgb": [0, 158, 115], "alpha": 215},    # Green
    "both_1_2": {"hex": "#CC79A7", "rgb": [204, 121, 167], "alpha": 220}, # Reddish Purple
    "both_1_3": {"hex": "#00E5FF", "rgb": [0, 229, 255], "alpha": 220},  # High-Contrast Electric Cyan (Distinct from #0072B2)
    "both_2_3": {"hex": "#D55E00", "rgb": [213, 94, 0], "alpha": 220},   # Vermilion
    "all_three": {"hex": "#2B2D42", "rgb": [43, 45, 66], "alpha": 75}     # Semi-transparent Slate (Preserves satellite water texture)
}

# 1. Generate full-resolution water masks
full_masks = []
study_box_masks = []
areas_km2 = []

for i, f in enumerate(npz_files):
    d = np.load(f)
    hh = d['HHHH'][r0:r1, c0:c1].astype(np.float32)
    db = 10.0 * np.log10(np.where(hh > 0, hh, np.nan))
    db = np.nan_to_num(db, nan=-30.0)
    filt = median_filter(db, size=5)
    raw = filt < THRESHOLD_DB
    filled = binary_fill_holes(raw).astype(np.uint8)
    lbl = label(filled)
    props = sorted(regionprops(lbl), key=lambda p: p.area, reverse=True)
    keep = [p.label for p in props if p.area >= props[0].area * 0.05 and p.area >= 500]
    final = np.isin(lbl, keep).astype(bool)
    
    # Clip downstream pixels east of KRS dam wall
    final = final & reservoir_mask
    
    fm = np.zeros((ny, nx), dtype=bool)
    fm[r0:r1, c0:c1] = final
    full_masks.append(fm)
    study_box_masks.append(final)
    
    area = round(float(final.sum()) * pixel_area_km2, 4)
    areas_km2.append(area)
    print(f"Loaded {DATES[i]}: {area:.2f} km² (within study box)")

# Grid size for 2x downsampled web overlays
# Shape: (ny//2, nx//2) = (1114, 1352) or (1115, 1353)
m_2x_list = [m[::2, ::2] for m in full_masks]
h2, w2 = m_2x_list[0].shape

def save_overlay(rgba_arr, filename):
    img = Image.fromarray(rgba_arr, 'RGBA')
    path = os.path.join(OVERLAYS_DIR, filename)
    img.save(path, optimize=True)
    print(f"  Saved {filename} ({w2}x{h2})")

print("\n--- 1. Exporting Single-Date Fills ---")
fill_files = {}
for i, date in enumerate(DATES):
    key = f"date{i+1}"
    c = COLORS[key]
    rgba = np.zeros((h2, w2, 4), dtype=np.uint8)
    rgba[m_2x_list[i]] = c["rgb"] + [c["alpha"]]
    fn = f"fill_{date}.png"
    save_overlay(rgba, fn)
    fill_files[date] = fn

print("\n--- 2. Exporting 2px Shoreline Outlines ---")
outline_files = {}
for i, date in enumerate(DATES):
    key = f"date{i+1}"
    c = COLORS[key]
    # Fast 2px outline: find_boundaries + 1 iteration dilation
    boundary = find_boundaries(m_2x_list[i], mode='inner')
    outline_2px = binary_dilation(boundary, iterations=1)
    
    rgba = np.zeros((h2, w2, 4), dtype=np.uint8)
    rgba[outline_2px] = c["rgb"] + [255]  # Full alpha for crisp outline
    fn = f"outline_{date}.png"
    save_overlay(rgba, fn)
    outline_files[date] = fn

# Boolean algebra on 2x masks for overlays
mA_2x, mB_2x, mC_2x = m_2x_list
# Full-resolution masks for exact area accounting
mA, mB, mC = study_box_masks

print("\n--- 3. Exporting Pairwise Overlap Fills ---")
# Pair (2025-11-23, 2026-08-14)
p1_fn = f"overlap_{DATES[0]}_{DATES[1]}.png"
rgba_p1 = np.zeros((h2, w2, 4), dtype=np.uint8)
rgba_p1[mA_2x & (~mB_2x)] = COLORS["date1"]["rgb"] + [COLORS["date1"]["alpha"]]
rgba_p1[mB_2x & (~mA_2x)] = COLORS["date2"]["rgb"] + [COLORS["date2"]["alpha"]]
rgba_p1[mA_2x & mB_2x]     = COLORS["both_1_2"]["rgb"] + [COLORS["both_1_2"]["alpha"]]
save_overlay(rgba_p1, p1_fn)

# Pair (2025-11-23, 2026-11-06)
p2_fn = f"overlap_{DATES[0]}_{DATES[2]}.png"
rgba_p2 = np.zeros((h2, w2, 4), dtype=np.uint8)
rgba_p2[mA_2x & (~mC_2x)] = COLORS["date1"]["rgb"] + [COLORS["date1"]["alpha"]]
rgba_p2[mC_2x & (~mA_2x)] = COLORS["date3"]["rgb"] + [COLORS["date3"]["alpha"]]
rgba_p2[mA_2x & mC_2x]     = COLORS["both_1_3"]["rgb"] + [COLORS["both_1_3"]["alpha"]]
save_overlay(rgba_p2, p2_fn)

# Pair (2026-08-14, 2026-11-06)
p3_fn = f"overlap_{DATES[1]}_{DATES[2]}.png"
rgba_p3 = np.zeros((h2, w2, 4), dtype=np.uint8)
rgba_p3[mB_2x & (~mC_2x)] = COLORS["date2"]["rgb"] + [COLORS["date2"]["alpha"]]
rgba_p3[mC_2x & (~mB_2x)] = COLORS["date3"]["rgb"] + [COLORS["date3"]["alpha"]]
rgba_p3[mB_2x & mC_2x]     = COLORS["both_2_3"]["rgb"] + [COLORS["both_2_3"]["alpha"]]
save_overlay(rgba_p3, p3_fn)

print("\n--- 4. Exporting All-Three 7-Class Overlap Fill ---")
all_fn = "overlap_all_three.png"
rgba_all = np.zeros((h2, w2, 4), dtype=np.uint8)
# 7 disjoint classes
c1 = mA_2x & (~mB_2x) & (~mC_2x)
c2 = mB_2x & (~mA_2x) & (~mC_2x)
c3 = mC_2x & (~mA_2x) & (~mB_2x)
c4 = (mA_2x & mB_2x) & (~mC_2x)
c5 = (mA_2x & mC_2x) & (~mB_2x)
c6 = (mB_2x & mC_2x) & (~mA_2x)
c7 = mA_2x & mB_2x & mC_2x

rgba_all[c1] = COLORS["date1"]["rgb"] + [COLORS["date1"]["alpha"]]
rgba_all[c2] = COLORS["date2"]["rgb"] + [COLORS["date2"]["alpha"]]
rgba_all[c3] = COLORS["date3"]["rgb"] + [COLORS["date3"]["alpha"]]
rgba_all[c4] = COLORS["both_1_2"]["rgb"] + [COLORS["both_1_2"]["alpha"]]
rgba_all[c5] = COLORS["both_1_3"]["rgb"] + [COLORS["both_1_3"]["alpha"]]
rgba_all[c6] = COLORS["both_2_3"]["rgb"] + [COLORS["both_2_3"]["alpha"]]
rgba_all[c7] = COLORS["all_three"]["rgb"] + [COLORS["all_three"]["alpha"]]
save_overlay(rgba_all, all_fn)

print("\n--- 5. Computing True Areas (km², within study box) & Sanity Check ---")
def get_area(mask):
    return round(float(mask.sum()) * pixel_area_km2, 2)

# Full resolution exact class areas
area_A = get_area(mA)
area_B = get_area(mB)
area_C = get_area(mC)

# Pairwise breakdown
pair_1_2_data = {
    "only_A": get_area(mA & (~mB)),
    "only_B": get_area(mB & (~mA)),
    "both": get_area(mA & mB)
}

pair_1_3_data = {
    "only_A": get_area(mA & (~mC)),
    "only_C": get_area(mC & (~mA)),
    "both": get_area(mA & mC)
}

pair_2_3_data = {
    "only_B": get_area(mB & (~mC)),
    "only_C": get_area(mC & (~mB)),
    "both": get_area(mB & mC)
}

# 7-class breakdown
all_three_data = {
    "only_A": get_area(mA & (~mB) & (~mC)),
    "only_B": get_area(mB & (~mA) & (~mC)),
    "only_C": get_area(mC & (~mA) & (~mB)),
    "both_AB_only": get_area((mA & mB) & (~mC)),
    "both_AC_only": get_area((mA & mC) & (~mB)),
    "both_BC_only": get_area((mB & mC) & (~mA)),
    "all_three": get_area(mA & mB & mC)
}

# Area Sanity Check Table
print("=" * 80)
print("SANITY CHECK: Disjoint Partition Areas vs. Total Date Areas (km²)")
print("=" * 80)
print(f"Total Date A (23 Nov 2025): {area_A:.2f} km²")
print(f"Total Date B (14 Aug 2026): {area_B:.2f} km²")
print(f"Total Date C (06 Nov 2026): {area_C:.2f} km²")
print("-" * 80)

# Check Pair A & B
sum_pair_A = round(pair_1_2_data["only_A"] + pair_1_2_data["both"], 2)
sum_pair_B = round(pair_1_2_data["only_B"] + pair_1_2_data["both"], 2)
print(f"Pair [2025-11-23, 2026-08-14]:")
print(f"  Only 2025-11-23: {pair_1_2_data['only_A']:.2f} km² | Only 2026-08-14: {pair_1_2_data['only_B']:.2f} km² | Both: {pair_1_2_data['both']:.2f} km²")
print(f"  Sum for Date A: {sum_pair_A:.2f} km² (matches {area_A:.2f}: {abs(sum_pair_A - area_A) < 0.02})")
print(f"  Sum for Date B: {sum_pair_B:.2f} km² (matches {area_B:.2f}: {abs(sum_pair_B - area_B) < 0.02})")

# Check Pair A & C
sum_pair_A_c = round(pair_1_3_data["only_A"] + pair_1_3_data["both"], 2)
sum_pair_C_c = round(pair_1_3_data["only_C"] + pair_1_3_data["both"], 2)
print(f"\nPair [2025-11-23, 2026-11-06]:")
print(f"  Only 2025-11-23: {pair_1_3_data['only_A']:.2f} km² | Only 2026-11-06: {pair_1_3_data['only_C']:.2f} km² | Both: {pair_1_3_data['both']:.2f} km²")
print(f"  Sum for Date A: {sum_pair_A_c:.2f} km² (matches {area_A:.2f}: {abs(sum_pair_A_c - area_A) < 0.02})")
print(f"  Sum for Date C: {sum_pair_C_c:.2f} km² (matches {area_C:.2f}: {abs(sum_pair_C_c - area_C) < 0.02})")

# Check Pair B & C
sum_pair_B_bc = round(pair_2_3_data["only_B"] + pair_2_3_data["both"], 2)
sum_pair_C_bc = round(pair_2_3_data["only_C"] + pair_2_3_data["both"], 2)
print(f"\nPair [2026-08-14, 2026-11-06]:")
print(f"  Only 2026-08-14: {pair_2_3_data['only_B']:.2f} km² | Only 2026-11-06: {pair_2_3_data['only_C']:.2f} km² | Both: {pair_2_3_data['both']:.2f} km²")
print(f"  Sum for Date B: {sum_pair_B_bc:.2f} km² (matches {area_B:.2f}: {abs(sum_pair_B_bc - area_B) < 0.02})")
print(f"  Sum for Date C: {sum_pair_C_bc:.2f} km² (matches {area_C:.2f}: {abs(sum_pair_C_bc - area_C) < 0.02})")

# Check All Three
sum_all_A = round(all_three_data["only_A"] + all_three_data["both_AB_only"] + all_three_data["both_AC_only"] + all_three_data["all_three"], 2)
sum_all_B = round(all_three_data["only_B"] + all_three_data["both_AB_only"] + all_three_data["both_BC_only"] + all_three_data["all_three"], 2)
sum_all_C = round(all_three_data["only_C"] + all_three_data["both_AC_only"] + all_three_data["both_BC_only"] + all_three_data["all_three"], 2)

print(f"\nAll Three [2025-11-23, 2026-08-14, 2026-11-06]:")
print(f"  Only 23 Nov 2025:                  {all_three_data['only_A']:.2f} km²")
print(f"  Only 14 Aug 2026:                  {all_three_data['only_B']:.2f} km²")
print(f"  Only 06 Nov 2026:                  {all_three_data['only_C']:.2f} km²")
print(f"  Both 23 Nov 2025 & 14 Aug 2026 only: {all_three_data['both_AB_only']:.2f} km²")
print(f"  Both 23 Nov 2025 & 06 Nov 2026 only: {all_three_data['both_AC_only']:.2f} km²")
print(f"  Both 14 Aug 2026 & 06 Nov 2026 only: {all_three_data['both_BC_only']:.2f} km²")
print(f"  In All Three Dates (Core):         {all_three_data['all_three']:.2f} km²")
print(f"  Sum for Date A: {sum_all_A:.2f} km² (matches {area_A:.2f}: {abs(sum_all_A - area_A) < 0.02})")
print(f"  Sum for Date B: {sum_all_B:.2f} km² (matches {area_B:.2f}: {abs(sum_all_B - area_B) < 0.02})")
print(f"  Sum for Date C: {sum_all_C:.2f} km² (matches {area_C:.2f}: {abs(sum_all_C - area_C) < 0.02})")
print("=" * 80)

# 6. Build and write web/data/overlap.json
overlap_json_payload = {
    "project": "Karnataka Water Watch",
    "target": "KRS Reservoir, Mandya, Karnataka",
    "spatial_resolution_m": 10.0,
    "threshold_dB": THRESHOLD_DB,
    "note": "All statistics are strictly within the study box (lon 76.445–76.585, lat 12.380–12.530).",
    "bounds": [[12.350016, 76.450005], [12.549971, 76.699940]],
    "dates": {
        "2025-11-23": {"label": "23 Nov 2025", "color": COLORS["date1"]["hex"], "area_km2": area_A, "outline_png": outline_files["2025-11-23"], "fill_png": fill_files["2025-11-23"]},
        "2026-08-14": {"label": "14 Aug 2026", "color": COLORS["date2"]["hex"], "area_km2": area_B, "outline_png": outline_files["2026-08-14"], "fill_png": fill_files["2026-08-14"]},
        "2026-11-06": {"label": "06 Nov 2026", "color": COLORS["date3"]["hex"], "area_km2": area_C, "outline_png": outline_files["2026-11-06"], "fill_png": fill_files["2026-11-06"]}
    },
    "combinations": {
        "2025-11-23": {
            "dates": ["2025-11-23"],
            "fill_png": fill_files["2025-11-23"],
            "classes": [
                {"label": "Water on 23 Nov 2025", "color": COLORS["date1"]["hex"], "area_km2": area_A}
            ]
        },
        "2026-08-14": {
            "dates": ["2026-08-14"],
            "fill_png": fill_files["2026-08-14"],
            "classes": [
                {"label": "Water on 14 Aug 2026", "color": COLORS["date2"]["hex"], "area_km2": area_B}
            ]
        },
        "2026-11-06": {
            "dates": ["2026-11-06"],
            "fill_png": fill_files["2026-11-06"],
            "classes": [
                {"label": "Water on 06 Nov 2026", "color": COLORS["date3"]["hex"], "area_km2": area_C}
            ]
        },
        "2025-11-23+2026-08-14": {
            "dates": ["2025-11-23", "2026-08-14"],
            "fill_png": p1_fn,
            "classes": [
                {"label": "Water on 23 Nov 2025 only", "color": COLORS["date1"]["hex"], "area_km2": pair_1_2_data["only_A"]},
                {"label": "Water on 14 Aug 2026 only", "color": COLORS["date2"]["hex"], "area_km2": pair_1_2_data["only_B"]},
                {"label": "Water on both 23 Nov 2025 & 14 Aug 2026", "color": COLORS["both_1_2"]["hex"], "area_km2": pair_1_2_data["both"]}
            ]
        },
        "2025-11-23+2026-11-06": {
            "dates": ["2025-11-23", "2026-11-06"],
            "fill_png": p2_fn,
            "classes": [
                {"label": "Water on 23 Nov 2025 only", "color": COLORS["date1"]["hex"], "area_km2": pair_1_3_data["only_A"]},
                {"label": "Water on 06 Nov 2026 only", "color": COLORS["date3"]["hex"], "area_km2": pair_1_3_data["only_C"]},
                {"label": "Water on both 23 Nov 2025 & 06 Nov 2026", "color": COLORS["both_1_3"]["hex"], "area_km2": pair_1_3_data["both"]}
            ]
        },
        "2026-08-14+2026-11-06": {
            "dates": ["2026-08-14", "2026-11-06"],
            "fill_png": p3_fn,
            "classes": [
                {"label": "Water on 14 Aug 2026 only", "color": COLORS["date2"]["hex"], "area_km2": pair_2_3_data["only_B"]},
                {"label": "Water on 06 Nov 2026 only", "color": COLORS["date3"]["hex"], "area_km2": pair_2_3_data["only_C"]},
                {"label": "Water on both 14 Aug 2026 & 06 Nov 2026", "color": COLORS["both_2_3"]["hex"], "area_km2": pair_2_3_data["both"]}
            ]
        },
        "2025-11-23+2026-08-14+2026-11-06": {
            "dates": ["2025-11-23", "2026-08-14", "2026-11-06"],
            "fill_png": all_fn,
            "classes": [
                {"label": "Water on 23 Nov 2025 only", "color": COLORS["date1"]["hex"], "area_km2": all_three_data["only_A"]},
                {"label": "Water on 14 Aug 2026 only", "color": COLORS["date2"]["hex"], "area_km2": all_three_data["only_B"]},
                {"label": "Water on 06 Nov 2026 only", "color": COLORS["date3"]["hex"], "area_km2": all_three_data["only_C"]},
                {"label": "Water on both 23 Nov 2025 & 14 Aug 2026 only", "color": COLORS["both_1_2"]["hex"], "area_km2": all_three_data["both_AB_only"]},
                {"label": "Water on both 23 Nov 2025 & 06 Nov 2026 only", "color": COLORS["both_1_3"]["hex"], "area_km2": all_three_data["both_AC_only"]},
                {"label": "Water on both 14 Aug 2026 & 06 Nov 2026 only", "color": COLORS["both_2_3"]["hex"], "area_km2": all_three_data["both_BC_only"]},
                {"label": "Water in all three dates", "color": COLORS["all_three"]["hex"], "area_km2": all_three_data["all_three"]}
            ]
        }
    }
}

overlap_json_path = os.path.join(DATA_DIR, "overlap.json")
with open(overlap_json_path, 'w') as f:
    json.dump(overlap_json_payload, f, indent=2)

print(f"\nWrote {overlap_json_path}")
print(f"Stage 1 Pipeline completed successfully in {time.time()-t0:.1f}s!")
