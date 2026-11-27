import os, json, requests

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw'
os.makedirs(f'{BASE}/osm', exist_ok=True)

gj = json.load(open(f'{BASE}/ibge/amesc_municipios_raw.geojson', encoding='utf-8'))
coords = []
def walk(c):
    if isinstance(c[0], (int, float)): coords.append(c)
    else:
        for x in c: walk(x)
for f in gj['features']: walk(f['geometry']['coordinates'])
minx, maxx = min(c[0] for c in coords), max(c[0] for c in coords)
miny, maxy = min(c[1] for c in coords), max(c[1] for c in coords)

# Split into 2 latitude halves (North & South) so Overpass is super fast and never hits 502
midy = (miny + maxy) / 2.0
halves = [
    ('north', midy - 0.002, minx - 0.005, maxy + 0.005, maxx + 0.005),
    ('south', miny - 0.005, minx - 0.005, midy + 0.002, maxx + 0.005),
]

s = requests.Session()
s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})

for tag, south, west, north, east in halves:
    q = f"""[out:json][timeout:60];
(
  node["place"]({south},{west},{north},{east});
  way["highway"~"^(trunk|primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|track|path)$"]({south},{west},{north},{east});
  way["bridge"="yes"]({south},{west},{north},{east});
  node["amenity"~"^(school|kindergarten|college|university|hospital|clinic|doctors|pharmacy|townhall|police|fire_station|post_office|community_centre|library|place_of_worship|bus_station)$"]({south},{west},{north},{east});
  way["amenity"~"^(school|kindergarten|college|university|hospital|clinic|doctors|pharmacy|townhall|police|fire_station|post_office|community_centre|library|place_of_worship)$"]({south},{west},{north},{east});
  node["tourism"]({south},{west},{north},{east});
  way["tourism"]({south},{west},{north},{east});
  node["waterway"="waterfall"]({south},{west},{north},{east});
  node["natural"~"^(peak|spring|cave_entrance|cliff|beach)$"]({south},{west},{north},{east});
  way["leisure"~"^(park|pitch|sports_centre|nature_reserve)$"]({south},{west},{north},{east});
  way["landuse"="industrial"]({south},{west},{north},{east});
);
out body center;
>;
out skel qt;"""
    for mirror in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        try:
            r = s.post(mirror, data={'data': q}, timeout=75)
            print(f'OSM {tag} ({mirror}): HTTP {r.status_code} len={len(r.content)}', flush=True)
            if r.status_code == 200 and len(r.content) > 1000:
                open(f'{BASE}/osm/osm_{tag}.json', 'wb').write(r.content)
                break
        except Exception as e:
            print(f'OSM {tag} ERR: {e}', flush=True)
