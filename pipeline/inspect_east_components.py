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
only_C = (~mA) & (~mB) & mC

# Label connected components of only_C east of dam (c > 1310)
east_mask = np.zeros_like(only_C)
east_mask[:, 1310:] = only_C[:, 1310:]
lbl_east = label(east_mask)
props_east = sorted(regionprops(lbl_east), key=lambda p: p.area, reverse=True)

print(f"Components of 'Nov 2026 only' east of col 1310:")
for idx, p in enumerate(props_east[:10]):
    rmin, cmin, rmax, cmax = p.bbox
    # Convert centroid to lat/lon
    cr_y, cr_x = p.centroid
    ux = x_coords[c0 + int(cr_x)]
    uy = y_coords[r0 + int(cr_y)]
    lon, lat = to_ll.transform(ux, uy)
    area_km2 = p.area * 1e-4
    print(f"  Component {idx+1}: Area = {area_km2:.4f} km² ({p.area} px), Centroid = ({lat:.4f}°N, {lon:.4f}°E), BBox = rows [{rmin}, {rmax}], cols [{cmin}, {cmax}]")
