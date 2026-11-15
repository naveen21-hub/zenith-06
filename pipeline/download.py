import os
import asf_search as asf

def download_scene(scene_name, dest_folder='data'):
    user = os.getenv('EARTHDATA_USERNAME')
    password = os.getenv('EARTHDATA_PASSWORD')
    if not user or not password or user == 'YOUR_USERNAME':
        print("Error: Please set valid EARTHDATA_USERNAME and EARTHDATA_PASSWORD environment variables.")
        return
    
    print(f"Logging into ASF and searching for {scene_name}...")
    session = asf.ASFSession().auth_with_creds(user, password)
    results = asf.product_search(scene_name)
    if len(results) > 0:
        product = results[0]
        print(f"Downloading {product.properties['sceneName']} to {dest_folder}/")
        product.download(path=dest_folder, session=session)
    else:
        print("Scene not found.")

if __name__ == '__main__':
    # Test download on a small metadata file or placeholder if configured
    print("Download pipeline script ready.")