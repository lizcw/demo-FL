from argparse import ArgumentParser
import os
import pandas as pd

import requests
from scripts.utils import find_project_root
import yaml


def fetch_dicom(series_manifest, data_directory, username=None, password=None):
    """Fetch DICOM from DICOM server using the series manifest file

    Args:
        series_manifest (_type_): file containing UIDs for DICOM series
        data_directory (_type_): location to download to
        username (_type_, optional): DICOM server username. Defaults to None.
        password (_type_, optional): DICOM server password. Defaults to None.
    """    
    print('Fetching DICOM')
    df = pd.read_csv(series_manifest)
    for index, row in df.iterrows():
        uri = row["uri"]
        print(uri)
        download_url = f"{uri}/archive"
        download_url = download_url.replace("http://", f"http://{username}:{password}@")
  
        series = row["expt_id"]
        download_file = os.path.join(data_directory, f"{series}.zip")
        try:
            # Download file
            with requests.get(download_url, 
                            stream=True,
                            timeout=(10, 300),
            ) as response:
                response.raise_for_status()

                with open(download_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            print(str(e))
            exit(1)





if __name__ == '__main__':
    parser = ArgumentParser(prog="01_retrieve", 
                            description="Retrieve DICOM by SeriesUID")
    parser.add_argument('--params', dest='params', required=True)
    args = parser.parse_args()

    if os.path.exists(args.params):
        with open(args.params) as param_file:
            params = yaml.safe_load(param_file)
    else:
        raise Exception(f"No pipeline parameters found: {args.params}")

    PROJECT_ROOT = find_project_root()
    SERIES_CSV = params['retrieve']['series_csv']
    SOURCE_DIRECTORY: str = params['preprocess']['source_directory']
    USERNAME = params['retrieve']['username']
    PASSWORD = None
    PASSWORD_FILE = params['retrieve']['password_file']
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, 'r') as pf:
            PASSWORD = pf.readline()
            pf.close()


    try:
        series_manifest = os.path.join(PROJECT_ROOT, SERIES_CSV)
        data_directory = os.path.join(PROJECT_ROOT, SOURCE_DIRECTORY)
        print(f"{series_manifest} {data_directory}")

        if not os.path.exists(series_manifest):
            raise Exception("Manifest file not found")
        if not os.path.exists(data_directory):
            print(f'Creating data directory: {data_directory}')
            os.makedirs(data_directory, exist_ok=True)
        rtn = fetch_dicom(series_manifest, data_directory, USERNAME, PASSWORD)
        if rtn:
            print("Success")
        else:
            print("Error occurred")
    except Exception as e:
        print(str(e))