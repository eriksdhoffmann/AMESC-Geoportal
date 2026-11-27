import os, json, warnings
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import geopandas as gpd
from shapely.ops import unary_union

warnings.filterwarnings('ignore')

ROOT = r'C:\Users\Win11\Downloads\AMESC-Geoportal'
mun_gdf = gpd.read_file(f'{ROOT}/data/amesc_municipios.geojson').to_crs('EPSG:4326')
amesc_outer = unary_union(mun_gdf.geometry.buffer(0))

p = f'{ROOT}/data_raw/wfs/incra_sigef.geojson'
if os.path.exists(p):
    g = gpd.read_file(p)
    g = g.to_crs('EPSG:4326')
    g = g[g.geometry.notnull() & ~g.geometry.is_empty].copy()
    g['geometry'] = g.geometry.buffer(0)
    g = gpd.clip(g, amesc_outer)
    g = g[g.geometry.notnull() & ~g.geometry.is_empty].copy()
    g['geometry'] = g.geometry.simplify(0.00012, preserve_topology=True)
    # Keep essential SIGEF fields
    keep_cands = ['parcela_co', 'codigo_imo', 'nome_area', 'situacao_i', 'status', 'art', 'municipio_', 'area_hecta']
    cols = [c for c in keep_cands if c in g.columns] + ['geometry']
    g = g[cols]
    out = f'{ROOT}/data/amesc_incra_sigef.geojson'
    gj = json.loads(g.to_json())
    def rc(obj):
        if isinstance(obj, float): return round(obj, 5)
        if isinstance(obj, list): return [rc(x) for x in obj]
        if isinstance(obj, dict): return {k: rc(v) for k, v in obj.items()}
        return obj
    gj['features'] = [{'type': 'Feature', 'properties': f['properties'], 'geometry': rc(f['geometry'])} for f in gj['features'] if f.get('geometry')]
    json.dump(gj, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'OK amesc_incra_sigef: {len(gj["features"])} feats | {os.path.getsize(out)/1024:.1f} KB')
