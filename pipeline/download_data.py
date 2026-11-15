import os
import asf_search as asf

scenes = ['NISAR_L2_PR_GCOV_006_012_A_008_4005_DHDH_A_20251123T002448_20251123T002522_X05009_N_F_J_001', 'NISAR_L2_PR_GCOV_028_012_A_008_4005_DHDH_A_20260814T002446_20260814T002521_P05023_N_F_J_001', 'NISAR_L2_PR_GCOV_035_012_A_008_4005_DHDH_A_20261106T002447_20261106T002521_P05036_N_F_J_001']

def run_downloads():
    username = os.getenv('EARTHDATA_USERNAME')
    password = os.getenv('EARTHDATA_PASSWORD')
    if not username or not password:
        print("Error: EARTHDATA_USERNAME and EARTHDATA_PASSWORD environment variables are required!")
        return

    print("Logging into ASF...")
    session = asf.ASFSession().auth_with_creds(username, password)

    os.makedirs('data', exist_ok=True)
    for scene in scenes:
        print(f"Searching for product: {scene}")
        results = asf.product_search(scene)
        if results:
            print(f"Downloading {scene}...")
            results[0].download(path='data', session=session)
        else:
            print(f"Product {scene} not found on ASF.")

if __name__ == '__main__':
    run_downloads()