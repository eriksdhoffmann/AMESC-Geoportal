import os, re, requests
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw\fbds'
os.makedirs(BASE, exist_ok=True)

AMESC = [
    ('ARARANGUA', '4201406'),
    ('BALNEARIO_ARROIO_DO_SILVA', '4201950'),
    ('BALNEARIO_GAIVOTA', '4202073'),
    ('ERMO', '4205191'),
    ('JACINTO_MACHADO', '4208708'),
    ('MARACAJA', '4210407'),
    ('MELEIRO', '4210803'),
    ('MORRO_GRANDE', '4211256'),
    ('PASSO_DE_TORRES', '4212254'),
    ('PRAIA_GRANDE', '4213807'),
    ('SANTA_ROSA_DO_SUL', '4215653'),
    ('SAO_JOAO_DO_SUL', '4216404'),
    ('SOMBRIO', '4217709'),
    ('TIMBE_DO_SUL', '4218103'),
    ('TURVO', '4218806'),
]

def download_city(item):
    slug, cd = item
    s = requests.Session()
    s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})
    cdir = os.path.join(BASE, slug)
    os.makedirs(cdir, exist_ok=True)
    cnt = 0
    for sub in ['USO', 'APP', 'HIDROGRAFIA']:
        url = f'https://geo.fbds.org.br/SC/{slug}/{sub}/'
        try:
            r = s.get(url, timeout=20)
            if r.status_code != 200: continue
            files = sorted(set(re.findall(r'href="([^"]+\.(?:shp|dbf|shx|prj|cpg))"', r.text, re.I)))
            sdir = os.path.join(cdir, sub)
            os.makedirs(sdir, exist_ok=True)
            for href in files:
                if '_APP_USO' in href.upper(): continue
                fn = os.path.basename(href)
                out = os.path.join(sdir, fn)
                if os.path.exists(out) and os.path.getsize(out) > 0:
                    cnt += 1
                    continue
                fr = s.get(urljoin(url, href), timeout=60)
                if fr.status_code == 200:
                    open(out, 'wb').write(fr.content)
                    cnt += 1
        except Exception as e:
            print(f'  ERR {slug}/{sub}: {e}', flush=True)
    print(f'FBDS {slug:26s}: {cnt} files OK', flush=True)

with ThreadPoolExecutor(max_workers=5) as ex:
    ex.map(download_city, AMESC)
print('ALL 15 FBDS DOWNLOADED!', flush=True)
