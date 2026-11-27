import os, io, zipfile, json, requests, xml.etree.ElementTree as ET

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw'
s = requests.Session()
s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})

gj = json.load(open(f'{BASE}/ibge/amesc_municipios_raw.geojson', encoding='utf-8'))
coords = []
def walk(c):
    if isinstance(c[0], (int, float)): coords.append(c)
    else:
        for x in c: walk(x)
for f in gj['features']: walk(f['geometry']['coordinates'])
minx, maxx = min(c[0] for c in coords), max(c[0] for c in coords)
miny, maxy = min(c[1] for c in coords), max(c[1] for c in coords)
bbox_xy = f'{minx},{miny},{maxx},{maxy},EPSG:4326'
bbox_raw = f'{minx},{miny},{maxx},{maxy}'

# 1. Probe ANEEL SIGEL REST services
print('=== 1. ANEEL SIGEL ===', flush=True)
try:
    j = s.get('https://sigel.aneel.gov.br/arcgis/rest/services?f=json', timeout=15).json()
    print('  Folders:', j.get('folders'), 'Services:', [x['name'] for x in j.get('services', [])][:10], flush=True)
    for folder in (j.get('folders') or []):
        fj = s.get(f'https://sigel.aneel.gov.br/arcgis/rest/services/{folder}?f=json', timeout=15).json()
        print(f'  Folder {folder}:', [x['name'] for x in fj.get('services', [])][:12], flush=True)
except Exception as e:
    print('  ANEEL ERR:', e, flush=True)

# 2. Check SIGSC Ilhas & IMA APP
for name, url in [
    ('sigsc_ilhas', f'https://sigsc.sc.gov.br/sigserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=SIGSC:INDE_ilha&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_app', f'https://geo.ima.sc.gov.br/geoserver/ima/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:ima_hidrografia_app&outputFormat=application/json&bbox={bbox_xy}'),
]:
    try:
        r = s.get(url, timeout=35)
        if r.status_code == 200 and r.content.lstrip().startswith(b'{'):
            open(f'{BASE}/wfs/{name}.geojson', 'wb').write(r.content)
            print(f'  OK {name}: {len(r.json().get("features", []))} feats', flush=True)
        else:
            print(f'  FAIL {name}: HTTP {r.status_code}', flush=True)
    except Exception as e:
        print(f'  ERR {name}: {e}', flush=True)

# 3. Inspect RIGeo zip contents for remaining AMESC cities where 0 files were extracted
class FastRemoteZipFile(io.RawIOBase):
    def __init__(self, url, session, block_size=2*1024*1024):
        self.url, self.session, self.block_size, self.pos, self.buf_start, self.buf = url, session, block_size, 0, -1, b''
        self.size = int(self.session.head(url, timeout=15).headers.get('Content-Length', 0))
    def seekable(self): return True
    def readable(self): return True
    def seek(self, o, w=0):
        self.pos = o if w == 0 else (self.pos + o if w == 1 else self.size + o)
        return self.pos
    def tell(self): return self.pos
    def read(self, n=-1):
        if n == -1: n = self.size - self.pos
        if self.pos >= self.size or n == 0: return b''
        out = bytearray()
        while len(out) < n and self.pos < self.size:
            if not (self.buf_start <= self.pos < self.buf_start + len(self.buf)):
                end = min(self.pos + max(self.block_size, n) - 1, self.size - 1)
                r = self.session.get(self.url, headers={'Range': f'bytes={self.pos}-{end}'}, timeout=60)
                self.buf_start, self.buf = self.pos, r.content
                if not self.buf: break
            off = self.pos - self.buf_start
            take = min(n - len(out), len(self.buf) - off)
            out.extend(self.buf[off:off+take])
            self.pos += take
        return bytes(out)

print('\n=== 3. RIGEO REMAINING SHPS ===', flush=True)
links = json.load(open(f'{BASE}/rigeo_amesc/rigeo_links.json', encoding='utf-8'))
for cd7, info in links.items():
    cdir = f'{BASE}/rigeo_amesc/{cd7}'
    if any(f.endswith('.shp') for f in os.listdir(cdir)):
        continue
    sig_url = info.get('sig_url')
    if not sig_url:
        # Look for ANY zip in ORIGINAL bundle
        uuid = info['rigeo_url'].split('/')[-1]
        bundles = s.get(f'https://rigeo.sgb.gov.br/server/api/core/items/{uuid}/bundles', timeout=15).json()
        for b in bundles.get('_embedded', {}).get('bundles', []):
            if b['name'] != 'ORIGINAL': continue
            bits = s.get(b['_links']['bitstreams']['href'], timeout=15).json().get('_embedded', {}).get('bitstreams', [])
            zips = [(bit['name'], bit['_links']['content']['href']) for bit in bits if bit['name'].lower().endswith('.zip') and 'mde' not in bit['name'].lower() and 'orto' not in bit['name'].lower()]
            print(f"  {info['municipio']} zips: {[z[0] for z in zips]}", flush=True)
            for zn, zurl in zips:
                if 'sig' in zn.lower() or 'susc' in zn.lower():
                    sig_url = zurl
                    break
    if sig_url:
        rz = FastRemoteZipFile(sig_url, s)
        with zipfile.ZipFile(rz) as z:
            shps = [i.filename for i in z.infolist() if i.filename.lower().endswith('.shp')]
            print(f"  {info['municipio']} shps: {shps[:15]}", flush=True)
            for i in z.infolist():
                fn = i.filename
                low = fn.lower()
                if any(k in low for k in ['inund', 'mov', 'desliz', 'enxur', 'corrida', 'suscet']) and low.endswith(('.shp', '.dbf', '.shx', '.prj', '.cpg')):
                    out = os.path.join(cdir, os.path.basename(fn))
                    open(out, 'wb').write(z.open(i).read())
