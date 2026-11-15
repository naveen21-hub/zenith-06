import os
import glob
import h5py
import numpy as np
import matplotlib.pyplot as plt
from skimage.filters import threshold_otsu, median
from skimage.morphology import disk, remove_small_objects, remove_small_holes
from skimage.measure import label, regionprops

def process_nisar_water_v2(h5_path, output_dir='processed', plot_dir='web/plots'):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)
    base_name = os.path.basename(h5_path).replace('.h5', '')

    # Parsing date & track from name
    parts = base_name.split('_')
    track_num = "Track 12"
    acq_date = "Unknown"
    for p in parts:
        if p.startswith('2025') or p.startswith('2026'):
            if 'T' in p:
                acq_date = p.split('T')[0]
                acq_date = f"{acq_date[:4]}-{acq_date[4:6]}-{acq_date[6:]}"

    print(f'Processing file: {h5_path} (Date: {acq_date}, {track_num})')

    with h5py.File(h5_path, 'r') as f:
        ds_path = None
        # Force HH Polarization search for better contrast, avoiding metadata folders
        def find_dataset_hh(name, obj):
            nonlocal ds_path
            if isinstance(obj, h5py.Dataset):
                if 'metadata' in name or 'calibrationInformation' in name:
                    return
                if 'HHHH' in name or 'grids/frequencyA/HH' in name:
                    ds_path = name
        f.visititems(find_dataset_hh)

        if not ds_path:
            print('Warning: HH grid polarization not found. Searching for fallback polarization...')
            def find_dataset_any(name, obj):
                nonlocal ds_path
                if isinstance(obj, h5py.Dataset):
                    if 'metadata' in name or 'calibrationInformation' in name:
                        return
                    if 'HH' in name or 'HV' in name or 'backscatter' in name:
                        ds_path = name
            f.visititems(find_dataset_any)

        if not ds_path:
            print(f'Error: No suitable polarization dataset found inside {h5_path}!')
            return

        print(f'Using polarization dataset path: {ds_path}')
        dataset = f[ds_path]
        ny, nx = dataset.shape[-2:]
        cy, cx = ny // 2, nx // 2
        crop_size = 500

        sub_data = dataset[..., cy-crop_size:cy+crop_size, cx-crop_size:cx+crop_size]
        if len(sub_data.shape) > 2:
            sub_data = sub_data[0]

        sub_data = np.nan_to_num(sub_data.astype(np.float32), nan=0.0001)
        sub_data[sub_data <= 0] = 0.0001

        # Calibrate to dB scale
        db_data = 10.0 * np.log10(sub_data)
        db_data = np.clip(db_data, -25.0, 0.0)

        # Stronger speckle filter (5x5 median filter)
        filtered_db = median(db_data, disk(2))

        # Otsu threshold calculation with robust fallback
        calculated_thresh = threshold_otsu(filtered_db)
        print(f'Calculated Otsu threshold: {calculated_thresh:.2f} dB')

        # If threshold is too high (above -15.0 dB), apply robust fixed threshold
        if calculated_thresh > -15.0:
            final_thresh = -18.0
            print(f'Calculated threshold is too high (> -15.0 dB). Falling back to fixed threshold: {final_thresh} dB')
        else:
            final_thresh = calculated_thresh

        # Binary segment
        water_mask = (filtered_db < final_thresh).astype(bool)

        # Post-Processing:
        # 1. Remove connected components smaller than 200 pixels
        water_mask = remove_small_objects(water_mask, min_size=200)
        # 2. Fill small holes
        water_mask = remove_small_holes(water_mask, area_threshold=200)

        # 3. Isolate main reservoir body (largest connected component)
        labeled_mask = label(water_mask)
        regions = regionprops(labeled_mask)
        if len(regions) > 0:
            largest_region = max(regions, key=lambda r: r.area)
            clean_mask = (labeled_mask == largest_region.label).astype(np.uint8)
        else:
            clean_mask = water_mask.astype(np.uint8)

        # Save numpy data arrays
        np.save(os.path.join(output_dir, f'{base_name}_db.npy'), db_data)
        np.save(os.path.join(output_dir, f'{base_name}_water.npy'), clean_mask)

        # Save Side-by-Side verification PNG plots
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].imshow(db_data, cmap='gray', vmin=-25, vmax=0)
        axes[0].set_title(f'Raw dB ({acq_date})')
        axes[0].axis('off')

        axes[1].imshow(clean_mask, cmap='Blues')
        axes[1].set_title(f'Clean Reservoir Mask (Thresh: {final_thresh:.1f} dB)')
        axes[1].axis('off')

        plt.tight_layout()
        plot_path = os.path.join(plot_dir, f'{base_name}_verification.png')
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f'Verification plot successfully saved to {plot_path}')

def run_pipeline_v2():
    files = glob.glob('data/*.h5')
    for f in files:
        try:
            process_nisar_water_v2(f)
        except Exception as e:
            print(f'Failed to process {f}: {e}')

if __name__ == '__main__':
    run_pipeline_v2()