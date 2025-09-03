import json
import os
import re
from pathlib import Path

import folium
import requests
from notion_client import Client

# ---------- CONFIG ----------
BASE_PATH = Path(__file__).parent
CACHE_FILE = BASE_PATH / "url_cache.json"
OUTPUT_DIR = BASE_PATH.parent / "public"  # GitHub Pages folder
OUTPUT_FILE = OUTPUT_DIR / "map.html"

DATABASE_ID = "24f33ffcade8804d8a83c74b5f601067"
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if NOTION_TOKEN is None:
    raise ValueError("Please set the NOTION_TOKEN environment variable")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- URL CACHE ----------
if CACHE_FILE.exists():
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}


def expand_url(short_url):
    if short_url in cache:
        return cache[short_url]

    r = requests.get(short_url, allow_redirects=True)
    cache[short_url] = r.url

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    return r.url


# ---------- EXTRACT COORDS ----------
def extract_coords(url):
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return float(match.group(1)), float(match.group(2))
    match = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None


# ---------- GET URLS, EXPAND URLS & EXTRACT COORDS ----------

notion = Client(auth=NOTION_TOKEN)
database = notion.databases.query(database_id=DATABASE_ID)

coords = []
markers = []

for page in database["results"]:  # type: ignore
    # Pull the map link
    link_prop = page["properties"].get("Maps Link")
    if not link_prop or not link_prop.get("url"):
        continue
    link = link_prop["url"]

    # Pull the destination
    dest_prop = page["properties"].get("Destination")
    destination = ""
    if dest_prop:
        # Usually text properties are in dest_prop["title"]
        title_content = dest_prop.get("title", [])
        if title_content:
            destination = title_content[0]["text"]["content"]

    # Expand URL and extract coordinates
    try:
        expanded = expand_url(link)
        coord = extract_coords(expanded)
        if coord:
            coords.append(coord)
            markers.append((coord, destination))
            print(f"Found: {coord} -> {destination}")
    except Exception as e:
        print(f"Failed to process {link}: {e}")


# ---------- GENERATE MAP ----------
m = folium.Map()

for (lat, lon), destination in markers:
    folium.Marker(
        [lat, lon],
        popup=destination,  # Shows when clicked
        tooltip=destination,  # Shows on hover
    ).add_to(m)


m.fit_bounds(coords)
m.save(OUTPUT_FILE)
print(f"✅ Map saved as {OUTPUT_FILE}")
