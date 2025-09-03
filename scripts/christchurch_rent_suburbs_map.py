import os
from pathlib import Path
from re import sub
import folium
import notion
from notion import query

import requests

BASE_PATH = Path(__file__).parent
OUTPUT_DIR = BASE_PATH.parent / "public"  # GitHub Pages folder
OUTPUT_FILE = OUTPUT_DIR / "christchurch_rent_suburbs.html"

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if NOTION_TOKEN is None:
    raise ValueError("Please set the NOTION_TOKEN environment variable")

LINZ_API_KEY = os.environ.get("LINZ_API_KEY")
if LINZ_API_KEY is None:
    raise ValueError("Please set the LINZ_API_KEY environment variable")

suburbs = []

page = notion.Block("24c33ffcade880be9a38eb704e58d526")
res = page.retrieve_children()["results"]
inside_suburb_section = False
for re in res:
    if re["type"] == "heading_2":
        text = "".join([t["plain_text"] for t in re["heading_2"]["rich_text"]])
        if text.strip().lower() == "suburbs":
            inside_suburb_section = True
        else:
            inside_suburb_section = False

    if inside_suburb_section and re["type"] == "heading_3":
        suburb = re["heading_3"]["rich_text"][-1]["plain_text"]
        suburbs.append(suburb)

# Build LINZ WFS request
cql_filter = f"name IN ('{'\',\''.join(suburbs)}')"
url = (
    f"https://data.linz.govt.nz/services;key={LINZ_API_KEY}/wfs?"
    f"service=WFS&version=2.0.0&request=GetFeature&"
    f"typeNames=layer-113764&outputFormat=application/json&"
    f"CQL_FILTER={cql_filter}"
)

# Fetch GeoJSON data
response = requests.get(url)
response.raise_for_status()
geojson_data = response.json()

# Create base map
m = folium.Map(tiles="OpenStreetMap")

# Add all suburbs to the map
folium.GeoJson(
    geojson_data,
    name="Suburbs",
    style_function=lambda feature: {
        "color": "#0074D9",
        "weight": 2,
        "fillColor": "#7FDBFF",
        "fillOpacity": 0.3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Suburb:"]),
).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)
m.fit_bounds(m.get_bounds())  # type: ignore

# Save to HTML
m.save(OUTPUT_FILE)
print(f"✅ Map saved as {OUTPUT_FILE}")
