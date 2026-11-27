import re

ROOT = r'C:\Users\Win11\Downloads\AMESC-Geoportal'
SRC_JM = r'C:\Users\Win11\Downloads\Geopotal Jacinto Machado\js'

# 1. Adapt js/layer-engine.js
le = open(f'{SRC_JM}/layer-engine.js', encoding='utf-8').read()
le_repls = [
    ('Geoportal Municipal de Jacinto Machado', 'Geoportal Regional da AMESC'),
    ('Jacinto Machado (SC — IBGE 4208708)', 'AMESC — Extremo Sul Catarinense (15 Municípios)'),
    ('IBGE 4208708 (430,704 km²)', 'AMESC (15 Municípios)'),
    ('IBGE 4208708', 'AMESC 15 Municípios'),
    ('JACINTO_BOUNDS', 'AMESC_BOUNDS'),
    ('JACINTO_URBAN_CENTER', 'AMESC_CENTER'),
    ('Geoportal-Jacinto-Machado', 'AMESC-Geoportal'),
    ('GEOJACINTO_BUNDLE', 'GEOAMESC_BUNDLE'),
    ('JACINTO_LIMIT_GEOJSON', 'AMESC_LIMIT_GEOJSON'),
    ('jacinto-bundle-extra.js', 'amesc-bundle.js'),
    ('geoportal_jacinto_machado_', 'geoportal_amesc_'),
    ('de Jacinto Machado', 'da região AMESC'),
    ('em Jacinto Machado', 'na região AMESC'),
    ('Jacinto Machado', 'Região AMESC'),
]
for a, b in le_repls:
    le = le.replace(a, b)

# Enhance buildMunicipalMask to support 'ALL' (AMESC mosaic) OR a single selected municipality (divisasintermunicipais style)
old_mask = """    let municipalClipEnabled = true;
    let municipalMaskLayer = null;

    function buildMunicipalMask() {
      const gj = window.AMESC_LIMIT_GEOJSON;
      if (!gj?.features?.[0]?.geometry) return null;
      const geom = gj.features[0].geometry;"""

new_mask = """    let municipalClipEnabled = true;
    let selectedMunCode = 'ALL';
    let municipalMaskLayer = null;

    function buildMunicipalMask() {
      let geom = null;
      if (selectedMunCode !== 'ALL' && window.AMESC_MUNICIPIOS_GEOJSON?.features) {
        const feat = window.AMESC_MUNICIPIOS_GEOJSON.features.find((f) => String(f.properties?.CD_MUN) === String(selectedMunCode));
        if (feat?.geometry) geom = feat.geometry;
      }
      if (!geom) {
        const gj = window.AMESC_LIMIT_GEOJSON;
        if (!gj?.features?.[0]?.geometry) return null;
        geom = gj.features[0].geometry;
      }"""
le = le.replace(old_mask, new_mask)

# Expose setSelectedMunicipality & getSelectedMunicipality
old_set_clip = """    function setMunicipalClip(enabled) {
      municipalClipEnabled = Boolean(enabled);
      syncMunicipalMask();
      callbacks.onStateChange?.();
    }"""
new_set_clip = """    function setMunicipalClip(enabled) {
      municipalClipEnabled = Boolean(enabled);
      syncMunicipalMask();
      callbacks.onStateChange?.();
    }

    function setSelectedMunicipality(cdMun) {
      selectedMunCode = cdMun || 'ALL';
      syncMunicipalMask();
      callbacks.onStateChange?.();
    }

    function getSelectedMunicipality() {
      return selectedMunCode;
    }"""
le = le.replace(old_set_clip, new_set_clip)
le = le.replace('      isMunicipalClipEnabled,\n', '      isMunicipalClipEnabled,\n      setSelectedMunicipality,\n      getSelectedMunicipality,\n')

# Update Raio-X coreContextIds
le = re.sub(
    r"const coreContextIds = \[[^\]]+\];",
    "const coreContextIds = ['amesc_municipios', 'amesc_distritos_ibge', 'amesc_bairros_ibge', 'amesc_setores_ibge', 'amesc_setores_risco_sgb', 'amesc_bacias_ima', 'amesc_ucs_mma', 'amesc_geologia_ibge', 'amesc_pedologia_ibge'];",
    le
)
# Do not skip amesc_municipios in Raio-X so user sees which of the 15 municipalities they clicked!
le = le.replace("if (cfg.id === 'limite_municipal_ibge') continue;", "if (cfg.id === 'amesc_limite_regional') continue;")

open(f'{ROOT}/js/layer-engine.js', 'w', encoding='utf-8').write(le)
print('Wrote js/layer-engine.js', len(le))

# 2. Adapt js/tools.js
ts = open(f'{SRC_JM}/tools.js', encoding='utf-8').read()
ts_repls = [
    ('Geoportal Municipal de Jacinto Machado', 'Geoportal Regional da AMESC'),
    ('JACINTO_BOUNDS', 'AMESC_BOUNDS'),
    ('GEOJACINTO_BUNDLE', 'GEOAMESC_BUNDLE'),
    ('geoportal_jacinto_machado_desenhos.geojson', 'geoportal_amesc_desenhos.geojson'),
    ('sistema_viario_osm', 'amesc_sistema_viario_osm'),
    ('rodovias_jacinto', 'amesc_rodovias_osm'),
    ('Jacinto Machado/SC', 'AMESC/SC'),
    ('de Jacinto Machado', 'da região AMESC'),
    ('em Jacinto Machado', 'na região AMESC'),
    ('Jacinto Machado', 'Região AMESC'),
]
for a, b in ts_repls:
    ts = ts.replace(a, b)

s_idx = ts.find('// 2. Localidades')
e_idx = ts.find('// 6. Rodovias')
if s_idx != -1 and e_idx != -1:
    new_search = """// 2. 15 Municípios da AMESC
      for (const f of window.AMESC_MUNICIPIOS_GEOJSON?.features || []) {
        const nome = f.properties?.NM_MUN || '';
        if (norm(nome).includes(qNorm)) {
          results.push({
            type: 'Município (AMESC)',
            badge: 'Município',
            title: nome,
            subtitle: `IBGE ${f.properties?.CD_MUN || ''} • ${f.properties?.AREA_KM2 || '-'} km² (SC)`,
            geojson: f,
            activateLayer: 'amesc_municipios',
          });
        }
      }

      // 3. Sedes, Localidades & Comunidades (OSM)
      for (const f of bundle.amesc_localidades_osm?.features || []) {
        const nome = f.properties?.nome || '';
        if (norm(nome).includes(qNorm) && !results.some((r) => norm(r.title) === norm(nome))) {
          results.push({
            type: 'Localidade',
            badge: 'Local',
            title: nome,
            subtitle: `${f.properties?.tipo || 'Localidade'} — AMESC/SC`,
            geojson: f,
            activateLayer: 'amesc_localidades_osm',
          });
        }
      }

      // 4. Setores de Risco (SGB/CPRM), Saúde (CNES), Escolas, Equipamentos e Turismo
      const poiSources = [
        { key: 'amesc_setores_risco_sgb', type: 'Setor de Risco (SGB/CPRM)', badge: 'Risco', layer: 'amesc_setores_risco_sgb', sub: (p) => `${p.municipio || ''} • Risco ${p.grau_risco || 'Alto'}` },
        { key: 'amesc_saude_cnes', type: 'Unidade de Saúde (CNES)', badge: 'Saúde', layer: 'amesc_saude_cnes', sub: (p) => `${p.municipio || ''} • ${p.esfera || ''}` },
        { key: 'amesc_escolas_osm', type: 'Educação', badge: 'Escola', layer: 'amesc_escolas_osm', sub: (p) => `${p.tipo || 'Escola'} — AMESC/SC` },
        { key: 'amesc_turismo_osm', type: 'Turismo / Atrativo', badge: 'Turismo', layer: 'amesc_turismo_osm', sub: (p) => `${p.categoria || 'Atrativo'} — AMESC/SC` },
      ];
      for (const src of poiSources) {
        for (const f of bundle[src.key]?.features || []) {
          const p = f.properties || {};
          const hay = norm(`${p.nome || ''} ${p.local || ''} ${p.municipio || ''} ${p.endereco || ''} ${p.categoria || ''}`);
          if (hay.includes(qNorm)) {
            results.push({
              type: src.type,
              badge: src.badge,
              title: p.nome || p.local || src.type,
              subtitle: src.sub(p),
              geojson: f,
              activateLayer: src.layer,
            });
            if (results.length >= 18) break;
          }
        }
      }

      """
    ts = ts[:s_idx] + new_search + ts[e_idx:]

open(f'{ROOT}/js/tools.js', 'w', encoding='utf-8').write(ts)
print('Wrote js/tools.js', len(ts))

# 3. Adapt js/downloads-page.js
dl = open(f'{SRC_JM}/downloads-page.js', encoding='utf-8').read()
dl_repls = [
    ('Geoportal Municipal de Jacinto Machado', 'Geoportal Regional da AMESC'),
    ('GEOJACINTO_BUNDLE', 'GEOAMESC_BUNDLE'),
    ('geoportal_jacinto_machado_', 'geoportal_amesc_'),
    ('jacinto-bundle-extra.js', 'amesc-bundle.js'),
    ('Jacinto Machado', 'Região AMESC'),
]
for a, b in dl_repls:
    dl = dl.replace(a, b)

m_start = dl.find('const MUNICIPAL_DOCS = [')
m_end = dl.find('  ];\n\n  // Unify')
if m_start == -1: m_end = dl.find('  ];\n\n  // Monta')
if m_start != -1 and m_end != -1:
    docs_block = """const MUNICIPAL_DOCS = [
    {
      id: 'doc_amesc_ind_json',
      name: 'Indicadores Socioeconômicos dos 15 Municípios da AMESC (IBGE SIDRA)',
      category: 'Indicadores Regionais & SEPLAN',
      sourceClass: 'Oficial',
      whatIsThis: 'Arquivo JSON consolidado com Censo 2022, PIB Municipal, Lavouras PAM, Uso do Solo FBDS e links RIGeo SGB/CPRM para os 15 municípios.',
      format: 'JSON Oficial (IBGE SIDRA)',
      localFile: 'data/amesc_indicadores.json',
      orgao: 'IBGE / FBDS / SGB',
    },
    {
      id: 'doc_seplan_divisas',
      name: 'Portal Oficial de Divisas Intermunicipais de Santa Catarina (SEPLAN / DITER)',
      category: 'Indicadores Regionais & SEPLAN',
      sourceClass: 'Oficial',
      whatIsThis: 'Referência estadual oficial de limites e memoriais descritivos dos municípios catarinenses.',
      format: 'Portal Oficial SC (SEPLAN)',
      externalUrl: 'https://divisasintermunicipais.sc.gov.br/',
      orgao: 'SEPLAN / Governo de Santa Catarina',
    },
    {
      id: 'doc_sigsc_portal',
      name: 'SIGSC — Aerolevantamento Oficial de Santa Catarina (Ortofoto 39cm & MDT/MDS)',
      category: 'Indicadores Regionais & SEPLAN',
      sourceClass: 'Oficial',
      whatIsThis: 'Portal estadual de ortofotos e modelos digitais de terreno/superfície integrados via WMS no Geoportal AMESC.',
      format: 'Serviço WMS / Portal SIGSC',
      externalUrl: 'https://sigsc.sc.gov.br/',
      orgao: 'Governo de SC — SDS / SIGSC',
    },
"""
    dl = dl[:m_start] + docs_block + dl[m_end:]

open(f'{ROOT}/js/downloads-page.js', 'w', encoding='utf-8').write(dl)
print('Wrote js/downloads-page.js', len(dl))
