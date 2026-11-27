import os, json, requests, urllib.parse

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw\wfs'
s = requests.Session()
s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})

gj = json.load(open(r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw\ibge\amesc_municipios_raw.geojson', encoding='utf-8'))
coords = []
def walk(c):
    if isinstance(c[0], (int, float)): coords.append(c)
    else:
        for x in c: walk(x)
for f in gj['features']: walk(f['geometry']['coordinates'])
minx, maxx = min(c[0] for c in coords), max(c[0] for c in coords)
miny, maxy = min(c[1] for c in coords), max(c[1] for c in coords)
bbox_raw = f'{minx},{miny},{maxx},{maxy}'
bbox_xy = f'{minx},{miny},{maxx},{maxy},EPSG:4326'

# 1. Inspect ANEEL PORTAL/Camadas & PORTAL/Distribuição
for svc in ['PORTAL/Camadas', 'PORTAL/Distribuição', 'sas/AreaConcessao']:
    enc = urllib.parse.quote(svc)
    try:
        j = s.get(f'https://sigel.aneel.gov.br/arcgis/rest/services/{enc}/MapServer?f=json', timeout=15).json()
        print(f'ANEEL {svc}:', [(l['id'], l['name']) for l in j.get('layers', [])], flush=True)
    except Exception as e:
        print(f'ANEEL {svc} ERR:', e, flush=True)

# 2. Fetch ANEEL layers (check PORTAL/Distribuição layer 0 & PORTAL/Camadas)
for name, svc, lid in [
    ('aneel_distribuicao', 'PORTAL/Distribuição', 0),
    ('aneel_transmissao_camadas', 'PORTAL/Camadas', 0),
]:
    enc = urllib.parse.quote(svc)
    url = f'https://sigel.aneel.gov.br/arcgis/rest/services/{enc}/MapServer/{lid}/query?where=1%3D1&geometry={bbox_raw}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson'
    try:
        r = s.get(url, timeout=30)
        if r.status_code == 200 and r.content.lstrip().startswith(b'{'):
            open(f'{BASE}/{name}.geojson', 'wb').write(r.content)
            print(f'  OK {name}: {len(r.json().get("features", []))} feats', flush=True)
    except Exception as e:
        print(f'  ERR {name}: {e}', flush=True)

# 3. Probe INCRA SIGEF WFS & IBGE BC25-SC WFS
for name, url in [
    ('incra_sigef', f'https://geoportal.incra.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=geonode:sigef_geo&outputFormat=application/json&bbox={bbox_xy}'),
    ('ibge_bc25_rodovias', f'https://geoservicos.ibge.gov.br/geoserver/CCAR/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=CCAR:BC25_SC_trecho_rodoviario_L&outputFormat=application/json&bbox={bbox_xy}'),
]:
    try:
        r = s.get(url, timeout=30)
        print(f'{name}: HTTP {r.status_code} len={len(r.content)} head={r.text[:90]!r}', flush=True)
        if r.status_code == 200 and r.content.lstrip().startswith(b'{'):
            open(f'{BASE}/{name}.geojson', 'wb').write(r.content)
            print(f'  feats: {len(r.json().get("features", []))}', flush=True)
    except Exception as e:
        print(f'{name} ERR: {e}', flush=True)
