# 1. Update js/layer-engine.js to support multi-municipality selection (Set of codes)
p_le = r'C:\Users\Win11\Downloads\AMESC-Geoportal\js\layer-engine.js'
le = open(p_le, encoding='utf-8').read()
crlf_le = '\r\n' in le
le = le.replace('\r\n', '\n')

old_mask_block = """    let municipalClipEnabled = true;
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
      }
      const worldRing = [
        [-85, -180],
        [-85, 180],
        [85, 180],
        [85, -180],
        [-85, -180],
      ];
      const holes = [];
      const polys = geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates];
      for (const poly of polys) {
        if (poly[0]) {
          holes.push(poly[0].map(([lon, lat]) => [lat, lon]));
        }
      }"""

new_mask_block = """    let municipalClipEnabled = true;
    let selectedMunCodes = new Set(); // empty = ALL 15 municipalities
    let municipalMaskLayer = null;

    function buildMunicipalMask() {
      const geoms = [];
      if (selectedMunCodes.size > 0 && window.AMESC_MUNICIPIOS_GEOJSON?.features) {
        for (const feat of window.AMESC_MUNICIPIOS_GEOJSON.features) {
          if (selectedMunCodes.has(String(feat.properties?.CD_MUN)) && feat.geometry) {
            geoms.push(feat.geometry);
          }
        }
      }
      if (!geoms.length) {
        const gj = window.AMESC_LIMIT_GEOJSON;
        if (!gj?.features?.[0]?.geometry) return null;
        geoms.push(gj.features[0].geometry);
      }
      const worldRing = [
        [-85, -180],
        [-85, 180],
        [85, 180],
        [85, -180],
        [-85, -180],
      ];
      const holes = [];
      for (const geom of geoms) {
        const polys = geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates];
        for (const poly of polys) {
          if (poly[0]) {
            holes.push(poly[0].map(([lon, lat]) => [lat, lon]));
          }
        }
      }"""

assert old_mask_block in le, 'old_mask_block not found'
le = le.replace(old_mask_block, new_mask_block, 1)

old_set_mun = """    function setSelectedMunicipality(cdMun) {
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
    }

    function getSelectedMunicipality() {
      return selectedMunCode;
    }"""

new_set_mun = """    function setSelectedMunicipality(cdMunOrList) {
      selectedMunCodes.clear();
      if (Array.isArray(cdMunOrList)) {
        for (const c of cdMunOrList) {
          if (c && c !== 'ALL') selectedMunCodes.add(String(c));
        }
      } else if (cdMunOrList && cdMunOrList !== 'ALL') {
        selectedMunCodes.add(String(cdMunOrList));
      }
      if (municipalMaskLayer && map.hasLayer(municipalMaskLayer)) {
        map.removeLayer(municipalMaskLayer);
      }
      municipalMaskLayer = null;
      syncMunicipalMask();
      for (const st of activeLayers.values()) {
        if (st.geojson) renderVectorState(st);
      }
      callbacks.onStateChange?.();
    }

    function toggleSelectedMunicipality(cdMun) {
      const code = String(cdMun || '');
      if (!code || code === 'ALL') {
        setSelectedMunicipality('ALL');
        return [];
      }
      if (selectedMunCodes.has(code)) selectedMunCodes.delete(code);
      else selectedMunCodes.add(code);
      setSelectedMunicipality([...selectedMunCodes]);
      return [...selectedMunCodes];
    }

    function getSelectedMunicipality() {
      return selectedMunCodes.size === 0 ? 'ALL' : (selectedMunCodes.size === 1 ? [...selectedMunCodes][0] : [...selectedMunCodes]);
    }

    function getSelectedMunicipalities() {
      return [...selectedMunCodes];
    }"""

assert old_set_mun in le, 'old_set_mun not found'
le = le.replace(old_set_mun, new_set_mun, 1)
le = le.replace(
    '      setSelectedMunicipality,\n      getSelectedMunicipality,\n',
    '      setSelectedMunicipality,\n      toggleSelectedMunicipality,\n      getSelectedMunicipality,\n      getSelectedMunicipalities,\n'
)

old_filter = """    function filterGeoJsonBySelectedMunicipality(geojson) {
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
    }"""

new_filter = """    function filterGeoJsonBySelectedMunicipality(geojson) {
      if (selectedMunCodes.size === 0 || !geojson?.features?.length) return geojson;
      const selFeats = (window.AMESC_MUNICIPIOS_GEOJSON?.features || []).filter(
        (f) => selectedMunCodes.has(String(f.properties?.CD_MUN)) && f.geometry
      );
      if (!selFeats.length) return geojson;
      const selNames = new Set(selFeats.map((f) => normMunName(f.properties?.NM_MUN)));
      const selBoxes = selFeats.map((f) => ({ geom: f.geometry, bbox: computeGeomBbox(f.geometry) }));

      const out = [];
      for (const f of geojson.features) {
        const p = f.properties || {};
        const pCode = p.CD_MUN ?? p.cd_mun;
        if (pCode !== undefined && pCode !== null && String(pCode).trim() !== '') {
          if (selectedMunCodes.has(String(pCode).trim())) out.push(f);
          continue;
        }
        const pName = p.NM_MUN ?? p.nm_mun ?? p.MUNICIPIO ?? p.municipio;
        if (pName !== undefined && pName !== null && String(pName).trim() !== '') {
          if (selNames.has(normMunName(pName))) out.push(f);
          continue;
        }
        if (selBoxes.some((sb) => featureIntersectsMun(f.geometry, sb.geom, sb.bbox))) {
          out.push(f);
        }
      }
      return { type: 'FeatureCollection', features: out };
    }"""

assert old_filter in le, 'old_filter not found'
le = le.replace(old_filter, new_filter, 1)

open(p_le, 'w', encoding='utf-8').write(le.replace('\n', '\r\n') if crlf_le else le)
print('Updated js/layer-engine.js for multi-municipality selection!')

# 2. Update js/app.js: "Selecionar" additive toggle in Municípios (15) tab
p_app = r'C:\Users\Win11\Downloads\AMESC-Geoportal\js\app.js'
app = open(p_app, encoding='utf-8').read()
crlf_app = '\r\n' in app
app = app.replace('\r\n', '\n')

old_app_sel = """  function selectMunicipality(cdMun, { zoom = true } = {}) {
    const code = cdMun || 'ALL';
    engine.setSelectedMunicipality(code);

    const headerSel = document.getElementById('headerMunSelect');
    if (headerSel && headerSel.value !== code) headerSel.value = code;

    const scopeEl = document.getElementById('headerActiveScope');
    if (code === 'ALL') {
      if (scopeEl) scopeEl.textContent = 'Mosaico Integrado • 15 Municípios';
      if (zoom) {
        map.fitBounds(AMESC_BOUNDS, { paddingTopLeft: [56, 22], paddingBottomRight: [window.innerWidth <= 760 ? 32 : 390, 40] });
      }
      showToast('Exibindo o Mosaico Integrado dos 15 municípios da AMESC.', 'info');
    } else {
      const m = getAmsecMunicipiosList().find((x) => String(x.cd_mun) === String(code));
      if (m) {
        if (scopeEl) scopeEl.textContent = `${m.nome} • IBGE ${m.cd_mun}`;
        if (zoom && m.bounds) {
          map.fitBounds(m.bounds, { paddingTopLeft: [60, 30], paddingBottomRight: [window.innerWidth <= 760 ? 32 : 400, 46] });
        }
        showToast(`Município selecionado: ${m.nome} (IBGE ${m.cd_mun})`, 'success');
      }
    }
    renderLayerDrawer();
  }"""

new_app_sel = """  function fitSelectedMunicipalities(codes) {
    if (!codes.length) {
      map.fitBounds(AMESC_BOUNDS, { paddingTopLeft: [56, 22], paddingBottomRight: [window.innerWidth <= 760 ? 32 : 390, 40] });
      return;
    }
    const list = getAmsecMunicipiosList().filter((m) => codes.includes(String(m.cd_mun)) && m.bounds);
    if (!list.length) return;
    let minLat = 90, minLon = 180, maxLat = -90, maxLon = -180;
    for (const m of list) {
      minLat = Math.min(minLat, m.bounds[0][0]);
      minLon = Math.min(minLon, m.bounds[0][1]);
      maxLat = Math.max(maxLat, m.bounds[1][0]);
      maxLon = Math.max(maxLon, m.bounds[1][1]);
    }
    map.fitBounds([[minLat, minLon], [maxLat, maxLon]], {
      paddingTopLeft: [60, 30],
      paddingBottomRight: [window.innerWidth <= 760 ? 32 : 400, 46],
    });
  }

  function selectMunicipality(cdMun, { zoom = true, toggle = false } = {}) {
    let codes = [];
    if (toggle && cdMun && cdMun !== 'ALL') {
      codes = engine.toggleSelectedMunicipality(cdMun);
    } else {
      engine.setSelectedMunicipality(cdMun || 'ALL');
      codes = engine.getSelectedMunicipalities();
    }

    const headerSel = document.getElementById('headerMunSelect');
    if (headerSel) {
      headerSel.value = codes.length === 1 ? codes[0] : 'ALL';
    }

    if (zoom) fitSelectedMunicipalities(codes);

    if (codes.length === 0) {
      showToast('Exibindo todos os 15 municípios da AMESC.', 'info');
    } else if (codes.length === 1) {
      const m = getAmsecMunicipiosList().find((x) => String(x.cd_mun) === codes[0]);
      if (m) showToast(`Selecionado: ${m.nome} (IBGE ${m.cd_mun})`, 'success');
    } else {
      const names = getAmsecMunicipiosList().filter((x) => codes.includes(String(x.cd_mun))).map((x) => x.nome);
      showToast(`${codes.length} municípios selecionados: ${names.join(', ')}`, 'success');
    }
    renderLayerDrawer();
  }"""

assert old_app_sel in app, 'old_app_sel not found'
app = app.replace(old_app_sel, new_app_sel, 1)

old_tab_muns = """  function renderMunicipiosTab(container) {
    const cur = engine.getSelectedMunicipality();
    const list = getAmsecMunicipiosList();
    const q = searchFilterText.trim().toLowerCase();
    const filtered = q ? list.filter((m) => m.nome.toLowerCase().includes(q) || m.cd_mun.includes(q)) : list;
    const fmtN = (n, d = 0) => Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });

    const cards = filtered
      .map((m) => {
        const isSel = String(cur) === String(m.cd_mun);
        const rigeoPdf = m.rigeo?.pdf_url;
        return `
          <div class="gp-mun-card ${isSel ? 'active' : ''}" data-pick-mun="${m.cd_mun}">
            <div class="gp-mun-card-top">
              <span class="gp-mun-card-name">${escapeHtml(m.nome)}</span>
              <span class="gp-mun-card-code">IBGE ${m.cd_mun}</span>
            </div>
            <div class="gp-mun-card-stats">
              <span><b>Pop.:</b> ${fmtN(m.pop_2022)}</span>
              <span><b>Área:</b> ${fmtN(m.area_ibge_km2 || m.area_km2, 1)} km²</span>
              <span><b>CNES:</b> ${m.cnes_ativos || 0}</span>
            </div>
            <div class="gp-mun-card-actions">
              <button class="gp-opt-btn" data-pick-mun="${m.cd_mun}">${isSel ? '✓ Selecionado' : 'Focar & Recortar'}</button>
              ${rigeoPdf ? `<a class="gp-opt-btn" href="${escapeHtml(rigeoPdf)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Carta SGB ↗</a>` : ''}
            </div>
          </div>`;
      })
      .join('');

    container.innerHTML = `
      <div class="gp-mun-list">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:4px">
          <span style="font-size:11.5px;font-weight:700;color:#475569">Clique em um município para focar e recortar:</span>
          ${cur !== 'ALL' ? `<button class="gp-opt-btn" id="btnResetAmsecMosaic" style="background:#033c8e;color:#fff;border-color:#033c8e">Ver Todos (15)</button>` : ''}
        </div>
        ${cards}
      </div>
    `;
    container.querySelector('#btnResetAmsecMosaic')?.addEventListener('click', () => selectMunicipality('ALL'));
    container.querySelectorAll('[data-pick-mun]').forEach((el) => {
      el.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        selectMunicipality(el.dataset.pickMun);
      });
    });
  }"""

new_tab_muns = """  function renderMunicipiosTab(container) {
    const selList = engine.getSelectedMunicipalities();
    const list = getAmsecMunicipiosList();
    const q = searchFilterText.trim().toLowerCase();
    const filtered = q ? list.filter((m) => m.nome.toLowerCase().includes(q) || m.cd_mun.includes(q)) : list;
    const fmtN = (n, d = 0) => Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });

    const cards = filtered
      .map((m) => {
        const isSel = selList.includes(String(m.cd_mun));
        const rigeoPdf = m.rigeo?.pdf_url;
        return `
          <div class="gp-mun-card ${isSel ? 'active' : ''}" data-pick-mun="${m.cd_mun}">
            <div class="gp-mun-card-top">
              <span class="gp-mun-card-name">${escapeHtml(m.nome)}</span>
              <span class="gp-mun-card-code">IBGE ${m.cd_mun}</span>
            </div>
            <div class="gp-mun-card-stats">
              <span><b>Pop.:</b> ${fmtN(m.pop_2022)}</span>
              <span><b>Área:</b> ${fmtN(m.area_ibge_km2 || m.area_km2, 1)} km²</span>
              <span><b>CNES:</b> ${m.cnes_ativos || 0}</span>
            </div>
            <div class="gp-mun-card-actions">
              <button class="gp-opt-btn" data-pick-mun="${m.cd_mun}" style="${isSel ? 'background:#033c8e;color:#fff;border-color:#033c8e' : ''}">${isSel ? '✓ Selecionado' : 'Selecionar'}</button>
              ${rigeoPdf ? `<a class="gp-opt-btn" href="${escapeHtml(rigeoPdf)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Carta SGB ↗</a>` : ''}
            </div>
          </div>`;
      })
      .join('');

    container.innerHTML = `
      <div class="gp-mun-list">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:4px">
          <span style="font-size:11.5px;font-weight:700;color:#475569">${selList.length ? `${selList.length} selecionado(s) — clique para somar/remover:` : 'Clique em Selecionar para somar municípios:'}</span>
          ${selList.length ? `<button class="gp-opt-btn" id="btnResetAmsecMosaic" style="background:#033c8e;color:#fff;border-color:#033c8e">Ver Todos (15)</button>` : ''}
        </div>
        ${cards}
      </div>
    `;
    container.querySelector('#btnResetAmsecMosaic')?.addEventListener('click', () => selectMunicipality('ALL'));
    container.querySelectorAll('[data-pick-mun]').forEach((el) => {
      el.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        selectMunicipality(el.dataset.pickMun, { toggle: true });
      });
    });
  }"""

assert old_tab_muns in app, 'old_tab_muns not found'
app = app.replace(old_tab_muns, new_tab_muns, 1)

open(p_app, 'w', encoding='utf-8').write(app.replace('\n', '\r\n') if crlf_app else app)
print('Updated js/app.js for multi-municipality Selecionar!')
