import io
import zipfile

import geopandas as gpd
import streamlit as st

from pcodegenerator import generator as pcode_generator


def load_geospatial_file(uploaded_file):
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension == "geojson":
        return gpd.read_file(uploaded_file)
    elif file_extension == "gpkg":
        return gpd.read_file(uploaded_file, driver="GPKG")
    elif file_extension == "zip":
        with zipfile.ZipFile(uploaded_file) as z:
            for filename in z.namelist():
                if filename.endswith(".shp"):
                    with z.open(filename) as f:
                        return gpd.read_file(f)
    else:
        st.error("Unsupported file format. Please upload a GeoJSON, GeoPackage, or zipped Shapefile.")
        return None


def load_geospatial_file(uploaded_file):
    file_extension = uploaded_file.name.split(".")[-1].lower()

    try:
        if file_extension in ["geojson", "json"]:
            return gpd.read_file(uploaded_file)
        elif file_extension == "gpkg":
            return gpd.read_file(uploaded_file, driver="GPKG")
        elif file_extension == "shp":
            return gpd.read_file(uploaded_file)
        elif file_extension == "zip":
            with zipfile.ZipFile(uploaded_file) as z:
                for filename in z.namelist():
                    if filename.endswith(".shp"):
                        with z.open(filename) as f:
                            return gpd.read_file(f)
        elif file_extension == "kml":
            return gpd.read_file(uploaded_file, driver="KML")
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None


def main():
    st.set_page_config(page_title="PCode Generator", layout="wide")
    st.title("PCode Generator")
    supported_formats = ["GeoJSON", "GeoPackage", "Shapefile", "KML", "Zipped Shapefile"]
    format_extensions = {
        "GeoJSON": ["geojson", "json"],
        "GeoPackage": ["gpkg"],
        "Shapefile": ["shp"],
        "KML": ["kml"],
        "Zipped Shapefile": ["zip"],
    }
    all_extensions = [ext for exts in format_extensions.values() for ext in exts]

    uploaded_file = st.file_uploader(f"Upload a geospatial file ({', '.join(supported_formats)})", type=all_extensions)

    geojson_text = st.text_area("Or paste GeoJSON here")

    source_url = st.text_input(
        "Enter the source URL for admin4cod GeoParquet file",
        value="https://staging-raw-data-api.s3.amazonaws.com/default/cod/adm4_polygons.parquet",
    )

    output_format = st.selectbox("Select output format", ["GeoJSON", "GeoParquet", "ESRI Shapefile", "GeoPackage", "CSV", "Excel"])

    intersection_method = st.selectbox("Select intersection method", ["centroid"])

    if st.button("Generate PCodes"):
        with st.spinner("Processing..."):
            if uploaded_file:
                gdf = load_geospatial_file(uploaded_file)
            elif geojson_text:
                gdf = gpd.read_file(io.StringIO(geojson_text), driver="GeoJSON")
            else:
                st.error("Please upload a file or paste GeoJSON data.")
                return

            if gdf is not None:
                result_gdf = pcode_generator.main(source_url, gdf, intersection_method)

                st.subheader("Top 50 rows of the result")
                df = result_gdf.drop(columns=["geometry"])
                st.write(df.head(50))

                # Prepare output based on selected format
                if output_format == "GeoJSON":
                    output_data = result_gdf.to_json()
                    file_extension = "geojson"
                    mime_type = "application/json"
                elif output_format == "GeoParquet":
                    output_buffer = io.BytesIO()
                    result_gdf.to_parquet(output_buffer)
                    output_data = output_buffer.getvalue()
                    file_extension = "parquet"
                    mime_type = "application/octet-stream"
                elif output_format == "ESRI Shapefile":
                    output_buffer = io.BytesIO()
                    result_gdf.to_file(output_buffer, driver="ESRI Shapefile")
                    output_data = output_buffer.getvalue()
                    file_extension = "zip"
                    mime_type = "application/zip"
                elif output_format == "GeoPackage":
                    output_buffer = io.BytesIO()
                    result_gdf.to_file(output_buffer, driver="GPKG")
                    output_data = output_buffer.getvalue()
                    file_extension = "gpkg"
                    mime_type = "application/geopackage+sqlite3"
                elif output_format == "CSV":
                    output_data = result_gdf.to_csv(index=False)
                    file_extension = "csv"
                    mime_type = "text/csv"
                elif output_format == "Excel":
                    output_buffer = io.BytesIO()
                    result_gdf.to_excel(output_buffer, index=False)
                    output_data = output_buffer.getvalue()
                    file_extension = "xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                st.download_button(
                    label=f"Download {output_format} file", data=output_data, file_name=f"output.{file_extension}", mime=mime_type
                )


if __name__ == "__main__":
    main()
