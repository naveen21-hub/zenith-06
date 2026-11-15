import numpy as np
import os, glob
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

npz_files = sorted(glob.glob(os.path.join(DB_DIR, "*.npz")))
ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
epsg = int(ref['epsg'])

print("=== 1. COORDINATE SPACING VERIFICATION ===")
print(f"EPSG: {epsg} (UTM Zone 43N, meters)")
print(f"Number of X coords: {len(x_coords)}")
print(f"Number of Y coords: {len(y_coords)}")

# Check spacing across all points
dx_all = np.diff(x_coords)
dy_all = np.diff(y_coords)

print(f"dx: min = {dx_all.min():.6f} m, max = {dx_all.max():.6f} m, mean = {dx_all.mean():.6f} m")
print(f"dy: min = {dy_all.min():.6f} m, max = {dy_all.max():.6f} m, mean = {dy_all.mean():.6f} m")
print(f"Is dx exactly 10.0 m everywhere? {np.allclose(dx_all, 10.0)}")
print(f"Is dy exactly -10.0 m everywhere? {np.allclose(dy_all, -10.0)}")

# Pixel area
pixel_area_m2 = abs(dx_all[0] * dy_all[0])
print(f"Exact Pixel Area: {pixel_area_m2:.6f} m² = {pixel_area_m2 * 1e-6:.8f} km²")

print("\n=== 2. RESERVOIR TRUNCATION VS FRL RECOMPUTATION ===")
# Official KRS Dam parameters:
# Full Reservoir Level (FRL): 124.80 ft (38.04 m)
# Gross Storage Capacity: 49.452 TMC (1,399.8 MCM)
# Live Storage Capacity: 45.07 TMC
# Published Water-Spread Area at FRL: ~129.5 km² (50.0 sq miles / ~128.5 to 130 km²)
frl_area_km2 = 129.5

# Detected water area in Nov 2025 within our study box:
# 77.93 km²
study_box_nov25_area = 77.93
pct_of_frl = (study_box_nov25_area / frl_area_km2) * 100
unobserved_pct = 100.0 - pct_of_frl

print(f"Published KRS FRL Water Spread Area: ~{frl_area_km2:.1f} km²")
print(f"Detected Nov 2025 Water Area in Study Box: {study_box_nov25_area:.2f} km²")
print(f"Percentage of FRL captured in Study Box: {pct_of_frl:.1f}%")
print(f"Unobserved / Clipped percentage of FRL Area: {unobserved_pct:.1f}% (~40% of FRL area)")

# Now check where the old "~32%" came from:
# KRS reservoir westernmost tail reaches ~76.350°E (near Akkihebbalu / Hemavathi confluence)
# Dam wall is at ~76.572°E.
# Total longitudinal length: 76.572 - 76.350 = 0.222 degrees (~24.0 km)
# Our study box western boundary: 76.445°E (or raw scene boundary: 76.450°E)
# Truncated longitudinal length: 76.450 - 76.350 = 0.100 degrees (~10.8 km)
# Linear longitudinal truncation percentage: (0.100 / 0.222) * 100 = 45%
# Or if measured across the full NISAR frame bbox [76.35 to 76.70]: (0.450 - 0.350) / 0.350 = 28-32%
linear_pct = (76.450 - 76.350) / (76.572 - 76.350) * 100
print(f"\nLongitudinal East-West Truncation:")
print(f"  Full reservoir longitude span: 76.350°E to 76.572°E (0.222° ~ 24.1 km)")
print(f"  Clipped western inflow span: 76.350°E to 76.450°E (0.100° ~ 10.9 km)")
print(f"  Linear E-W length clipped: {linear_pct:.1f}%")
print(f"\nConclusion on '~32%' vs '~60% of FRL':")
print(f"  - In terms of SURFACE AREA: The study box captures 60.2% of FRL (77.93 km² / 129.5 km²).")
print(f"    Therefore, the clipped/unobserved portion is ~40% of the reservoir's full water spread area.")
print(f"  - The old text conflated a ~32% linear length estimate with area. The area clipped is ~40%, meaning the study box captures ~60% of the full reservoir.")
