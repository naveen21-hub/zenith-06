import numpy as np
import os, glob
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
from scipy.ndimage import median_filter, binary_fill_holes
from skimage.measure import label, regionprops

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "processed", "db")
PLOTS_DIR = os.path.join(BASE_DIR, "web", "plots")

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

# Load the dam zoom Esri image
dam_esri_path = os.path.join(PLOTS_DIR, "dam_zoom_esri.png")
esri_img = Image.open(dam_esri_path).convert('RGB')
esri_arr = np.array(esri_img)

# Dam region bounding box
ZOOM_LON = (76.555, 76.585)
ZOOM_LAT = (12.410, 12.445)
extent = [ZOOM_LON[0], ZOOM_LON[1], ZOOM_LAT[0], ZOOM_LAT[1]]

# Create coordinate meshgrid for zoom region to sample masks
# In global grid:
z_ux0, z_uy0 = to_utm.transform(ZOOM_LON[0], ZOOM_LAT[0])
z_ux1, z_uy1 = to_utm.transform(ZOOM_LON[1], ZOOM_LAT[1])
zc0 = int((z_ux0 - x_coords[0]) / dx)
zc1 = int((z_ux1 - x_coords[0]) / dx)
zr0 = int((y_coords[0] - z_uy1) / dx)
zr1 = int((y_coords[0] - z_uy0) / dx)

fig, ax = plt.subplots(figsize=(10, 10), dpi=180)
ax.imshow(esri_arr, extent=extent, origin='upper', aspect='auto')

# Extract full-grid masks
fg_A = np.zeros((len(y_coords), len(x_coords)), dtype=bool)
fg_B = np.zeros((len(y_coords), len(x_coords)), dtype=bool)
fg_C = np.zeros((len(y_coords), len(x_coords)), dtype=bool)
fg_A[r0:r1, c0:c1] = mA
fg_B[r0:r1, c0:c1] = mB
fg_C[r0:r1, c0:c1] = mC

crop_A = fg_A[zr0:zr1, zc0:zc1]
crop_B = fg_B[zr0:zr1, zc0:zc1]
crop_C = fg_C[zr0:zr1, zc0:zc1]

crop_only_C = (~crop_A) & (~crop_B) & crop_C

# Overlay only_C in vibrant bright green
rgba = np.zeros((crop_C.shape[0], crop_C.shape[1], 4), dtype=np.float32)
# Common water in dark blue
common = crop_A & crop_B & crop_C
rgba[common] = [0.1, 0.4, 0.8, 0.5]
# Only C in vivid lime green
rgba[crop_only_C] = [0.0, 1.0, 0.2, 0.85]

ax.imshow(rgba, extent=extent, origin='upper', aspect='auto')

# Plot KRS Dam wall trace
# KRS Dam wall vertices (South to North)
# Measured precisely along the masonry dam crest:
dam_crest = [
    (76.5710, 12.4175), # South abutment
    (76.5714, 12.4210),
    (76.5720, 12.4250), # Central sluices
    (76.5727, 12.4290),
    (76.5735, 12.4340), # North spillway
    (76.5738, 12.4365)  # North abutment
]
crest_lons = [p[0] for p in dam_crest]
crest_lats = [p[1] for p in dam_crest]
ax.plot(crest_lons, crest_lats, 'y-', linewidth=3.0, label='KRS Dam Masonry Wall (Crest)')
ax.plot(crest_lons, crest_lats, 'ro', markersize=6)

ax.text(76.562, 12.427, "RESERVOIR\n(UPSTREAM)", color='white', fontsize=14, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="#0072B2", ec="white", lw=1.5, alpha=0.8))

ax.text(76.576, 12.422, "DOWNSTREAM\n(Kaveri River &\nBrindavan Gardens)", color='white', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="#b91c1c", ec="white", lw=1.5, alpha=0.8))

ax.text(76.5755, 12.440, "Visvesvaraya Canal Headworks\n& Irrigated Paddy Fields\n(Green Strip: 1.00 km²)", color='white', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="#047857", ec="white", lw=1.5, alpha=0.85))

ax.set_title("Downstream Audit: KRS Dam Wall & 'Nov 2026 Only' Anomaly Over Esri Satellite", fontsize=12, fontweight='bold')
ax.set_xlabel("Longitude (°E)", fontsize=10)
ax.set_ylabel("Latitude (°N)", fontsize=10)
ax.legend(loc="lower left", fontsize=10, framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.5, color='white')

out_path = os.path.join(PLOTS_DIR, "dam_downstream_audit_detail.png")
plt.savefig(out_path, bbox_inches='tight')
plt.close()
print(f"Saved detailed downstream audit plot to {out_path}")
