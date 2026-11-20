from argparse import ArgumentParser
import os
from pathlib import Path
from zipfile import ZipFile

from scripts.utils import find_project_root
import yaml


def preprocess(raw_dir, processed_dir):
    """Preprocess raw data from raw directory and put in processed directory

    Args:
        raw_dir (Path): Directory of downloaded data (zip files)
        processed_dir (Path): Directory for processed data
    """
    print('Preprocessing data')
    for zip in raw_dir.glob('*.zip'):
        output_dir = processed_dir / zip.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip, "r") as archive:
            archive.extractall(output_dir)
        print(f"Extracted {os.path.basename(zip)}")


if __name__ == '__main__':
    parser = ArgumentParser(prog="02_preprocess", 
                            description="Preprocess DICOM by SeriesUID")
    parser.add_argument('--params', dest='params', required=True)
    args = parser.parse_args()

    if os.path.exists(args.params):
        with open(args.params) as param_file:
            params = yaml.safe_load(param_file)
    else:
        raise Exception(f"No pipeline parameters found: {args.params}")

    PROJECT_ROOT = find_project_root()
    processed_dir = Path(PROJECT_ROOT) / params['preprocess']['destination_directory']
    raw_dir = Path(PROJECT_ROOT) / params['preprocess']['source_directory']

    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir, exist_ok=True)

    # Run
    preprocess(raw_dir, processed_dir)

    print("Preprocess complete")