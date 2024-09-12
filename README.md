# pcodegenerator
Generates pcodes for geospatial datasets based on COD 

## Install : 
```bash
pip install pcodegenerator
```

Make sure you have ogr2ogr installed on your machine too.

## Prepare :

Download / Update with the latest COD edge matched dataset , Know more https://fieldmaps.io/ 

```bash
pcodeprepare --admin 4
```

## Usage

Example to add pcode dataset on localities 

```bash
pcodegenerator --source ./adm4_polygons.parquet --input locality.geojson --output locality_pcodes.geojson
```



## Resources : 
All credits to respective providers 

### ISO2 naming

Source : https://www.fao.org/nocs/en/  

Multilingual database of Names of Countries and Territories (NOCS) 

### P-Codes Generation Logic

https://humanitarian.atlassian.net/wiki/spaces/imtoolbox/pages/222265609/P-codes+and+gazetteers

![pcode](https://github.com/user-attachments/assets/fd030038-f5cb-46af-b012-697478208a03)

### Admin boundaries

Source : https://www.geoboundaries.org/ 
License :  CC BY 4.0 license

![image](https://github.com/user-attachments/assets/3fd2f61a-5618-4b6c-a5ba-79cff4cd40ea)


### Global boundaries with COD attributes ( Including subnational geom )
Source : https://fieldmaps.io/data 

API :  https://data.fieldmaps.io/edge-matched.json 

License : Open Data Commons Open Database License (ODbL) 

![image](https://github.com/user-attachments/assets/639882ee-9148-478c-81a2-820c75ae15ff)
