p = r'C:\Users\Win11\Downloads\AMESC-Geoportal\js\layer-engine.js'
txt = open(p, encoding='utf-8').read()
use_crlf = '\r\n' in txt
norm = txt.replace('\r\n', '\n')

# 1. Raise paneMunicipalMask zIndex to 620 so white mask cleanly clips both basemaps AND straddling vector polygons/lines
old1 = "    map.createPane('paneMunicipalMask').style.zIndex = 230;"
new1 = "    map.createPane('paneMunicipalMask').style.zIndex = 620;"
assert old1 in norm, 'old1 not found'
norm = norm.replace(old1, new1, 1)

# 2. Re-render active vector layers when selected municipality changes
old2 = """    function setSelectedMunicipality(cdMun) {
      selectedMunCode = cdMun || 'ALL';
      if (municipalMaskLayer && map.hasLayer(municipalMaskLayer)) {
        map.removeLayer(municipalMaskLayer);
      }
      municipalMaskLayer = null;
      syncMunicipalMask();
      callbacks.onStateChange?.();
    }"""
new2 = """    function setSelectedMunicipality(cdMun) {
      selectedMunCode = cdMun || 'ALL';
      if (municipalMaskLayer && map.hasLayer(municipalMaskLayer)) {
        map.removeLayer(municipalMaskLayer);
      }
      municipalMaskLayer = null;
      syncMunicipalMask();
      for (const st of activeLayers.values()) {
        if (st.geojson) renderVectorState(st);
      }
      callbacks.onStateChange?.();
    }"""
assert old2 in norm, 'old2 not found'
norm = norm.replace(old2, new2, 1)

# 3. Filter active vector layers strictly to the selected municipality when selectedMunCode !== 'ALL'
old3 = """    function renderVectorState(state) {
      const { cfg, paneName } = state;
      const fullGj = state.geojson;
      clearStateMapObjects(state);

      if (cfg.minZoom && map.getZoom() < cfg.minZoom) {
        state.belowMinZoom = true;
        state.renderedCount = 0;
        syncLayerZIndexes();
        callbacks.onStateChange?.();
        return;
      }

      state.belowMinZoom = false;
      const displayGj = cfg.viewportFilter ? filterGeoJsonByBounds(fullGj, map.getBounds(), 3500) : fullGj;
      const gl = buildGeoJsonLayer(cfg, displayGj, state.opacity, paneName, fullGj);
      gl.addTo(map);

      let lg = null;
      if (cfg.labelField) {
        lg = buildLabelsGroup(cfg, displayGj);
        if (lg && map.getZoom() >= 12) lg.addTo(map);
      }

      state.leafletLayer = gl;
      state.labelGroup = lg;
      state.renderedCount = displayGj?.features?.length || 0;
      syncLayerZIndexes();"""

new3 = """    function normMunName(s) {
      return String(s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().trim();
    }

    function computeGeomBbox(geom) {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      const walk = (c) => {
        if (!Array.isArray(c)) return;
        if (typeof c[0] === 'number') {
          if (c[0] < minX) minX = c[0];
          if (c[0] > maxX) maxX = c[0];
          if (c[1] < minY) minY = c[1];
          if (c[1] > maxY) maxY = c[1];
        } else {
          for (let i = 0; i < c.length; i++) walk(c[i]);
        }
      };
      if (geom?.type === 'GeometryCollection') {
        for (const g of geom.geometries || []) {
          const b = computeGeomBbox(g);
          if (b[0] < minX) minX = b[0];
          if (b[1] < minY) minY = b[1];
          if (b[2] > maxX) maxX = b[2];
          if (b[3] > maxY) maxY = b[3];
        }
      } else if (geom?.coordinates) {
        walk(geom.coordinates);
      }
      return [minX, minY, maxX, maxY];
    }

    function featureIntersectsMun(geom, munGeom, munBbox) {
      if (!geom) return false;
      const fb = computeGeomBbox(geom);
      if (fb[2] < munBbox[0] || fb[0] > munBbox[2] || fb[3] < munBbox[1] || fb[1] > munBbox[3]) {
        return false;
      }
      if (geom.type === 'Point') {
        const [lon, lat] = geom.coordinates || [];
        return geomContainsLatLng(munGeom, { lat, lng: lon }, 0);
      }
      if (geom.type === 'MultiPoint') {
        return (geom.coordinates || []).some(([lon, lat]) => geomContainsLatLng(munGeom, { lat, lng: lon }, 0));
      }
      const samplePts = [];
      const collect = (c) => {
        if (!Array.isArray(c) || samplePts.length >= 24) return;
        if (typeof c[0] === 'number') {
          samplePts.push(c);
        } else if (c.length > 0) {
          const step = Math.max(1, Math.floor(c.length / 8));
          for (let i = 0; i < c.length && samplePts.length < 24; i += step) collect(c[i]);
        }
      };
      collect(geom.coordinates);
      if (samplePts.some(([lon, lat]) => geomContainsLatLng(munGeom, { lat, lng: lon }, 0))) return true;
      if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
        const cx = (munBbox[0] + munBbox[2]) / 2;
        const cy = (munBbox[1] + munBbox[3]) / 2;
        if (geomContainsLatLng(geom, { lat: cy, lng: cx }, 0)) return true;
      }
      return false;
    }

    function filterGeoJsonBySelectedMunicipality(geojson) {
      if (selectedMunCode === 'ALL' || !geojson?.features?.length) return geojson;
      const selFeat = window.AMESC_MUNICIPIOS_GEOJSON?.features?.find(
        (f) => String(f.properties?.CD_MUN) === String(selectedMunCode)
      );
      if (!selFeat?.geometry) return geojson;
      const selCode = String(selectedMunCode);
      const selName = normMunName(selFeat.properties?.NM_MUN);
      const munBbox = computeGeomBbox(selFeat.geometry);

      const out = [];
      for (const f of geojson.features) {
        const p = f.properties || {};
        const pCode = p.CD_MUN ?? p.cd_mun;
        if (pCode !== undefined && pCode !== null && String(pCode).trim() !== '') {
          if (String(pCode).trim() === selCode) out.push(f);
          continue;
        }
        const pName = p.NM_MUN ?? p.nm_mun ?? p.MUNICIPIO ?? p.municipio;
        if (pName !== undefined && pName !== null && String(pName).trim() !== '') {
          if (normMunName(pName) === selName) out.push(f);
          continue;
        }
        if (featureIntersectsMun(f.geometry, selFeat.geometry, munBbox)) {
          out.push(f);
        }
      }
      return { type: 'FeatureCollection', features: out };
    }

    function renderVectorState(state) {
      const { cfg, paneName } = state;
      const fullGj = state.geojson;
      clearStateMapObjects(state);

      if (cfg.minZoom && map.getZoom() < cfg.minZoom) {
        state.belowMinZoom = true;
        state.renderedCount = 0;
        syncLayerZIndexes();
        callbacks.onStateChange?.();
        return;
      }

      state.belowMinZoom = false;
      const scopedGj = filterGeoJsonBySelectedMunicipality(fullGj);
      const displayGj = cfg.viewportFilter ? filterGeoJsonByBounds(scopedGj, map.getBounds(), 3500) : scopedGj;
      const gl = buildGeoJsonLayer(cfg, displayGj, state.opacity, paneName, scopedGj);
      gl.addTo(map);

      let lg = null;
      if (cfg.labelField) {
        lg = buildLabelsGroup(cfg, displayGj);
        if (lg && map.getZoom() >= 12) lg.addTo(map);
      }

      state.leafletLayer = gl;
      state.labelGroup = lg;
      state.count = scopedGj?.features?.length || 0;
      state.renderedCount = displayGj?.features?.length || 0;
      syncLayerZIndexes();"""

assert old3 in norm, 'old3 not found'
norm = norm.replace(old3, new3, 1)

out = norm.replace('\n', '\r\n') if use_crlf else norm
open(p, 'w', encoding='utf-8').write(out)
print('Patched js/layer-engine.js successfully!')
