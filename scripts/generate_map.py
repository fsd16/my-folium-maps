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
OUTPUT_DIR = BASE_PATH.parent / "docs"  # GitHub Pages folder
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


# ---------- PULL LINKS FROM NOTION ----------
notion = Client(auth=NOTION_TOKEN)
database = notion.databases.query(database_id=DATABASE_ID)

map_links = []
for page in database["results"]:  # type: ignore
    prop = page["properties"].get("Maps Link")
    if prop and prop.get("url"):
        map_links.append(prop["url"])

if not map_links:
    raise ValueError("No map links found in the Notion database")

# ---------- EXPAND URLS & EXTRACT COORDS ----------
coords = []
for link in map_links:
    try:
        expanded = expand_url(link)
        coord = extract_coords(expanded)
        if coord:
            coords.append(coord)
            print(f"Found: {coord}")
    except Exception as e:
        print(f"Failed to process {link}: {e}")

if not coords:
    raise ValueError("No valid coordinates extracted")

# ---------- GENERATE MAP ----------
m = folium.Map(location=coords[0], zoom_start=14)
for lat, lon in coords:
    folium.Marker([lat, lon]).add_to(m)

m.fit_bounds(coords)
m.save(OUTPUT_FILE)
print(f"✅ Map saved as {OUTPUT_FILE}")

# Optional: open locally for testing
# import webbrowser
# webbrowser.open(f"file://{OUTPUT_FILE}")
