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

# Load Nov 06 2026 mask
d = np.load(npz_files[2])
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

# Let's inspect all pixels in `final` where lon > 76.568
for r in range(final.shape[0]):
    for c in range(1280, final.shape[1]):
        if final[r, c]:
            ux = x_coords[c0 + c]
            uy = y_coords[r0 + r]
            lon, lat = to_ll.transform(ux, uy)
            if lon >= 76.570:
                pass

r_idx, c_idx = np.where(final[:, 1280:])
c_idx = c_idx + 1280

print(f"Total water pixels in Nov 2026 with c >= 1280: {len(r_idx)}")
# Check distribution of (lat, lon)
pts = []
for r, c in zip(r_idx, c_idx):
    ux = x_coords[c0 + c]
    uy = y_coords[r0 + r]
    lon, lat = to_ll.transform(ux, uy)
    pts.append((lat, lon, r, c))

pts_east_of_76570 = [p for p in pts if p[1] >= 76.570]
print(f"Pixels with lon >= 76.570: {len(pts_east_of_76570)} ({len(pts_east_of_76570)*1e-4:.4f} km²)")

# Print min/max lat for these
lats_east = [p[0] for p in pts_east_of_76570]
lons_east = [p[1] for p in pts_east_of_76570]
print(f"Lat range for lon >= 76.570: {min(lats_east):.4f} to {max(lats_east):.4f}")
print(f"Lon range for lon >= 76.570: {min(lons_east):.4f} to {max(lons_east):.4f}")

# Group into clusters
from sklearn.cluster import DBSCAN
coords = np.array([[p[0], p[1]] for p in pts_east_of_76570])
dbscan = DBSCAN(eps=0.003, min_samples=20).fit(coords)
labels = dbscan.labels_
for cl in set(labels):
    sub = coords[labels == cl]
    print(f"Cluster {cl}: count={len(sub)} ({len(sub)*1e-4:.4f} km²), mean lat={sub[:,0].mean():.4f}, mean lon={sub[:,1].mean():.4f}")
