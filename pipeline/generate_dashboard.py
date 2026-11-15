
import os
import glob
import numpy as np
import folium
import json

def create_dashboard_v2(processed_dir='processed', output_dir='web'):
    os.makedirs(output_dir, exist_ok=True)
    
    # Load recomputed stats
    with open(os.path.join(processed_dir, 'stats.json'), 'r') as f:
        stats = json.load(f)

    # Initialize Folium Map with safe OpenStreetMap as default basemap
    m = folium.Map(
        location=[12.45, 76.57], 
        zoom_start=12, 
        control_scale=True, 
        tiles='OpenStreetMap'
    )

    # Add Esri World Imagery Satellite layer as toggleable layer option
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    water_files = sorted(glob.glob(os.path.join(processed_dir, '*_water.npy')))
    dates_labels = [
        '2025-11-23 (Track 12 - Dry Season)', 
        '2026-08-14 (Track 12 - Monsoon Peak)', 
        '2026-11-06 (Track 12 - Post-Monsoon Expansion)'
    ]
    colors = ['#d95f02', '#7570b3', '#1b9e77']

    for filepath, date_label, color in zip(water_files, dates_labels, colors):
        mask = np.load(filepath)
        ny, nx = mask.shape
        
        lat_min, lat_max = 12.35, 12.55
        lon_min, lon_max = 76.45, 76.70
        
        overlay = np.zeros((ny, nx, 4), dtype=np.uint8)
        rgb = [int(color[i:i+2], 16) for i in (1, 3, 5)]
        overlay[mask == 1] = [rgb[0], rgb[1], rgb[2], 210]  # Higher opacity for clear delineation
        
        folium.raster_layers.ImageOverlay(
            image=overlay,
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            name=f'Water Extent: {date_label}',
            opacity=0.75,
            interactive=True,
            cross_origin=False,
            zindex=10
        ).add_to(m)

    # Floating HTML Stats Dashboard Panel with accurate details
    stats_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 340px; height: 320px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid #555; border-radius: 8px; padding: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.35); font-family: sans-serif;">
        <h4 style="margin-top:0; color:#1b3d6c; font-size:15px; border-bottom: 2px solid #1b3d6c; padding-bottom:5px;">
            NISAR KRS Reservoir Dashboard (HH)
        </h4>
        <p style="margin:5px 0;"><b>Temporal Water Area (Track 12):</b></p>
        <table style="width:100%; text-align:left; border-collapse:collapse; font-size:11px;">
          <tr style="background-color:#eaeaea;"><th style="padding:4px;">Date</th><th style="padding:4px;">Season</th><th style="padding:4px;">Area (km²)</th></tr>
          <tr><td style="padding:4px;">2025-11-23</td><td style="padding:4px;">Winter Dry</td><td style="padding:4px; font-weight:bold; color:#d95f02;">{stats["epochs"][0]["area_km2"]} km²</td></tr>
          <tr><td style="padding:4px;">2026-08-14</td><td style="padding:4px;">Monsoon Peak</td><td style="padding:4px; font-weight:bold; color:#7570b3;">{stats["epochs"][1]["area_km2"]} km²</td></tr>
          <tr><td style="padding:4px;">2026-11-06</td><td style="padding:4px;">Post-Monsoon</td><td style="padding:4px; font-weight:bold; color:#1b9e77;">{stats["epochs"][2]["area_km2"]} km²</td></tr>
        </table>
        <hr style="margin:8px 0; border:0; border-top:1px solid #ccc;">
        <p style="font-size:11px; margin-bottom:4px;"><b>Temporal Overlay Analysis:</b></p>
        <p style="font-size:11px; margin:2px 0;">💧 Permanent Core Water: <b>{stats["change_analysis"]["permanent_water_km2"]} km²</b></p>
        <p style="font-size:11px; margin:2px 0;">🌱 Seasonal Expansion: <b>{stats["change_analysis"]["seasonal_expansion_km2"]} km²</b></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))

    # Add standard Layer Controls
    folium.LayerControl().add_to(m)

    dashboard_path = os.path.join(output_dir, 'index.html')
    m.save(dashboard_path)
    print(f'Dashboard successfully compiled and saved to {dashboard_path}')

if __name__ == '__main__':
    create_dashboard_v2()