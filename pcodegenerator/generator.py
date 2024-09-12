import argparse
import os

import duckdb
import geopandas as gpd
from shapely import wkb

from .__version__ import __version__


def load_admin4cod(source):
    conn = duckdb.connect("pcodegenerator.db")
    conn.install_extension("spatial")
    conn.install_extension("httpfs")
    conn.load_extension("spatial")
    conn.load_extension("httpfs")
    print("Extension installed on duckdb")

    if source.startswith("http"):
        from_query = f"read_parquet('{source}')"
    else:
        from_query = f"read_parquet('{os.path.abspath(source)}')"

    query = f"CREATE TABLE IF NOT EXISTS admincod AS (select * from {from_query})"
    print(query)
    conn.execute(query)
    print("Admincod table created in duckdb")
    return conn


def process_input(conn, input_data, intersection_method="centroid"):
    if isinstance(input_data, gpd.GeoDataFrame):
        gdf = input_data
    elif isinstance(input_data, str):
        if input_data.endswith(".geojson"):
            gdf = gpd.read_file(input_data)
        elif input_data.endswith(".parquet"):
            gdf = gpd.read_parquet(input_data)
        else:
            try:
                gdf = gpd.read_file(input_data)
            except:
                raise ValueError("Invalid input format. Must be GeoJSON or GeoParquet.")
    else:
        raise ValueError("Input must be a GeoDataFrame or a file path string.")

    print(gdf)

    if intersection_method == "centroid":
        gdf["geometry"] = gdf["geometry"].centroid

    gdf = gdf.to_wkb()
    create_table_query = (
        f"CREATE TABLE IF NOT EXISTS input_data AS (select * EXCLUDE geometry, ST_GeomFromWKB(geometry) AS geometry from gdf)"
    )
    print(create_table_query)
    conn.execute(create_table_query)

    query = """
    SELECT
    i.* EXCLUDE geometry,
    a.adm0_name as adm0_name,
    a.adm1_name as adm1_name,
    a.adm2_name as adm2_name,
    a.adm3_name as adm3_name,
    a.adm3_name as adm4_name,
    COALESCE(a.adm4_src, a.adm3_src, a.adm2_src, a.adm1_src, a.adm0_src) AS pcode,
    a.src_url as pcode_src,
    ST_AsHEXWKB(i.geometry) as geometry
    FROM input_data i , admincod a
    where ST_Within(i.geometry, a.geometry)
    """
    print(query)
    result_df = conn.execute(query).fetchdf()
    result_df["geometry"] = result_df["geometry"].apply(wkb.loads)
    result_gpd = gpd.GeoDataFrame(result_df, geometry="geometry", crs=4326)
    return result_gpd


def main(source_cod, input_data, intersection_method="centroid"):
    conn = load_admin4cod(source_cod)
    result = process_input(conn, input_data, intersection_method)
    print(result)
    return result


def run_as_script():
    parser = argparse.ArgumentParser(description="Process spatial data with DuckDB to generate pcodes")
    parser.add_argument("--source", help="Path or URL to the admin4cod GeoParquet file")
    parser.add_argument("--input", help="Path to input GeoJSON or GeoParquet file")
    parser.add_argument("--output", help="Path for output GeoJSON or GeoParquet file")
    parser.add_argument("--method", default="centroid", choices=["centroid"], help="Intersection method")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    result = main(args.source, args.input, args.method)
    if args.output.endswith(".geojson"):
        result.to_file(args.output, driver="GeoJSON")
    elif args.output.endswith(".parquet"):
        result.to_parquet(args.output)
    else:
        raise ValueError("Invalid output format. Must be GeoJSON or GeoParquet.")


if __name__ == "__main__":
    run_as_script()
