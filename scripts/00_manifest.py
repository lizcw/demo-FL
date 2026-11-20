from argparse import ArgumentParser
import json
import os
import shutil

from scripts.utils import find_project_root
import yaml
import sys 
from collections import defaultdict 
from pathlib import Path 
  
import pandas as pd 
import pydicom


def convert_json_to_csv(json_path, manifest_file=None):
    """
    Convert JSON from ORTHANC fetch via Zendaya
    """
    
    if not os.path.exists(json_path):
        print('JSON file not found')
    else:
        with open(json_path, 'r') as fh:
            json_data = json.load(fh)
            if json_data['status'] != 'SUCCESS':
                print('JSON data not present')
            elif len(json_data['items']) <=0:
                print('No JSON data items found')
            else:
                print('converting JSON to CSV')
                csv_file = json_path.replace('.json', '.csv')
                with open(csv_file, 'w') as cf:
                    cf.write("connection_type,body_part,description,modality,upload_date,series_uid,study_uid,study_id,uri,link_url,expt_id\n")
                    for scan in json_data['items']['scans']:
                        print(scan["series_uid"])
                        cf.write(f"{scan['connection_type']},{scan['body_part']},{scan['description']},{scan['modality']},{scan['upload_date']},{scan['series_uid']},{scan['study_uid']},{scan['study_id']},{scan['uri']},{scan['link_url']},{scan['expt_id']}\n")

                    cf.close()
                print(f"Conversion completed: {csv_file}")
                # Copy to manifest_file
                if manifest_file:
                    shutil.copy(csv_file, manifest_file)
                    print(f"Copied to {manifest_file}")
            fh.close()

def generate_manifest_from_folder(raw_dicom_directory, manifest_file):
    """
    Generate a manifest of DICOM files from a DICOM directory
    """
    series = defaultdict(lambda: {'n_images': 0, 'modality': None, 'study': None}) 
    bad = [] 
  
    for f in sorted(raw_dicom_directory.rglob('*.dcm')): 
        try: 
            ds = pydicom.dcmread(f, stop_before_pixels=True) 
            s = series[ds.SeriesInstanceUID] 
            s['n_images'] += 1 
            s['modality'] = getattr(ds, 'Modality', None) 
            s['study'] = ds.StudyInstanceUID 
        except Exception as e: 
            bad.append((str(f), str(e))) 
  
    df = pd.DataFrame.from_dict(series, orient='index') 
    df.index.name = 'series_uid' 
    df.to_csv(manifest_file) 
  
    print(f'{len(df)} series, {int(df.n_images.sum())} images, {len(bad)} unreadable files') 

    

if __name__ == '__main__':
    parser = ArgumentParser(prog=Path(__file__).name, 
                            description="Generate manifest for DICOM series")
    parser.add_argument('--params', dest='params', required=True)
    args = parser.parse_args()

    if os.path.exists(args.params):
        with open(args.params) as param_file:
            params = yaml.safe_load(param_file)
    else:
        raise Exception(f"No pipeline parameters found: {args.params}")

    PROJECT_ROOT = find_project_root()
    MANIFEST_CSV = params['retrieve']['manifest_csv']
    manifest_file = os.path.join(PROJECT_ROOT, MANIFEST_CSV)
    json_file = params['manifest']['json_file']
    

    # Options 1. Convert from JSON or 2. Generate from folder
    OPTION = params['manifest']['option']
    try:
        if OPTION == 'json':
            print('Generating from JSON')
            json_file = params['manifest']['json_file']
            convert_json_to_csv(json_file, manifest_file)
        elif OPTION == 'dicom-dir':
            print('Generating from Directory of DICOMs')
            dicom_dir = Path(params['manifest']['dicom_dir'])
            generate_manifest_from_folder(dicom_dir, manifest_file)
        else:
            print('No option provided (json or dir) - see params.yaml')
        
    except Exception as e:
        print(e)