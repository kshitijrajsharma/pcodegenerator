import argparse
import json
import os
import subprocess
import zipfile

import requests

from .__version__ import __version__


def fetch_fieldmaps_data():
    url = "https://data.fieldmaps.io/edge-matched.json"
    response = requests.get(url)
    return response.json()


def download_and_extract(url, extract_path):
    response = requests.get(url)
    zip_path = os.path.join(extract_path, "temp.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
    os.remove(zip_path)
    return [f for f in os.listdir(extract_path) if f.endswith(".gpkg")][0]


def convert_to_geoparquet(input_gpkg, output_parquet):
    cmd = [
        "ogr2ogr",
        "-f",
        "Parquet",
        output_parquet,
        input_gpkg,
        "-lco",
        "GEOMETRY_NAME=geometry",
    ]
    subprocess.run(cmd, check=True)


def create_meta_json(output_path, date, url):
    meta = {"date": date, "url": url}
    with open(os.path.join(output_path, "meta.json"), "w") as f:
        json.dump(meta, f)


def main(admin_level, output_path):
    os.makedirs(output_path, exist_ok=True)
    fieldmaps_data = fetch_fieldmaps_data()
    relevant_data = next(
        (item for item in fieldmaps_data if item["adm"] == admin_level and item["grp"] == "humanitarian"),
        None,
    )
    if not relevant_data:
        print(f"No data found for admin level {admin_level}")
        return

    date = relevant_data["date"]
    url = relevant_data["a_gpkg"]
    output_geoparquet_file = os.path.join(output_path, f"adm{admin_level}_polygons.parquet")
    meta_file = os.path.join(output_path, "meta.json")

    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            existing_meta = json.load(f)
        if existing_meta["date"] == date and os.path.exists(output_geoparquet_file):
            print("Data is up to date. No action needed.")
            return

    print("Downloading and extracting data...", url)
    temp_dir = os.path.join(output_path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    gpkg_file = download_and_extract(url, temp_dir)

    print("Converting to GeoParquet...")
    convert_to_geoparquet(os.path.join(temp_dir, gpkg_file), output_geoparquet_file)

    print("Creating meta.json...")
    create_meta_json(output_path, date, url)

    print("Cleaning up...")
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

    print(f"Process completed. Output saved to {output_geoparquet_file}")


def run_as_script():
    parser = argparse.ArgumentParser(description="Prepare Fieldmaps admin boundary cod data for pcodegenerator")
    parser.add_argument("--admin", type=int, help="Admin level (1-4)")
    parser.add_argument("--output", default=os.getcwd(), help="Path for output GeoParquet file")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()
    main(args.admin, args.output)


if __name__ == "__main__":
    run_as_script()
