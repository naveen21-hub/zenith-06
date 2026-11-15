import numpy as np
import os, glob
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

# Load coords
npz_files = sorted(glob.glob(os.path.join(DB_DIR, "*.npz")))
ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
dx = abs(float(x_coords[1] - x_coords[0]))

print(f"X range: {x_coords[0]} to {x_coords[-1]}, len={len(x_coords)}")
print(f"Y range: {y_coords[0]} to {y_coords[-1]}, len={len(y_coords)}")

# Dam coords
dam_lon, dam_lat = 76.572, 12.425
ux_dam, uy_dam = to_utm.transform(dam_lon, dam_lat)
c_dam = int((ux_dam - x_coords[0]) / dx)
r_dam = int((y_coords[0] - uy_dam) / dx)

print(f"KRS Dam: Lon={dam_lon}, Lat={dam_lat} -> UTM=({ux_dam:.1f}, {uy_dam:.1f}) -> col={c_dam}, row={r_dam}")

# Study box
BOX_LON = (76.445, 76.585)
BOX_LAT = (12.380, 12.530)
ux0, uy0 = to_utm.transform(BOX_LON[0], BOX_LAT[0])
ux1, uy1 = to_utm.transform(BOX_LON[1], BOX_LAT[1])
c0 = max(0, int((ux0 - x_coords[0]) / dx))
c1 = min(len(x_coords), int((ux1 - x_coords[0]) / dx))
r0 = max(0, int((y_coords[0] - uy1) / dx))
r1 = min(len(y_coords), int((y_coords[0] - uy0) / dx))

print(f"Study box in UTM: x=[{ux0:.1f}, {ux1:.1f}], y=[{uy0:.1f}, {uy1:.1f}]")
print(f"Study box row: [{r0}, {r1}], col: [{c0}, {c1}]")
