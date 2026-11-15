import urllib.request
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOTS_DIR = os.path.join(BASE_DIR, "web", "plots")
DB_DIR = os.path.join(BASE_DIR, "processed", "db")

to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
to_ll = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

# Dam region bounding box
# Lat: 12.410 to 12.445, Lon: 76.555 to 76.585
ZOOM_LON = (76.555, 76.585)
ZOOM_LAT = (12.410, 12.445)

# Fetch Esri satellite image of dam region
esri_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox={ZOOM_LON[0]},{ZOOM_LAT[0]},{ZOOM_LON[1]},{ZOOM_LAT[1]}&bboxSR=4326&imageSR=4326&size=1200,1400&format=png&f=image"
req = urllib.request.Request(esri_url, headers={'User-Agent': 'Mozilla/5.0'})
dam_esri_path = os.path.join(PLOTS_DIR, "dam_zoom_esri.png")
with urllib.request.urlopen(req, timeout=15) as resp:
    with open(dam_esri_path, 'wb') as f:
        f.write(resp.read())
print(f"Downloaded dam zoom Esri image to {dam_esri_path}")

# Load masks
npz_files = sorted([os.path.join(DB_DIR, f) for f in os.listdir(DB_DIR) if f.endswith('.npz')])
ref = np.load(npz_files[0])
x_coords, y_coords = ref['x'], ref['y']
dx = 10.0

from scipy.ndimage import median_filter, binary_fill_holes
from skimage.measure import label, regionprops

BOX_LON = (76.445, 76.585)
BOX_LAT = (12.380, 12.530)
ux0, uy0 = to_utm.transform(BOX_LON[0], BOX_LAT[0])
ux1, uy1 = to_utm.transform(BOX_LON[1], BOX_LAT[1])
c0 = max(0, int((ux0 - x_coords[0]) / dx))
c1 = min(len(x_coords), int((ux1 - x_coords[0]) / dx))
r0 = max(0, int((y_coords[0] - uy1) / dx))
r1 = min(len(y_coords), int((y_coords[0] - uy0) / dx))

DATES = ["2025-11-23", "2026-08-14", "2026-11-06"]
COLORS = ["#0072B2", "#E69F00", "#009E73"]

# Zoom pixel bounds in global grid
z_ux0, z_uy0 = to_utm.transform(ZOOM_LON[0], ZOOM_LAT[0])
z_ux1, z_uy1 = to_utm.transform(ZOOM_LON[1], ZOOM_LAT[1])
zc0 = int((z_ux0 - x_coords[0]) / dx)
zc1 = int((z_ux1 - x_coords[0]) / dx)
zr0 = int((y_coords[0] - z_uy1) / dx)
zr1 = int((y_coords[0] - z_uy0) / dx)

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
    
    # Store full grid
    fg = np.zeros((len(y_coords), len(x_coords)), dtype=bool)
    fg[r0:r1, c0:c1] = final
    masks.append(fg[zr0:zr1, zc0:zc1])

# Plot 3-panel figure showing each date over Esri imagery
esri_img = Image.open(dam_esri_path).convert('RGB')
esri_arr = np.array(esri_img)

fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=150)
plt.subplots_adjust(wspace=0.08, left=0.03, right=0.97, top=0.90, bottom=0.05)

extent = [ZOOM_LON[0], ZOOM_LON[1], ZOOM_LAT[0], ZOOM_LAT[1]]

for i, date in enumerate(DATES):
    ax = axes[i]
    ax.imshow(esri_arr, extent=extent, origin='upper', aspect='auto')
    
    # Overlay mask
    m = masks[i]
    # Mask overlay with alpha
    rgba = np.zeros((m.shape[0], m.shape[1], 4), dtype=np.float32)
    c_rgb = matplotlib.colors.to_rgb(COLORS[i])
    rgba[m, :3] = c_rgb
    rgba[m, 3] = 0.55
    
    # Show mask overlay
    # Note: masks array origin is upper (row 0 = north)
    ax.imshow(rgba, extent=extent, origin='upper', aspect='auto')
    
    # Plot Dam marker / line
    dam_lon, dam_lat = 76.572, 12.425
    ax.plot(dam_lon, dam_lat, 'r^', markersize=9, label='Dam Center' if i==0 else "")
    
    # Draw longitude line at 76.572 (approximate dam longitude)
    ax.axvline(x=76.572, color='yellow', linestyle='--', linewidth=1.5, alpha=0.8, label='Dam Longitude (76.572°E)' if i==0 else "")
    
    ax.set_title(f"{date} (Mask: {COLORS[i]})", fontsize=13, fontweight='bold', color='navy')
    ax.set_xlabel("Longitude (°E)", fontsize=10)
    if i == 0:
        ax.set_ylabel("Latitude (°N)", fontsize=10)
        ax.legend(loc='lower left', fontsize=9, framealpha=0.9)
    ax.grid(True, linestyle=':', alpha=0.4, color='white')

fig.suptitle("Zoomed Crop Around KRS Dam (Lat 12.425, Lon 76.572) Over Esri Satellite", fontsize=15, fontweight='bold')
out_fig_path = os.path.join(PLOTS_DIR, "dam_audit_zoom_three_dates.png")
plt.savefig(out_fig_path, bbox_inches='tight')
plt.close()
print(f"Saved dam audit comparison plot to {out_fig_path}")
