import os, json, requests

BASE = r'C:\Users\Win11\Downloads\AMESC-Geoportal\data_raw'
os.makedirs(f'{BASE}/wfs', exist_ok=True)
os.makedirs(f'{BASE}/cnes', exist_ok=True)
os.makedirs(f'{BASE}/ibge', exist_ok=True)

AMESC = [
    ('Araranguá', '4201406', '420140'),
    ('Balneário Arroio do Silva', '4201950', '420195'),
    ('Balneário Gaivota', '4202073', '420207'),
    ('Ermo', '4205191', '420519'),
    ('Jacinto Machado', '4208708', '420870'),
    ('Maracajá', '4210407', '421040'),
    ('Meleiro', '4210803', '421080'),
    ('Morro Grande', '4211256', '421125'),
    ('Passo de Torres', '4212254', '421225'),
    ('Praia Grande', '4213807', '421380'),
    ('Santa Rosa do Sul', '4215653', '421565'),
    ('São João do Sul', '4216404', '421640'),
    ('Sombrio', '4217709', '421770'),
    ('Timbé do Sul', '4218103', '421810'),
    ('Turvo', '4218806', '421880'),
]

s = requests.Session()
s.headers.update({'User-Agent': 'AMESC-Geoportal/1.0'})

# 1. Paginated DataSUS CNES (API returns max 20 per page)
print('=== 1. DATASUS CNES PAGINADO (15 MUNICÍPIOS) ===', flush=True)
all_cnes = []
for nm, cd7, cd6 in AMESC:
    offset = 0
    seen_cnes = set()
    city_cnt = 0
    while True:
        url = f'https://apidadosabertos.saude.gov.br/cnes/estabelecimentos?codigo_municipio={cd6}&status=1&limit=20&offset={offset}'
        try:
            r = s.get(url, headers={'Accept': 'application/json'}, timeout=25)
            if r.status_code != 200: break
            ests = r.json().get('estabelecimentos', [])
            if not ests: break
            new_in_page = 0
            for e in ests:
                cid = e.get('codigo_cnes')
                if cid in seen_cnes: continue
                seen_cnes.add(cid)
                e['_nm_mun'] = nm
                e['_cd_mun'] = cd7
                all_cnes.append(e)
                new_in_page += 1
                city_cnt += 1
            if len(ests) < 20 or new_in_page == 0: break
            offset += len(ests)
        except Exception as ex:
            print(f'  CNES {nm} ERR: {ex}', flush=True)
            break
    print(f'  CNES {nm:26s}: {city_cnt} ativos', flush=True)

with open(f'{BASE}/cnes/amesc_cnes.json', 'w', encoding='utf-8') as f:
    json.dump(all_cnes, f, ensure_ascii=False)
print(f'TOTAL CNES AMESC: {len(all_cnes)}', flush=True)

# Compute AMESC bbox
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
print(f'\nAMESC BBOX: {bbox_raw}', flush=True)

# 2. GeoFTP IBGE Bairros & Distritos SC (GPKG)
print('\n=== 2. IBGE GEOFTP BAIRROS & DISTRITOS SC ===', flush=True)
for fn, url in [
    ('SC_bairros_CD2022.gpkg', 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/bairros/gpkg/UF/SC/SC_bairros_CD2022.gpkg'),
    ('SC_distritos_CD2022.gpkg', 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/distritos/gpkg/UF/SC/SC_distritos_CD2022.gpkg'),
]:
    out = f'{BASE}/ibge/{fn}'
    if not os.path.exists(out):
        try:
            r = s.get(url, timeout=60)
            if r.status_code == 200:
                open(out, 'wb').write(r.content)
                print(f'  {fn}: {len(r.content):,} B', flush=True)
            else:
                print(f'  {fn}: HTTP {r.status_code}', flush=True)
        except Exception as e:
            print(f'  {fn} ERR: {e}', flush=True)

# 3. Regional WFS & ArcGIS REST layers
print('\n=== 3. REGIONAL WFS / REST LAYERS ===', flush=True)
targets = [
    ('ibge_setores_2022', f'https://geoservicos.ibge.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=CGMAT:pbqg22_26_SetoresCensitarios_SetoresCensitarios&outputFormat=application/json&bbox={bbox_xy}'),
    ('ibge_geologia', f'https://geoservicos.ibge.gov.br/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=BDIA:geol_area&outputFormat=application/json&bbox={bbox_xy}'),
    ('ibge_geomorfologia', f'https://geoservicos.ibge.gov.br/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=BDIA:geom_area&outputFormat=application/json&bbox={bbox_xy}'),
    ('ibge_pedologia', f'https://geoservicos.ibge.gov.br/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=BDIA:pedo_area&outputFormat=application/json&bbox={bbox_xy}'),
    ('ibge_vegetacao', f'https://geoservicos.ibge.gov.br/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=BDIA:vege_area&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_bacias', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:ft_bacia_hidrografica&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_fitogeografico', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:ft_fitogeografico&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_declividade', f'https://geo.ima.sc.gov.br/geoserver/ima/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:declividade&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_licenciamento', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:sinfat_licenciamento_ima_pontos&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_autos', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:auto_infracacao_ambiental&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_embargos', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:gaia_embargos&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_funai_ti', f'https://geo.ima.sc.gov.br/geoserver/ima/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=ima:funai_terra_indigena&outputFormat=application/json&bbox={bbox_xy}'),
    ('ima_mma_ucs', f'https://geo.ima.sc.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=externos:mma_ucs&outputFormat=application/json&bbox={bbox_xy}'),
    ('sgb_risco', f'https://geoservicos.sgb.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=gestao-territorial:risco_geologico&outputFormat=application/json&bbox={bbox_xy}'),
    ('sgb_siagas', f'https://geoservicos.sgb.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=hidrogeologia:siagas&outputFormat=application/json&bbox={bbox_xy}'),
    ('sgb_hidrogeo', f'https://geoservicos.sgb.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=hidrogeologia:dominios_hidrogeologicos_2_5m&outputFormat=application/json&bbox={bbox_xy}'),
    ('dnit_snv', f'https://servicos.dnit.gov.br/dnitgeo/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=vgeo:vw_snv_rod&outputFormat=application/json&bbox={bbox_xy}'),
    ('dnit_oae', f'https://servicos.dnit.gov.br/dnitgeo/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=vgeo:vw_oae&outputFormat=application/json&bbox={bbox_xy}'),
    ('iphan_sitios', f'https://servicos.dnit.gov.br/dnitgeo/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=vgeo:vw_iphan_sitios_arq&outputFormat=application/json&bbox={bbox_xy}'),
    ('sigsc_ottobacias', f'https://sigsc.sc.gov.br/sigserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=SIGSC:ANA_ottobacia&outputFormat=application/json&bbox={bbox_xy}'),
    ('sigsc_areas_umidas', f'https://sigsc.sc.gov.br/sigserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=SIGSC:INDE_area_umida&outputFormat=application/json&bbox={bbox_xy}'),
    ('aneel_transmissao', f'https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmissao/MapServer/1/query?where=1%3D1&geometry={bbox_raw}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson'),
    ('aneel_subestacoes', f'https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Transmissao/MapServer/3/query?where=1%3D1&geometry={bbox_raw}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson'),
    ('aneel_distribuicao', f'https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Distribuicao/MapServer/0/query?where=1%3D1&geometry={bbox_raw}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson'),
]

for name, url in targets:
    out = f'{BASE}/wfs/{name}.geojson'
    try:
        r = s.get(url, timeout=45)
        if r.status_code == 200 and r.content.lstrip().startswith(b'{'):
            open(out, 'wb').write(r.content)
            fc = len(r.json().get('features', []))
            print(f'  OK {name:22s}: {fc:5d} feats ({len(r.content)/1024:.1f} KB)', flush=True)
        else:
            print(f'  FAIL {name:20s}: HTTP {r.status_code} {r.text[:100]}', flush=True)
    except Exception as e:
        print(f'  ERR {name:21s}: {str(e)[:90]}', flush=True)
