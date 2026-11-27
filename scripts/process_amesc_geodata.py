import os, json, glob, warnings
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

warnings.filterwarnings('ignore')

ROOT = r'C:\Users\Win11\Downloads\AMESC-Geoportal'
RAW = os.path.join(ROOT, 'data_raw')
OUT = os.path.join(ROOT, 'data')
JS_OUT = os.path.join(ROOT, 'js')
os.makedirs(OUT, exist_ok=True)
os.makedirs(JS_OUT, exist_ok=True)

AMESC_LIST = [
    ('Araranguá', 'ARARANGUA', '4201406'),
    ('Balneário Arroio do Silva', 'BALNEARIO_ARROIO_DO_SILVA', '4201950'),
    ('Balneário Gaivota', 'BALNEARIO_GAIVOTA', '4202073'),
    ('Ermo', 'ERMO', '4205191'),
    ('Jacinto Machado', 'JACINTO_MACHADO', '4208708'),
    ('Maracajá', 'MARACAJA', '4210407'),
    ('Meleiro', 'MELEIRO', '4210803'),
    ('Morro Grande', 'MORRO_GRANDE', '4211256'),
    ('Passo de Torres', 'PASSO_DE_TORRES', '4212254'),
    ('Praia Grande', 'PRAIA_GRANDE', '4213807'),
    ('Santa Rosa do Sul', 'SANTA_ROSA_DO_SUL', '4215653'),
    ('São João do Sul', 'SAO_JOAO_DO_SUL', '4216404'),
    ('Sombrio', 'SOMBRIO', '4217709'),
    ('Timbé do Sul', 'TIMBE_DO_SUL', '4218103'),
    ('Turvo', 'TURVO', '4218806'),
]
AMESC_CODES = {c for _, _, c in AMESC_LIST}

# 1. Load 15 Municipal Boundaries & Dissolve Outer AMESC Boundary
print('=== 1. MUNICÍPIOS E CONTORNO AMESC ===', flush=True)
mun_gdf = gpd.read_file(f'{RAW}/ibge/amesc_municipios_raw.geojson').to_crs('EPSG:4326')
mun_gdf['geometry'] = mun_gdf.geometry.buffer(0)
# Compute accurate area in SIRGAS 2000 UTM 22S
mun_utm = mun_gdf.to_crs('EPSG:31982')
mun_gdf['AREA_KM2'] = (mun_utm.geometry.area / 1e6).round(3)
mun_gdf['FONTE'] = 'IBGE — Malha Municipal Oficial (SIRGAS 2000)'

amesc_outer = unary_union(mun_gdf.geometry)
minx, miny, maxx, maxy = amesc_outer.bounds
outer_gdf = gpd.GeoDataFrame([{'REGIAO': 'AMESC — Extremo Sul Catarinense', 'MUNICIPIOS': 15, 'AREA_KM2': round(float(mun_gdf['AREA_KM2'].sum()), 2)}], geometry=[amesc_outer], crs='EPSG:4326')

def round_coords(obj, prec=5):
    if isinstance(obj, float): return round(obj, prec)
    if isinstance(obj, list): return [round_coords(x, prec) for x in obj]
    if isinstance(obj, dict): return {k: round_coords(v, prec) for k, v in obj.items()}
    return obj

def save_geojson(gdf, layer_id, simplify_tol=0.0, prec=5, clip=True, keep_cols=None, fast_intersects=False):
    if gdf is None or len(gdf) == 0:
        print(f'  SKIP {layer_id}: empty', flush=True)
        return None
    if gdf.crs is None: gdf = gdf.set_crs('EPSG:4326')
    else: gdf = gdf.to_crs('EPSG:4326')
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    # Fast rectangular clip first (1000x faster on state-wide multipolygons like declividade/hidrogeo)
    if clip or fast_intersects:
        try:
            gdf['geometry'] = gdf.geometry.clip_by_rect(minx - 0.01, miny - 0.01, maxx + 0.01, maxy + 0.01)
            gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
        except Exception:
            pass
        gdf = gdf[gdf.geometry.intersects(amesc_outer)].copy()
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    if len(gdf) == 0:
        print(f'  SKIP {layer_id}: empty after intersects', flush=True)
        return None
    # Simplify BEFORE exact clip for huge speed boost
    if simplify_tol > 0:
        gdf['geometry'] = gdf.geometry.simplify(simplify_tol, preserve_topology=True)
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    if clip and not fast_intersects:
        try:
            gdf = gpd.clip(gdf, amesc_outer)
        except Exception:
            try:
                gdf['geometry'] = gdf.geometry.buffer(0)
                gdf = gpd.clip(gdf, amesc_outer)
            except Exception:
                pass
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    if len(gdf) == 0:
        print(f'  SKIP {layer_id}: empty after clip', flush=True)
        return None
    if keep_cols:
        cols = [c for c in keep_cols if c in gdf.columns] + ['geometry']
        gdf = gdf[cols]
    for c in gdf.columns:
        if c == 'geometry': continue
        gdf[c] = gdf[c].apply(lambda v: None if pd.isna(v) else (str(v).strip() if not isinstance(v, (int, float, bool)) else v))
    gj = json.loads(gdf.to_json())
    gj['features'] = [
        {'type': 'Feature', 'properties': f['properties'], 'geometry': round_coords(f['geometry'], prec)}
        for f in gj['features'] if f.get('geometry')
    ]
    out_path = os.path.join(OUT, f'{layer_id}.geojson')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(gj, f, ensure_ascii=False, separators=(',', ':'))
    print(f'  OK {layer_id:32s}: {len(gj["features"]):6d} feats | {os.path.getsize(out_path)/1024:7.1f} KB', flush=True)
    return gj

saved = {}
saved['amesc_municipios'] = save_geojson(mun_gdf, 'amesc_municipios', simplify_tol=0.00005, clip=False)
saved['amesc_limite_regional'] = save_geojson(outer_gdf, 'amesc_limite_regional', simplify_tol=0.00008, clip=False)

# Compute municipal bounds lookup
mun_meta = {}
for _, row in mun_gdf.iterrows():
    b = row.geometry.bounds
    mun_meta[row['CD_MUN']] = {
        'cd_mun': row['CD_MUN'],
        'nome': row['NM_MUN'],
        'slug': row['SLUG'],
        'area_km2': float(row['AREA_KM2']),
        'bounds': [[round(b[1], 4), round(b[0], 4)], [round(b[3], 4), round(b[2], 4)]],
        'center': [round((b[1]+b[3])/2, 4), round((b[0]+b[2])/2, 4)],
    }

# 2. IBGE Bairros, Distritos & Setores Censitários 2022
print('\n=== 2. IBGE BAIRROS, DISTRITOS & SETORES ===', flush=True)
if os.path.exists(f'{RAW}/ibge/SC_bairros_CD2022.gpkg'):
    g = gpd.read_file(f'{RAW}/ibge/SC_bairros_CD2022.gpkg')
    cd_col = next((c for c in g.columns if 'cd_mun' in c.lower()), None)
    nm_col = next((c for c in g.columns if 'nm_bairro' in c.lower()), None)
    mun_col = next((c for c in g.columns if 'nm_mun' in c.lower()), None)
    if cd_col:
        g = g[g[cd_col].astype(str).isin(AMESC_CODES)].copy()
        g['nome'] = g[nm_col] if nm_col else 'Bairro'
        g['municipio'] = g[mun_col] if mun_col else ''
        g['cd_mun'] = g[cd_col].astype(str)
        saved['amesc_bairros_ibge'] = save_geojson(g, 'amesc_bairros_ibge', simplify_tol=0.00006, clip=False, keep_cols=['nome', 'municipio', 'cd_mun'])

if os.path.exists(f'{RAW}/ibge/SC_distritos_CD2022.gpkg'):
    g = gpd.read_file(f'{RAW}/ibge/SC_distritos_CD2022.gpkg')
    cd_col = next((c for c in g.columns if 'cd_mun' in c.lower()), None)
    nm_col = next((c for c in g.columns if 'nm_dist' in c.lower()), None)
    mun_col = next((c for c in g.columns if 'nm_mun' in c.lower()), None)
    if cd_col:
        g = g[g[cd_col].astype(str).isin(AMESC_CODES)].copy()
        g['nome'] = g[nm_col] if nm_col else 'Distrito'
        g['municipio'] = g[mun_col] if mun_col else ''
        g['cd_mun'] = g[cd_col].astype(str)
        saved['amesc_distritos_ibge'] = save_geojson(g, 'amesc_distritos_ibge', simplify_tol=0.00008, clip=False, keep_cols=['nome', 'municipio', 'cd_mun'])

if os.path.exists(f'{RAW}/wfs/ibge_setores_2022.geojson'):
    g = gpd.read_file(f'{RAW}/wfs/ibge_setores_2022.geojson')
    g = g[g['cd_mun'].astype(str).isin(AMESC_CODES)].copy()
    g['situacao'] = g['nm_sit'].apply(lambda x: 'Urbana' if 'urbana' in str(x).lower() or 'núcleo' in str(x).lower() else 'Rural')
    saved['amesc_setores_ibge'] = save_geojson(g, 'amesc_setores_ibge', simplify_tol=0.00008, clip=False, keep_cols=['cd_setor', 'cd_mun', 'nm_mun', 'situacao', 'nm_sit'])

# 3. IBGE BDIA (Geologia, Geomorfologia, Pedologia, Vegetação)
print('\n=== 3. IBGE BDIA 1:250K ===', flush=True)
for raw_fn, lid, col_candidates, out_col in [
    ('ibge_geologia', 'amesc_geologia_ibge', ['nm_unidade', 'letra_simb', 'nm_lito1'], 'nm_unidade'),
    ('ibge_geomorfologia', 'amesc_geomorfologia_ibge', ['nm_unidade', 'nm_regiao', 'nm_dominio', 'categoria'], 'nm_unidade'),
    ('ibge_pedologia', 'amesc_pedologia_ibge', ['ordem', 'legenda', 'subordem'], 'ordem'),
    ('ibge_vegetacao', 'amesc_vegetacao_ibge', ['legenda', 'nm_uveg', 'legenda_1'], 'legenda'),
]:
    p = f'{RAW}/wfs/{raw_fn}.geojson'
    if os.path.exists(p):
        g = gpd.read_file(p)
        keep = [c for c in g.columns if c != 'geometry' and not c.lower().startswith(('id', 'cd_', 'ar_', 'shape'))][:6]
        saved[lid] = save_geojson(g, lid, simplify_tol=0.00012, keep_cols=keep)

# 4. IMA-SC, SGB/CPRM, DNIT, IPHAN, ANEEL, SIGSC
print('\n=== 4. IMA-SC, SGB, DNIT, IPHAN, ANEEL, SIGSC ===', flush=True)
wfs_jobs = [
    ('ima_bacias', 'amesc_bacias_ima', 0.00015, ['bhi_nm', 'bhi_nm_comite', 'bhi_ar_km2']),
    ('ima_fitogeografico', 'amesc_fitogeografico_ima', 0.00015, None),
    ('ima_declividade', 'amesc_declividade_ima', 0.00025, ['dec_cl', 'classe_decliv']),
    ('ima_app', 'amesc_app_ima', 0.00022, None),
    ('ima_licenciamento', 'amesc_licenciamento_ima', 0, ['nome_empreendimento', 'atividade', 'tipo_licenca', 'licenca_status', 'processo', 'municipio']),
    ('ima_autos', 'amesc_autos_ima', 0, ['aia_numero', 'aia_data', 'aia_categoria', 'aia_status', 'municipio']),
    ('ima_embargos', 'amesc_embargos_ima', 0.00008, None),
    ('ima_mma_ucs', 'amesc_ucs_mma', 0.00008, ['nome_uc', 'cd_cnuc', 'cria_ano', 'co_gestor', 'pl_manejo']),
    ('sgb_risco', 'amesc_setores_risco_sgb', 0.00004, ['municipio', 'num_setor', 'local', 'tipolo_g1', 'cobrade_01', 'grau_risco', 'num_edif', 'num_pess', 'descricao', 'sug_interv', 'data_setor']),
    ('sgb_siagas', 'amesc_pocos_siagas', 0, ['idt_ponto', 'str_local_ponto', 'str_natureza_ponto', 'str_tipo_situacao', 'str_uso_agua', 'str_aquifero', 'num_profundidade', 'num_vazao_especifica']),
    ('sgb_hidrogeo', 'amesc_hidrogeologia_sgb', 0.0002, ['nome_unida', 'dom', 'subdom', 'sigla_unid']),
    ('dnit_snv', 'amesc_rodovias_dnit', 0.0001, ['vl_br', 'sg_uf', 'ds_tipo_trecho', 'ds_superficie', 'vl_extensao']),
    ('dnit_oae', 'amesc_pontes_dnit', 0, None),
    ('iphan_sitios', 'amesc_iphan_sitios', 0, None),
    ('sigsc_ottobacias', 'amesc_ottobacias_sigsc', 0.00025, ['cobacia', 'cocursodag', 'nuordemcda']),
    ('sigsc_areas_umidas', 'amesc_areas_umidas_sigsc', 0.00018, None),
    ('sigsc_ilhas', 'amesc_ilhas_sigsc', 0.0001, None),
    ('aneel_distribuicao', 'amesc_aneel_concessao', 0.00015, None),
]

for raw_fn, lid, simp, keep in wfs_jobs:
    p = f'{RAW}/wfs/{raw_fn}.geojson'
    if not os.path.exists(p): continue
    if os.path.exists(f'{OUT}/{lid}.geojson') and os.path.getsize(f'{OUT}/{lid}.geojson') > 100:
        saved[lid] = json.load(open(f'{OUT}/{lid}.geojson', encoding='utf-8'))
        print(f'  CACHED {lid}', flush=True)
        continue
    try:
        g = gpd.read_file(p)
        if raw_fn == 'ima_declividade' and 'dec_cl' in g.columns:
            dec_map = {'0': '0–5% (Plano)', '5': '5–12% (Suave)', '12': '12–25% (Ondulado)', '25': '25–45% (Forte)', '45': '>45% (Escarpado)'}
            g['classe_decliv'] = g['dec_cl'].astype(str).map(lambda x: dec_map.get(x, x))
        if raw_fn == 'ima_fitogeografico' and 'fit_tp' in g.columns:
            fit_map = {
                '10_FLORE_NEBULAR_CRISTA': 'Floresta Nebular de Crista / Serra Geral',
                '08_FLOREST_TROP_PLAN_QUASUL': 'Floresta Tropical da Planície Quaternária Sul',
                '07_FLOREST_TROP_MERIDIONAL': 'Floresta Tropical Meridional / Encostas',
                '00_VEG_LITORANEA': 'Vegetação de Influência Fluvio-Marinha',
            }
            g['regiao_fito'] = g['fit_tp'].map(lambda x: fit_map.get(x, str(x)))
        fast_i = raw_fn in ('ima_declividade', 'ima_app', 'sigsc_ottobacias', 'sgb_hidrogeo', 'dnit_snv')
        saved[lid] = save_geojson(g, lid, simplify_tol=simp, keep_cols=keep, fast_intersects=fast_i)
    except Exception as e:
        print(f'  ERR {lid}: {e}', flush=True)

# 5. Merge RIGeo Suscetibilidade shapefiles across available AMESC municipalities (Araranguá, Jacinto Machado, Maracajá, Timbé do Sul)
print('\n=== 5. RIGEO SUSCETIBILIDADE REGIONAL ===', flush=True)
inund_parts, mov_parts = [], []
for cd7 in os.listdir(f'{RAW}/rigeo_amesc'):
    cdir = f'{RAW}/rigeo_amesc/{cd7}'
    if not os.path.isdir(cdir): continue
    for fn in os.listdir(cdir):
        if not fn.lower().endswith('.shp'): continue
        p = os.path.join(cdir, fn)
        try:
            g = gpd.read_file(p, encoding='latin1').to_crs('EPSG:4326')
            cls_col = next((c for c in g.columns if 'classe' in c.lower()), None)
            if cls_col:
                g['Classe'] = g[cls_col].astype(str).replace({'Media': 'Média', 'MEDIA': 'Média', 'ALTA': 'Alta', 'BAIXA': 'Baixa'})
            else:
                g['Classe'] = 'Suscetível'
            g['cd_mun'] = cd7
            g['municipio'] = mun_meta.get(cd7, {}).get('nome', cd7)
            if 'inund' in fn.lower():
                inund_parts.append(g[['Classe', 'cd_mun', 'municipio', 'geometry']])
            elif 'mov' in fn.lower():
                mov_parts.append(g[['Classe', 'cd_mun', 'municipio', 'geometry']])
        except Exception as e:
            print(f'  RIGeo {fn} ERR: {e}', flush=True)

if inund_parts:
    saved['amesc_suscet_inundacao_sgb'] = save_geojson(pd.concat(inund_parts, ignore_index=True), 'amesc_suscet_inundacao_sgb', simplify_tol=0.00014, clip=False)
if mov_parts:
    saved['amesc_suscet_movmassa_sgb'] = save_geojson(pd.concat(mov_parts, ignore_index=True), 'amesc_suscet_movmassa_sgb', simplify_tol=0.00016, clip=False)

# 6. Merge FBDS 1:5.000 across ALL 15 AMESC municipalities
print('\n=== 6. FBDS 1:5.000 (MOSAICO 15 MUNICÍPIOS) ===', flush=True)
fbds_buckets = {'USO': [], 'APP': [], 'RIOS_SIMPLES': [], 'RIOS_DUPLOS': [], 'MASSAS_DAGUA': [], 'NASCENTES': []}
fbds_uso_by_mun = {}

for nm, slug, cd7 in AMESC_LIST:
    cdir = f'{RAW}/fbds/{slug}'
    if not os.path.isdir(cdir): continue
    for sub in ['USO', 'APP', 'HIDROGRAFIA']:
        sdir = os.path.join(cdir, sub)
        if not os.path.isdir(sdir): continue
        for fn in os.listdir(sdir):
            if not fn.lower().endswith('.shp'): continue
            p = os.path.join(sdir, fn)
            g = gpd.read_file(p).to_crs('EPSG:4326')
            g['MUNICIPIO'] = nm
            g['CD_MUN'] = cd7
            up = fn.upper()
            if '_USO.SHP' in up:
                if 'CLASSE_USO' in g.columns and 'AREA_HA' in g.columns:
                    fbds_uso_by_mun[cd7] = g.groupby('CLASSE_USO')['AREA_HA'].sum().round(2).to_dict()
                fbds_buckets['USO'].append(g[['CLASSE_USO', 'AREA_HA', 'MUNICIPIO', 'CD_MUN', 'geometry']])
            elif '_APP.SHP' in up:
                cols = [c for c in ['HIDRO', 'APP_M', 'AREA_HA', 'MUNICIPIO', 'CD_MUN'] if c in g.columns] + ['geometry']
                fbds_buckets['APP'].append(g[cols])
            elif 'RIOS_SIMPLES' in up:
                cols = [c for c in ['HIDRO', 'COMP_KM', 'MUNICIPIO', 'CD_MUN'] if c in g.columns] + ['geometry']
                fbds_buckets['RIOS_SIMPLES'].append(g[cols])
            elif 'RIOS_DUPLOS' in up:
                cols = [c for c in ['HIDRO', 'AREA_HA', 'MUNICIPIO', 'CD_MUN'] if c in g.columns] + ['geometry']
                fbds_buckets['RIOS_DUPLOS'].append(g[cols])
            elif 'MASSAS_DAGUA' in up:
                cols = [c for c in ['NATUREZA', 'AREA_HA', 'MUNICIPIO', 'CD_MUN'] if c in g.columns] + ['geometry']
                fbds_buckets['MASSAS_DAGUA'].append(g[cols])
            elif 'NASCENTES' in up:
                cols = [c for c in ['HIDRO', 'MUNICIPIO', 'CD_MUN'] if c in g.columns] + ['geometry']
                fbds_buckets['NASCENTES'].append(g[cols])

for key, lid, simp, prec in [
    ('USO', 'amesc_fbds_uso_solo', 0.00028, 4),
    ('APP', 'amesc_fbds_app', 0.00025, 4),
    ('RIOS_SIMPLES', 'amesc_fbds_rios_simples', 0.00022, 4),
    ('RIOS_DUPLOS', 'amesc_fbds_rios_duplos', 0.00010, 5),
    ('MASSAS_DAGUA', 'amesc_fbds_massas_dagua', 0.00010, 5),
    ('NASCENTES', 'amesc_fbds_nascentes', 0, 4),
]:
    if fbds_buckets[key]:
        merged = gpd.GeoDataFrame(pd.concat(fbds_buckets[key], ignore_index=True), crs='EPSG:4326')
        saved[lid] = save_geojson(merged, lid, simplify_tol=simp, prec=prec, clip=False)

# 7. DataSUS CNES (775 health establishments across 15 AMESC cities)
print('\n=== 7. DATASUS CNES (775) ===', flush=True)
cnes_raw = json.load(open(f'{RAW}/cnes/amesc_cnes.json', encoding='utf-8'))
cnes_rows = []
for e in cnes_raw:
    lat, lon = e.get('latitude_estabelecimento_decimo_grau'), e.get('longitude_estabelecimento_decimo_grau')
    if lat is None or lon is None: continue
    try: lat, lon = float(lat), float(lon)
    except Exception: continue
    if not (-29.5 < lat < -28.4 and -50.4 < lon < -49.1): continue
    nat = str(e.get('codigo_natureza_juridica') or '')
    esfera = 'Pública Municipal' if nat.startswith('103') or nat.startswith('124') else ('Pública Estadual/Federal' if nat.startswith('1') else ('Sem Fins Lucrativos' if nat.startswith('3') else 'Privada / Empresarial'))
    cnes_rows.append({
        'cnes': str(e.get('codigo_cnes', '')),
        'nome': e.get('nome_fantasia') or e.get('nome_razao_social') or 'Estabelecimento de Saúde',
        'esfera': esfera,
        'municipio': e.get('_nm_mun', ''),
        'cd_mun': e.get('_cd_mun', ''),
        'endereco': f"{e.get('endereco_estabelecimento') or ''}, {e.get('numero_estabelecimento') or 'S/N'}".strip(', '),
        'bairro': e.get('bairro_estabelecimento') or '',
        'geometry': Point(lon, lat)
    })
if cnes_rows:
    saved['amesc_saude_cnes'] = save_geojson(gpd.GeoDataFrame(cnes_rows, crs='EPSG:4326'), 'amesc_saude_cnes', clip=False)

# 8. OpenStreetMap Regional (Rodovias, Sistema Viário, Escolas, Equipamentos, Pontes, Localidades, Turismo, Trilhas, Indústria)
print('\n=== 8. OPENSTREETMAP AMESC ===', flush=True)
nodes = {}
seen_el = set()
localidades, rodovias, viario, pontes, escolas, equip, turismo, trilhas, industria = [], [], [], [], [], [], [], [], []

for fn in ['osm_north.json', 'osm_south.json']:
    p = f'{RAW}/osm/{fn}'
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8'))
    for el in d.get('elements', []):
        if el['type'] == 'node':
            nodes[el['id']] = (el['lon'], el['lat'])

for fn in ['osm_north.json', 'osm_south.json']:
    p = f'{RAW}/osm/{fn}'
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8'))
    for el in d.get('elements', []):
        uid = (el['type'], el['id'])
        if uid in seen_el: continue
        seen_el.add(uid)
        tags = el.get('tags') or {}
        if not tags: continue
        pt = Point(el['lon'], el['lat']) if el['type'] == 'node' else (Point(el['center']['lon'], el['center']['lat']) if 'center' in el else None)
        line = None
        if el['type'] == 'way' and 'nodes' in el:
            pts = [nodes[nid] for nid in el['nodes'] if nid in nodes]
            if len(pts) >= 2: line = LineString(pts)

        if 'place' in tags and pt is not None and tags.get('name'):
            pl_map = {'city': 'Cidade Polo', 'town': 'Sede Municipal', 'village': 'Vila / Distrito', 'hamlet': 'Comunidade Rural', 'suburb': 'Bairro', 'neighbourhood': 'Bairro / Loteamento', 'locality': 'Localidade'}
            if tags['place'] in pl_map:
                localidades.append({'nome': tags['name'], 'tipo': pl_map[tags['place']], 'geometry': pt})
        if tags.get('bridge') == 'yes' and line is not None:
            pontes.append({'nome': tags.get('name') or 'Ponte / Viaduto', 'rodovia': tags.get('ref') or tags.get('highway', ''), 'geometry': line.centroid})
        hw = tags.get('highway')
        if hw and line is not None:
            if hw in ('trunk', 'primary', 'secondary', 'tertiary') or str(tags.get('ref', '')).upper().startswith(('SC-', 'BR-')):
                jur = 'Federal (DNIT)' if 'BR-' in str(tags.get('ref', '')).upper() else ('Estadual (SIE-SC)' if 'SC-' in str(tags.get('ref', '')).upper() else 'Rodovia / Acesso Regional')
                rodovias.append({'nome': tags.get('name') or tags.get('ref') or 'Rodovia', 'ref': tags.get('ref') or '', 'jurisdicao': jur, 'pavimento': tags.get('surface') or 'Não informado', 'geometry': line})
            elif hw in ('path', 'footway') or tags.get('sac_scale'):
                if tags.get('name') or tags.get('sac_scale'):
                    trilhas.append({'nome': tags.get('name') or 'Trilha / Caminho', 'superficie': tags.get('surface') or 'Natural', 'geometry': line})
            else:
                hier_map = {'residential': 'Via Local / Urbana', 'living_street': 'Via Local / Urbana', 'pedestrian': 'Via Local / Urbana', 'unclassified': 'Estrada Municipal / Vicinal', 'track': 'Estrada Rural / Agrícola'}
                viario.append({'nome': tags.get('name') or ('Estrada Vicinal' if hw in ('unclassified', 'track') else 'Logradouro'), 'hierarquia': hier_map.get(hw, 'Via Municipal'), 'pavimento': tags.get('surface') or 'Não informado', 'geometry': line})
        am = tags.get('amenity')
        if am in ('school', 'kindergarten', 'college', 'university') and pt is not None:
            escolas.append({'nome': tags.get('name') or 'Unidade Escolar', 'tipo': 'Ensino Superior' if am in ('college', 'university') else ('Creche / Infantil' if am == 'kindergarten' else 'Escola'), 'geometry': pt})
        elif am in ('townhall', 'police', 'fire_station', 'post_office', 'community_centre', 'library', 'bus_station') and pt is not None:
            am_map = {'townhall': 'Prefeitura / Administração', 'police': 'Segurança Pública', 'fire_station': 'Corpo de Bombeiros', 'post_office': 'Correios', 'community_centre': 'Centro Comunitário', 'library': 'Biblioteca', 'bus_station': 'Terminal Rodoviário'}
            equip.append({'nome': tags.get('name') or am_map[am], 'tipo': am_map[am], 'geometry': pt})
        if (tags.get('tourism') or tags.get('waterway') == 'waterfall' or tags.get('natural') in ('peak', 'cave_entrance', 'cliff', 'beach')) and pt is not None:
            cat = 'Cachoeira' if tags.get('waterway') == 'waterfall' else ('Praia / Balneário' if tags.get('natural') == 'beach' else ('Pico / Mirante' if tags.get('natural') in ('peak', 'cliff') else ('Gruta / Caverna' if tags.get('natural') == 'cave_entrance' else tags.get('tourism', 'Atrativo').replace('_', ' ').title())))
            turismo.append({'nome': tags.get('name') or cat, 'categoria': cat, 'geometry': pt})
        if tags.get('landuse') == 'industrial' and pt is not None:
            industria.append({'nome': tags.get('name') or 'Área Industrial / Empresarial', 'tipo': 'Industrial', 'geometry': pt})

for lid, rows, simp, prec in [
    ('amesc_localidades_osm', localidades, 0, 4),
    ('amesc_rodovias_osm', rodovias, 0.00008, 4),
    ('amesc_sistema_viario_osm', viario, 0.00014, 4),
    ('amesc_pontes_osm', pontes, 0, 4),
    ('amesc_escolas_osm', escolas, 0, 4),
    ('amesc_equipamentos_osm', equip, 0, 4),
    ('amesc_turismo_osm', turismo, 0, 4),
    ('amesc_trilhas_osm', trilhas, 0.0001, 4),
    ('amesc_areas_industriais_osm', industria, 0, 4),
]:
    if rows:
        saved[lid] = save_geojson(gpd.GeoDataFrame(rows, crs='EPSG:4326'), lid, simplify_tol=simp, prec=prec, clip=True)

# 9. Process IBGE SIDRA for all 15 municipalities
print('\n=== 9. IBGE SIDRA INDICADORES (15 MUNICÍPIOS) ===', flush=True)
sidra = json.load(open(f'{RAW}/ibge/amesc_sidra.json', encoding='utf-8'))
rigeo_links = json.load(open(f'{RAW}/rigeo_amesc/rigeo_links.json', encoding='utf-8')) if os.path.exists(f'{RAW}/rigeo_amesc/rigeo_links.json') else {}

by_mun = {cd7: {'cd_mun': cd7, 'nome': nm, 'slug': slug, **mun_meta.get(cd7, {})} for nm, slug, cd7 in AMESC_LIST}

for r in sidra.get('censo2022_pop', [])[1:]:
    cd = r.get('D1C')
    if cd not in by_mun: continue
    v = float(r['V']) if r['V'] not in ('-', '...', '') else 0
    if r['D2C'] == '93': by_mun[cd]['pop_2022'] = int(v)
    elif r['D2C'] == '6318': by_mun[cd]['area_ibge_km2'] = v
    elif r['D2C'] == '614': by_mun[cd]['densidade_2022'] = v

for r in sidra.get('censo2022_urb_rur', [])[1:]:
    cd = r.get('D1C')
    if cd not in by_mun: continue
    v = float(r['V']) if r['V'] not in ('-', '...', '') else 0
    if r['D2C'] == '93':
        if r['D4N'] == 'Urbana': by_mun[cd]['pop_urbana'] = int(v)
        elif r['D4N'] == 'Rural': by_mun[cd]['pop_rural'] = int(v)
    elif r['D2C'] == '1000093':
        if r['D4N'] == 'Urbana': by_mun[cd]['pop_urbana_pct'] = v
        elif r['D4N'] == 'Rural': by_mun[cd]['pop_rural_pct'] = v

for r in sidra.get('censo2022_domicilios', [])[1:]:
    cd = r.get('D1C')
    if cd not in by_mun: continue
    v = float(r['V']) if r['V'] not in ('-', '...', '') else 0
    if r['D2C'] == '381': by_mun[cd]['domicilios_2022'] = int(v)
    elif r['D2C'] == '5930': by_mun[cd]['media_moradores'] = v

for r in sidra.get('pib_5938', [])[1:]:
    cd = r.get('D1C')
    if cd not in by_mun: continue
    yr = r['D3N']
    v = float(r['V']) if r['V'] not in ('-', '...', '') else 0.0
    by_mun[cd].setdefault('pib_serie', {}).setdefault(yr, {})[r['D2N']] = v

# PAM top crops per municipality
pam_temp_map = {}
for key in ['pam_temp_1612', 'pam_perm_1613']:
    for r in sidra.get(key, [])[1:]:
        cd, prod, var, vs = r.get('D1C'), r.get('D4N'), r.get('D2C'), r.get('V')
        if cd not in by_mun or not prod or prod == 'Total' or vs in ('-', '...', '', 'X'): continue
        val = float(vs)
        pdict = pam_temp_map.setdefault(cd, {}).setdefault(prod, {'produto': prod, 'area_ha': 0, 'producao_t': 0, 'valor_mil_reais': 0})
        if var == '214': pdict['producao_t'] = val
        elif var == '215': pdict['valor_mil_reais'] = val
        elif var == '216': pdict['area_ha'] = val

# Count CNES by municipality
cnes_by_mun = {}
for feat in (saved.get('amesc_saude_cnes') or {}).get('features', []):
    cd = feat['properties'].get('cd_mun')
    if cd: cnes_by_mun[cd] = cnes_by_mun.get(cd, 0) + 1

for cd, info in by_mun.items():
    pib_yrs = sorted(info.get('pib_serie', {}).keys())
    ly = pib_yrs[-1] if pib_yrs else '2023'
    pib_mil = info.get('pib_serie', {}).get(ly, {}).get('Produto Interno Bruto a preços correntes', 0)
    pop = info.get('pop_2022', 1)
    info['pib_ano'] = ly
    info['pib_total_mil'] = pib_mil
    info['pib_per_capita'] = round((pib_mil * 1000) / pop, 2) if pop else 0
    crops = sorted(pam_temp_map.get(cd, {}).values(), key=lambda x: x['valor_mil_reais'], reverse=True)
    info['top_culturas'] = [c for c in crops if c['valor_mil_reais'] > 0][:5]
    info['uso_solo_fbds_ha'] = fbds_uso_by_mun.get(cd, {})
    info['cnes_ativos'] = cnes_by_mun.get(cd, 0)
    info['rigeo'] = rigeo_links.get(cd, {})

regional_totals = {
    'municipios': 15,
    'pop_2022': sum(m.get('pop_2022', 0) for m in by_mun.values()),
    'pop_urbana': sum(m.get('pop_urbana', 0) for m in by_mun.values()),
    'pop_rural': sum(m.get('pop_rural', 0) for m in by_mun.values()),
    'domicilios_2022': sum(m.get('domicilios_2022', 0) for m in by_mun.values()),
    'area_km2': round(sum(m.get('area_ibge_km2', m.get('area_km2', 0)) for m in by_mun.values()), 2),
    'pib_total_mil': round(sum(m.get('pib_total_mil', 0) for m in by_mun.values()), 1),
    'cnes_ativos': sum(m.get('cnes_ativos', 0) for m in by_mun.values()),
}
regional_totals['densidade_2022'] = round(regional_totals['pop_2022'] / regional_totals['area_km2'], 2) if regional_totals['area_km2'] else 0
regional_totals['pib_per_capita'] = round((regional_totals['pib_total_mil'] * 1000) / regional_totals['pop_2022'], 2) if regional_totals['pop_2022'] else 0

indicadores_amesc = {
    'regiao': 'AMESC — Associação dos Municípios do Extremo Sul Catarinense',
    'totais': regional_totals,
    'municipios': [by_mun[cd] for _, _, cd in AMESC_LIST],
}
json.dump(indicadores_amesc, open(f'{OUT}/amesc_indicadores.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# Write instant JS bootstrap modules (lightweight! ~500 KB total so page opens in < 1s)
with open(f'{JS_OUT}/limite-amesc.js', 'w', encoding='utf-8') as f:
    f.write('window.AMESC_LIMIT_GEOJSON = '); json.dump(saved['amesc_limite_regional'], f, ensure_ascii=False, separators=(',', ':')); f.write(';\n')
    f.write('window.AMESC_MUNICIPIOS_GEOJSON = '); json.dump(saved['amesc_municipios'], f, ensure_ascii=False, separators=(',', ':')); f.write(';\n')

with open(f'{JS_OUT}/indicadores-amesc.js', 'w', encoding='utf-8') as f:
    f.write('window.AMESC_INDICADORES = '); json.dump(indicadores_amesc, f, ensure_ascii=False, separators=(',', ':')); f.write(';\n')

# Light core bundle (municipalities, localidades, rodovias, saude, escolas, setores risco, turismo)
core_keys = ['amesc_municipios', 'amesc_limite_regional', 'amesc_localidades_osm', 'amesc_rodovias_osm', 'amesc_saude_cnes', 'amesc_escolas_osm', 'amesc_setores_risco_sgb', 'amesc_turismo_osm']
core_bundle = {k: saved[k] for k in core_keys if k in saved and saved[k] is not None}
with open(f'{JS_OUT}/amesc-bundle.js', 'w', encoding='utf-8') as f:
    f.write('window.GEOAMESC_BUNDLE = '); json.dump(core_bundle, f, ensure_ascii=False, separators=(',', ':')); f.write(';\n')

print(f'\nALL DONE! Saved {len(saved)} layers | Core bundle: {os.path.getsize(f"{JS_OUT}/amesc-bundle.js")/1024:.1f} KB', flush=True)
