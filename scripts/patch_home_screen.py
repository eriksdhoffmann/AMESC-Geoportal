from pathlib import Path

p = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\js\app.js")
text = p.read_text(encoding="utf-8")

# 1. Update closeModal and openNavSection
old_block = """  function closeModal() {
    modalBackdrop?.classList.remove('open');
    setNavActive('map');
  }

  document.getElementById('modalClose')?.addEventListener('click', closeModal);
  modalBackdrop?.addEventListener('click', (e) => { if (e.target === modalBackdrop) closeModal(); });

  function openNavSection(navId) {
    setNavActive(navId);
    if (navId === 'map') {
      modalBackdrop?.classList.remove('open');
      return;
    }

    if (navId === 'home') {
      modalBackdrop?.classList.remove('open');
      setNavActive('map');
      tools.disableSwipe();
      engine.clearAllLayers();
      engine.setBasemapActive('satelite_global', true, true);
      selectMunicipality('ALL');
      renderLayerDrawer();
      return;
    }"""

new_block = """  const homeScreenEl = document.getElementById('homeScreen');

  function setHomeOpen(open) {
    if (!homeScreenEl) return;
    homeScreenEl.classList.toggle('open', open);
    if (open) {
      modalBackdrop?.classList.remove('open');
      homeScreenEl.scrollTop = 0;
      setNavActive('home');
    } else {
      setNavActive('map');
      setTimeout(() => map.invalidateSize(), 60);
    }
  }

  function closeModal() {
    modalBackdrop?.classList.remove('open');
    if (homeScreenEl?.classList.contains('open')) {
      setNavActive('home');
    } else {
      setNavActive('map');
    }
  }

  document.getElementById('modalClose')?.addEventListener('click', closeModal);
  modalBackdrop?.addEventListener('click', (e) => { if (e.target === modalBackdrop) closeModal(); });
  document.getElementById('logoHomeLink')?.addEventListener('click', (e) => {
    e.preventDefault();
    modalBackdrop?.classList.remove('open');
    setHomeOpen(false);
  });

  function openNavSection(navId) {
    document.getElementById('mainNav')?.classList.remove('mobile-open');
    if (navId === 'map') {
      modalBackdrop?.classList.remove('open');
      setHomeOpen(false);
      return;
    }

    if (navId === 'home') {
      setHomeOpen(true);
      return;
    }

    setNavActive(navId);"""

# Normalize CRLF for reliable matching
eol = "\r\n" if "\r\n" in text else "\n"
text_lf = text.replace("\r\n", "\n")

assert old_block in text_lf, "old_block not found!"
text_lf = text_lf.replace(old_block, new_block, 1)

# 2. Ensure applyPreset closes homeScreen
old_preset = """  function applyPreset(presetId) {
    const p = THEMATIC_PRESETS.find((x) => x.id === presetId);
    if (!p) return;
    closeModal();"""

new_preset = """  function applyPreset(presetId) {
    const p = THEMATIC_PRESETS.find((x) => x.id === presetId);
    if (!p) return;
    closeModal();
    setHomeOpen(false);"""

assert old_preset in text_lf, "old_preset not found!"
text_lf = text_lf.replace(old_preset, new_preset, 1)

# 3. Wire #homeScreen tiles, quick chips, and live search right before `renderLayerDrawer();` at the end
home_wiring = """
  // ==================== PÁGINA INICIAL (ESTILO GEOPORTAL FLORIANÓPOLIS) ====================
  function openMapWithCustomLayers(basemapId, layerIds, toastMsg) {
    closeModal();
    setHomeOpen(false);
    tools.disableSwipe();
    engine.clearAllLayers();
    if (basemapId) engine.setBasemapActive(basemapId, true, true);
    (layerIds || []).forEach((lid) => {
      const found = window.GeoCatalog.getLayerById(lid);
      if (found) expandedGroups.add(found.group.id);
      engine.enableLayer(lid);
    });
    setDrawerOpen(true);
    drawerTab = 'layers';
    renderLayerDrawer();
    if (toastMsg) showToast(toastMsg, 'success');
  }

  homeScreenEl?.querySelectorAll('[data-home-preset]').forEach((btn) => {
    btn.addEventListener('click', () => applyPreset(btn.dataset.homePreset));
  });

  homeScreenEl?.querySelectorAll('[data-home-action]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.homeAction;
      if (act === 'map_clean') {
        closeModal();
        setHomeOpen(false);
        tools.disableSwipe();
        engine.clearAllLayers();
        engine.setBasemapActive('satelite_global', true, true);
        selectMunicipality('ALL');
        setDrawerOpen(true);
        drawerTab = 'layers';
        renderLayerDrawer();
      } else if (act === 'municipios_tab') {
        closeModal();
        setHomeOpen(false);
        setDrawerOpen(true);
        drawerTab = 'municipios';
        renderLayerDrawer();
      } else if (act === 'socio') {
        openNavSection('socio');
      } else if (act === 'relevo_fisico') {
        openMapWithCustomLayers(
          'mdt_sigsc_2012',
          ['amesc_municipios', 'amesc_geologia_ibge', 'amesc_pedologia_ibge'],
          'Mapa Físico & Relevo (MDT SC 2012 + Geologia + Pedologia) carregado.'
        );
      } else if (act === 'licenciamento_ima') {
        openMapWithCustomLayers(
          'satelite_hibrido',
          ['amesc_municipios', 'amesc_licenciamento_ima', 'amesc_autos_ima', 'amesc_embargos_ima'],
          'Camadas de Licenciamento e Fiscalização (IMA-SC) carregadas.'
        );
      } else if (act === 'imoveis_sigef') {
        openMapWithCustomLayers(
          'satelite_global',
          ['amesc_municipios', 'amesc_incra_sigef'],
          'Imóveis Rurais Certificados (INCRA / SIGEF) carregados.'
        );
      }
    });
  });

  // Busca da Página Inicial (municípios, camadas, presets e bases)
  const homeSearchInput = document.getElementById('homeSearchInput');
  const homeSearchBtn = document.getElementById('homeSearchBtn');
  const homeSearchResults = document.getElementById('homeSearchResults');

  function normStr(s) {
    return String(s || '')
      .normalize('NFD')
      .replace(/[\\u0300-\\u036f]/g, '')
      .toLowerCase();
  }

  function buildHomeSearchMatches(rawQuery) {
    const q = normStr(rawQuery).trim();
    if (!q) return [];
    const results = [];

    // 1. Municípios (15)
    const muns = getAmsecMunicipiosList();
    muns.forEach((m) => {
      if (normStr(m.nome).includes(q) || String(m.cd_mun).includes(q)) {
        results.push({
          badge: 'Município',
          title: m.nome,
          sub: `IBGE ${m.cd_mun} • Focar e recortar no mapa`,
          run: () => {
            setHomeOpen(false);
            selectMunicipality(m.cd_mun);
          },
        });
      }
    });

    // 2. Mapas Temáticos (Presets)
    THEMATIC_PRESETS.forEach((p) => {
      if (normStr(`${p.title} ${p.desc}`).includes(q)) {
        results.push({
          badge: 'Mapa Temático',
          title: p.title,
          sub: p.desc,
          run: () => applyPreset(p.id),
        });
      }
    });

    // 3. Camadas Vetoriais (46)
    window.GeoCatalog.getAllLayers().forEach(({ layer, group }) => {
      const hay = normStr(`${layer.name} ${layer.description || ''} ${group.name} ${layer.source || ''}`);
      if (hay.includes(q)) {
        results.push({
          badge: 'Camada',
          title: layer.name,
          sub: `${group.name}${layer.source ? ' • ' + layer.source : ''}`,
          run: () => {
            setHomeOpen(false);
            window.GeoPortalMapNav.activateLayer(layer.id);
          },
        });
      }
    });

    // 4. Mapas Base (8)
    BASEMAPS.forEach((bm) => {
      if (normStr(`${bm.name} ${bm.description || ''}`).includes(q)) {
        results.push({
          badge: 'Mapa Base',
          title: bm.name,
          sub: bm.description || 'Mapa base oficial / satélite',
          run: () => {
            setHomeOpen(false);
            window.GeoPortalMapNav.activateBasemap(bm.id);
          },
        });
      }
    });

    return results.slice(0, 12);
  }

  function renderHomeSearch(openFirst = false) {
    if (!homeSearchInput || !homeSearchResults) return;
    const q = homeSearchInput.value.trim();
    if (!q) {
      homeSearchResults.innerHTML = '';
      homeSearchResults.classList.remove('open');
      return;
    }
    const items = buildHomeSearchMatches(q);
    if (openFirst && items.length === 1) {
      homeSearchResults.classList.remove('open');
      items[0].run();
      return;
    }
    if (!items.length) {
      homeSearchResults.innerHTML = `<div class="gp-search-empty">Nenhum dado encontrado para "${escapeHtml(q)}". Tente "risco", "saúde", "Araranguá", "FBDS", "SIGEF" ou "cânions".</div>`;
      homeSearchResults.classList.add('open');
      return;
    }
    homeSearchResults.innerHTML = items
      .map(
        (it, idx) => `
      <div class="gp-search-item" data-home-res-idx="${idx}">
        <span class="gp-search-badge">${escapeHtml(it.badge)}</span>
        <div style="min-width:0">
          <div class="gp-search-item-title">${escapeHtml(it.title)}</div>
          <div class="gp-search-item-sub">${escapeHtml(it.sub)}</div>
        </div>
      </div>`
      )
      .join('');
    homeSearchResults.classList.add('open');
    homeSearchResults.querySelectorAll('[data-home-res-idx]').forEach((el) => {
      el.addEventListener('click', () => {
        const item = items[Number(el.dataset.homeResIdx)];
        homeSearchResults.classList.remove('open');
        if (item) item.run();
      });
    });
  }

  homeSearchInput?.addEventListener('input', () => renderHomeSearch(false));
  homeSearchInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      renderHomeSearch(true);
    } else if (e.key === 'Escape') {
      homeSearchResults?.classList.remove('open');
    }
  });
  homeSearchBtn?.addEventListener('click', () => renderHomeSearch(true));

  homeScreenEl?.querySelectorAll('[data-home-chip]').forEach((chip) => {
    chip.addEventListener('click', () => {
      if (!homeSearchInput) return;
      homeSearchInput.value = chip.dataset.homeChip || '';
      homeSearchInput.focus();
      renderHomeSearch(false);
    });
  });

  document.addEventListener('click', (e) => {
    if (homeSearchResults?.classList.contains('open') && !e.target.closest('.gp-home-search-wrap')) {
      homeSearchResults.classList.remove('open');
    }
  });

  document.getElementById('headerMunSelect')?.addEventListener('change', () => {
    if (homeScreenEl?.classList.contains('open')) {
      setHomeOpen(false);
    }
  });

  renderLayerDrawer();
})();
"""

old_tail = "  renderLayerDrawer();\n})();"
assert old_tail in text_lf, "old_tail not found!"
text_lf = text_lf.replace(old_tail, home_wiring.lstrip("\n"), 1)

p.write_text(text_lf.replace("\n", eol), encoding="utf-8")
print("PATCHED js/app.js successfully! New size:", p.stat().st_size)
