import os
from pathlib import Path
import folium
import requests

BASE_PATH = Path(__file__).parent
OUTPUT_DIR = BASE_PATH.parent / "public"  # GitHub Pages folder
OUTPUT_FILE = OUTPUT_DIR / "christchurch_rent_suburbs.html"

LINZ_API_KEY = os.environ.get("LINZ_API_KEY")
if LINZ_API_KEY is None:
    raise ValueError("Please set the LINZ_API_KEY environment variable")

# Suburbs list (Get this from notion eventually)
suburbs = [
    "Wigram",
    "Upper Riccarton",
    "Aidanfield",
    "Hillmorton",
    "Hoon Hay",
    "Somerfield",
    "Spreydon",
    "Beckenham",
    "Cashmere",
    "Halswell",
    "St Albans",
]

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
