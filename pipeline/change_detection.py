import os
import glob
import numpy as np
import json

def calculate_temporal_stats_v2(processed_dir='processed'):
    water_files = sorted(glob.glob(os.path.join(processed_dir, '*_water.npy')))
    if len(water_files) < 3:
        print(f'Error: Expected 3 processed water files, found {len(water_files)}.')
        return

    # Load water masks
    mask_1 = np.load(water_files[0])       # 2025-11-23
    mask_2 = np.load(water_files[1])       # 2026-08-14
    mask_3 = np.load(water_files[2])       # 2026-11-06

    # 10 meters per pixel, pixel area = 0.0001 square kilometers
    pixel_area_km2 = 0.0001

    area_1 = int(np.sum(mask_1)) * pixel_area_km2
    area_2 = int(np.sum(mask_2)) * pixel_area_km2
    area_3 = int(np.sum(mask_3)) * pixel_area_km2

    # Quantify dynamics
    permanent_water = np.logical_and(np.logical_and(mask_1 == 1, mask_2 == 1), mask_3 == 1)
    permanent_area = int(np.sum(permanent_water)) * pixel_area_km2

    seasonal_expansion = np.logical_and(mask_1 == 0, mask_3 == 1)
    expansion_area = int(np.sum(seasonal_expansion)) * pixel_area_km2

    stats = {
        'epochs': [
            {'date': '2025-11-23', 'track': '12', 'status': 'Winter Dry Season', 'area_km2': round(area_1, 2)},
            {'date': '2026-08-14', 'track': '12', 'status': 'Monsoon Peak', 'area_km2': round(area_2, 2)},
            {'date': '2026-11-06', 'track': '12', 'status': 'Post-Monsoon Expansion', 'area_km2': round(area_3, 2)}
        ],
        'change_analysis': {
            'permanent_water_km2': round(permanent_area, 2),
            'seasonal_expansion_km2': round(expansion_area, 2)
        }
    }

    with open(os.path.join(processed_dir, 'stats.json'), 'w') as f:
        json.dump(stats, f, indent=4)

    print('Saved recomputed high-quality stats to processed/stats.json')
    print(json.dumps(stats, indent=2))

if __name__ == '__main__':
    calculate_temporal_stats_v2()