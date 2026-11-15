import numpy as np
import os, glob
from pyproj import Transformer
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

npz_files = sorted(glob.glob(os.path.join(DB_DIR, "*.npz")))
ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
dx = 10.0

# Nov 06 2026
d_nov26 = np.load(npz_files[2])
hh = d_nov26['HHHH'].astype(np.float32)
db = 10.0 * np.log10(np.where(hh > 0, hh, np.nan))
db = np.nan_to_num(db, nan=-30.0)

# Check region east of dam (lon: 76.570 to 76.585, lat: 12.410 to 12.445)
# Find where the dark pixels (db < -16) are located downstream
for lat in np.arange(12.415, 12.440, 0.005):
    for lon in np.arange(76.570, 76.585, 0.003):
        ux, uy = to_utm.transform(lon, lat)
        c = int((ux - x_coords[0]) / dx)
        r = int((y_coords[0] - uy) / dx)
        val = db[r, c]
        print(f"Lat: {lat:.3f}, Lon: {lon:.3f} (r={r}, c={c}) -> dB = {val:.2f}")

# Also check dam wall high backscatter:
# The masonry dam wall is a strong radar reflector (high dB > 0 or > -5 dB)
print("\nScanning across longitude at lat 12.425 for dam wall radar signature:")
lat = 12.425
for lon in np.linspace(76.565, 76.578, 20):
    ux, uy = to_utm.transform(lon, lat)
    c = int((ux - x_coords[0]) / dx)
    r = int((y_coords[0] - uy) / dx)
    val = db[r, c]
    print(f"  Lon: {lon:.5f} (c={c}) -> dB = {val:.2f}")
