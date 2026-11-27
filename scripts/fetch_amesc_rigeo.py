import os, io, zipfile, json, requests

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw\rigeo_amesc'
os.makedirs(BASE, exist_ok=True)

RIGEO_ITEMS = [
    ('Araranguá', '4201406', '87b85cba-acb2-4f21-a9af-6eaf207ad2d0'),
    ('Balneário Arroio do Silva', '4201950', '80bc7506-ceb0-43ec-8355-03625e439c75'),
    ('Balneário Gaivota', '4202073', 'db761e97-5cbe-4a34-9dc6-145629d3777a'),
    ('Ermo', '4205191', '8362a91c-d575-4471-85ac-e1f32d4f179b'),
    ('Jacinto Machado', '4208708', 'c43f811a-d579-4e78-aa19-cb4e54394f08'),
    ('Maracajá', '4210407', 'e9ae5078-f495-4495-bfbe-2cf381bd8742'),
    ('Meleiro', '4210803', 'a2399b88-1667-4451-901a-6d7948f0ffc4'),
    ('Morro Grande', '4211256', '4cd6f1fb-56e0-4571-a779-82dfc816801a'),
    ('Praia Grande', '4213807', 'f89846ad-4bd8-442f-ac8b-2d2fb8ad9ac4'),
    ('Santa Rosa do Sul', '4215653', 'd92dab50-88e4-48f2-b9a8-07e438e9168e'),
    ('São João do Sul', '4216404', '0c1d826e-997c-419a-83b9-8775a0a2639a'),
    ('Sombrio', '4217709', 'e4456995-7ae8-46d6-9d56-7e8e12782aa5'),
    ('Timbé do Sul', '4218103', 'c1412e29-7dee-4f8e-bd92-cec04fe89181'),
    ('Turvo', '4218806', '16c2343a-44f7-49f2-a0ba-973337c3fa4d'),
]

class FastRemoteZipFile(io.RawIOBase):
    def __init__(self, url, session, block_size=2*1024*1024):
        self.url = url
        self.session = session
        h = self.session.head(url, timeout=15)
        self.size = int(h.headers.get('Content-Length', 0))
        self.block_size = block_size
        self.pos = 0
        self.buf_start = -1
        self.buf = b''
    def seekable(self): return True
    def readable(self): return True
    def seek(self, offset, whence=0):
        if whence == 0: self.pos = offset
        elif whence == 1: self.pos += offset
        elif whence == 2: self.pos = self.size + offset
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
                self.buf_start = self.pos
                self.buf = r.content
                if not self.buf: break
            off = self.pos - self.buf_start
            take = min(n - len(out), len(self.buf) - off)
            out.extend(self.buf[off:off+take])
            self.pos += take
        return bytes(out)

s = requests.Session()
s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})

catalog_links = {}
for nm, cd7, uuid in RIGEO_ITEMS:
    cdir = os.path.join(BASE, cd7)
    os.makedirs(cdir, exist_ok=True)
    catalog_links[cd7] = {'municipio': nm, 'rigeo_url': f'https://rigeo.sgb.gov.br/items/{uuid}', 'pdf_url': None, 'sig_url': None}
    try:
        bundles = s.get(f'https://rigeo.sgb.gov.br/server/api/core/items/{uuid}/bundles', timeout=15).json()
        for b in bundles.get('_embedded', {}).get('bundles', []):
            if b['name'] != 'ORIGINAL': continue
            bits = s.get(b['_links']['bitstreams']['href'], timeout=15).json().get('_embedded', {}).get('bitstreams', [])
            for bit in bits:
                bn = bit['name']
                href = bit['_links']['content']['href']
                if bn.lower().endswith('.pdf'):
                    catalog_links[cd7]['pdf_url'] = href
                if 'suscet' in bn.lower() and bn.lower().endswith('.zip'):
                    catalog_links[cd7]['sig_url'] = href
                    # Extract ONLY Suscetibilidade shapefiles (Inundacao, MovimentoDeMassa, Corridas, Enxurradas)
                    rz = FastRemoteZipFile(href, s)
                    if rz.size == 0: continue
                    with zipfile.ZipFile(rz) as z:
                        ext_cnt = 0
                        for info in z.infolist():
                            fn = info.filename
                            low = fn.lower()
                            if info.is_dir(): continue
                            if any(k in low for k in ['suscetibilidadeinundacao', 'suscetibilidademovimentodemassa', 'suscetibilidadecorridas', 'suscetibilidadeenxurradas', 'suscet_inund', 'suscet_mov']) and low.endswith(('.shp', '.dbf', '.shx', '.prj', '.cpg')):
                                out = os.path.join(cdir, os.path.basename(fn))
                                if not (os.path.exists(out) and os.path.getsize(out) == info.file_size):
                                    open(out, 'wb').write(z.open(info).read())
                                ext_cnt += 1
                        print(f'RIGeo {nm:25s}: extracted {ext_cnt} suscet files', flush=True)
    except Exception as e:
        print(f'RIGeo {nm:25s} ERR: {e}', flush=True)

json.dump(catalog_links, open(os.path.join(BASE, 'rigeo_links.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('DONE RIGEO AMESC!', flush=True)
