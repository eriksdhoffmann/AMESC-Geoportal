/**
 * Geoportal Regional da AMESC — Página de Downloads (Padrão Institucional Geoportal Florianópolis)
 */
(() => {
  const { BASEMAPS, LAYER_GROUPS } = window.GeoCatalog;
  const Meta = window.GeoMetadata;

  const esc = (s) =>
    String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

  const norm = (s) =>
    String(s || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();

  // Rótulos curtos e institucionais por grupo (sem numeração artificial nem excesso de símbolos)
  const GROUP_PREFIX = {
    territorio_cadastro: 'Cadastro e Limites',
    meio_ambiente: 'Meio Ambiente',
    licenciamento_ima: 'Licenciamento Ambiental',
    hidrografia: 'Hidrografia',
    defesa_civil: 'Defesa Civil',
    geografia_fisica: 'Geologia e Relevo',
    infraestrutura_viario: 'Infraestrutura e Serviços',
    turismo_patrimonio: 'Patrimônio e Turismo',
    camadas_personalizadas: 'Estudos Técnicos',
    __basemaps__: 'Ortoimagens e Mapas Base',
    __docs__: 'Indicadores e Referências',
  };

  const SECTIONS = [
    {
      id: 'ALL_SIG',
      navLabel: 'Camadas em SIG do mapa',
      title: 'Camadas em SIG do mapa',
      subtitle: 'Acesse os arquivos vetoriais publicados no mapa interativo do GeoPortal',
    },
    {
      id: 'territorio_cadastro',
      navLabel: 'Cadastro e Limites Territoriais',
      title: 'Cadastro e Limites Territoriais',
      subtitle: 'Malhas municipais, distritos, bairros, setores censitários e parcelas certificadas',
    },
    {
      id: 'meio_ambiente',
      navLabel: 'Meio Ambiente e Uso do Solo',
      title: 'Meio Ambiente e Uso do Solo',
      subtitle: 'Cobertura da terra, áreas de preservação permanente, vegetação e unidades de conservação',
    },
    {
      id: 'licenciamento_ima',
      navLabel: 'Licenciamento Ambiental',
      title: 'Licenciamento e Fiscalização Ambiental',
      subtitle: 'Registros oficiais de licenciamento, autos de infração e áreas embargadas (IMA-SC)',
    },
    {
      id: 'hidrografia',
      navLabel: 'Hidrografia e Recursos Hídricos',
      title: 'Hidrografia e Recursos Hídricos',
      subtitle: 'Cursos d’água, nascentes, lagoas costeiras, bacias hidrográficas e poços tubulares',
    },
    {
      id: 'defesa_civil',
      navLabel: 'Defesa Civil e Áreas de Risco',
      title: 'Defesa Civil e Áreas de Risco',
      subtitle: 'Setores de risco geológico e cartas de suscetibilidade a inundações e movimentos de massa',
    },
    {
      id: 'geografia_fisica',
      navLabel: 'Geologia, Solos e Relevo',
      title: 'Geologia, Geomorfologia, Solos e Relevo',
      subtitle: 'Mapeamentos físicos oficiais do IBGE (BDIA), classes de declividade e hidrogeologia',
    },
    {
      id: 'infraestrutura_viario',
      navLabel: 'Infraestrutura, Saúde e Educação',
      title: 'Infraestrutura, Sistema Viário, Saúde e Educação',
      subtitle: 'Rodovias, rede viária, pontes, unidades de saúde (CNES), escolas e energia elétrica',
    },
    {
      id: 'turismo_patrimonio',
      navLabel: 'Patrimônio e Turismo',
      title: 'Patrimônio Arqueológico e Geoturismo',
      subtitle: 'Sítios cadastrados no IPHAN, trilhas, mirantes e atrativos dos cânions e litoral',
    },
    {
      id: '__basemaps__',
      navLabel: 'Ortoimagens e Mapas Base',
      title: 'Ortoimagens e Modelos Digitais de Terreno',
      subtitle: 'Serviços WMS oficiais do Estado de Santa Catarina (SIGSC) e bases cartográficas de referência',
    },
    {
      id: '__docs__',
      navLabel: 'Indicadores e Documentos Técnicos',
      title: 'Indicadores Socioeconômicos e Bases Estaduais',
      subtitle: 'Séries consolidadas dos 15 municípios da AMESC e portais técnicos oficiais',
    },
  ];

  // Limpa travessões longos e contagens brutas para manter padrão institucional limpo
  function cleanDisplayName(raw) {
    return String(raw || '')
      .replace(/\s*—\s*/g, ' - ')
      .replace(/\(\s*([^)]*?)\s*-\s*\d[\d.]*\s*\)/g, '($1)')
      .trim();
  }

  const MUNICIPAL_DOCS = [
    {
      id: 'doc_amesc_ind_json',
      name: 'Indicadores Socioeconômicos Consolidados dos 15 Municípios (Censo 2022, PIB, PAM e CNES)',
      category: 'Indicadores e Referências',
      sourceClass: 'Oficial',
      whatIsThis: 'Base consolidada com Censo 2022, PIB Municipal, Produção Agrícola Municipal e unidades ativas do CNES para os 15 municípios da AMESC.',
      format: 'JSON (UTF-8)',
      localFile: 'data/amesc_indicadores.json',
      downloadLabel: 'JSON',
      orgao: 'IBGE / DataSUS / AMESC',
    },
    {
      id: 'doc_seplan_divisas',
      name: 'Divisas Intermunicipais Oficiais do Estado de Santa Catarina (SEPLAN / DITER)',
      category: 'Indicadores e Referências',
      sourceClass: 'Oficial',
      whatIsThis: 'Portal estadual oficial de divisas e memoriais descritivos dos municípios catarinenses.',
      format: 'Portal Institucional',
      externalUrl: 'https://divisasintermunicipais.sc.gov.br/',
      downloadLabel: 'ACESSAR',
      orgao: 'SEPLAN / Governo de Santa Catarina',
    },
    {
      id: 'doc_sigsc_portal',
      name: 'Sistema de Informações Geográficas de Santa Catarina - Ortofotos e MDT (SIGSC)',
      category: 'Indicadores e Referências',
      sourceClass: 'Oficial',
      whatIsThis: 'Acervo aerofotogramétrico oficial de Santa Catarina (ortofotomosaicos de 39 cm, MDT e MDS).',
      format: 'Serviço WMS / Acervo Estadual',
      externalUrl: 'https://sigsc.sc.gov.br/',
      downloadLabel: 'ACESSAR',
      orgao: 'Governo do Estado de Santa Catarina',
    },
  ];

  const ALL_ITEMS = [];

  for (const g of LAYER_GROUPS) {
    if (g.id === 'camadas_personalizadas' && (!g.layers || !g.layers.length)) continue;
    const prefix = GROUP_PREFIX[g.id] || g.name;
    for (const l of g.layers) {
      const m = Meta.getEntry(l.id, { ...l, groupName: g.name });
      const cleanName = cleanDisplayName(l.name);
      ALL_ITEMS.push({
        kind: 'layer',
        id: l.id,
        groupId: g.id,
        prefix,
        displayLine: `- ${prefix} - ${cleanName}`,
        cleanName,
        cfg: l,
        metaEntry: m,
        redistributable: m.redistributable !== false && Boolean(l.localFile) && l.type !== 'wms',
        searchHaystack: norm(`${prefix} ${cleanName} ${l.name} ${g.name} ${m.whatIsThis} ${m.metadata.orgao_responsavel}`),
      });
    }
  }

  for (const bm of BASEMAPS) {
    const m = Meta.getEntry(bm.id, { ...bm, groupName: 'Ortoimagens e Mapas Base' });
    const cleanName = cleanDisplayName(bm.name);
    ALL_ITEMS.push({
      kind: 'basemap',
      id: bm.id,
      groupId: '__basemaps__',
      prefix: GROUP_PREFIX.__basemaps__,
      displayLine: `- Ortoimagens e Mapas Base - ${cleanName}`,
      cleanName,
      cfg: bm,
      metaEntry: m,
      redistributable: false,
      searchHaystack: norm(`ortoimagens mapas base ${cleanName} ${bm.category || ''} ${m.metadata.orgao_responsavel}`),
    });
  }

  for (const d of MUNICIPAL_DOCS) {
    ALL_ITEMS.push({
      kind: 'doc',
      id: d.id,
      groupId: '__docs__',
      prefix: GROUP_PREFIX.__docs__,
      displayLine: `- Indicadores e Referências - ${d.name}`,
      cleanName: d.name,
      cfg: d,
      metaEntry: Meta.makeMeta({
        sourceClass: d.sourceClass,
        whatIsThis: d.whatIsThis,
        nome_camada: d.name,
        categoria: d.category,
        orgao_responsavel: d.orgao,
        instituicao_fornecedora: d.orgao,
        url_fonte_original: d.externalUrl || 'data/amesc_indicadores.json',
        url_download_ou_servico: d.externalUrl || d.localFile,
        formato: d.format,
        tipo_geometria: 'Tabela / Base Alfanumérica',
        status_validacao: 'PUBLICADO',
      }),
      redistributable: Boolean(d.localFile),
      searchHaystack: norm(`indicadores referencias ${d.name} ${d.whatIsThis} ${d.orgao}`),
    });
  }

  let selectedSectionId = 'ALL_SIG';
  let queryText = '';

  const searchInput = document.getElementById('dlSearchInput');
  const clearBtn = document.getElementById('dlSearchClear');
  const urlQ = new URLSearchParams(window.location.search).get('q');
  if (urlQ && searchInput) {
    queryText = urlQ;
    searchInput.value = urlQ;
  }

  function getFilteredItems() {
    const q = norm(queryText.trim());
    return ALL_ITEMS.filter((it) => {
      // Se há busca digitada na aba geral, pesquisa em todo o catálogo
      if (selectedSectionId === 'ALL_SIG') {
        if (!q && it.kind !== 'layer') return false;
      } else if (it.groupId !== selectedSectionId) {
        return false;
      }
      if (q && !it.searchHaystack.includes(q)) return false;
      return true;
    });
  }

  function renderSidebar() {
    const navEl = document.getElementById('dlCategoryList');
    if (!navEl) return;
    navEl.innerHTML = SECTIONS.map(
      (s) => `
      <button type="button" class="dl-nav-item ${selectedSectionId === s.id ? 'active' : ''}" data-sec-id="${esc(s.id)}">
        ${esc(s.navLabel)}
      </button>`
    ).join('');
  }

  function renderHeader() {
    const sec = SECTIONS.find((s) => s.id === selectedSectionId) || SECTIONS[0];
    const titleEl = document.getElementById('dlSectionTitle');
    const subEl = document.getElementById('dlSectionSubtitle');
    if (titleEl) titleEl.textContent = sec.title;
    if (subEl) subEl.textContent = sec.subtitle;
  }

  function renderResults() {
    const items = getFilteredItems();
    const box = document.getElementById('dlResults');
    const summary = document.getElementById('dlResultSummary');
    if (clearBtn) clearBtn.classList.toggle('visible', Boolean(queryText.trim()));
    if (summary) summary.textContent = `${items.length} ${items.length === 1 ? 'camada' : 'camadas'}`;
    if (!box) return;

    if (!items.length) {
      box.innerHTML = `<div class="dl-empty">Nenhuma camada encontrada para o filtro informado.</div>`;
      return;
    }

    box.innerHTML = items
      .map((it) => {
        let primaryActionHtml = '';
        if (it.redistributable && it.cfg.localFile) {
          const fmtLabel = it.kind === 'doc' ? (it.cfg.downloadLabel || 'JSON') : 'GEOJSON';
          primaryActionHtml = `<a class="dl-act-btn" href="${esc(it.cfg.localFile)}" download>${esc(fmtLabel)}</a>`;
        } else if (it.kind === 'layer') {
          primaryActionHtml = `<a class="dl-act-btn" href="index.html?layer=${encodeURIComponent(it.id)}">MAPA</a>`;
        } else if (it.kind === 'basemap') {
          primaryActionHtml = `<a class="dl-act-btn" href="index.html?basemap=${encodeURIComponent(it.id)}">MAPA</a>`;
        } else if (it.cfg.externalUrl) {
          primaryActionHtml = `<a class="dl-act-btn" href="${esc(it.cfg.externalUrl)}" target="_blank" rel="noopener">${esc(it.cfg.downloadLabel || 'ACESSAR')}</a>`;
        }

        return `
          <div class="dl-row">
            <div class="dl-row-name">${esc(it.displayLine)}</div>
            <div class="dl-action-group">
              ${primaryActionHtml}
              <button type="button" class="dl-act-btn" data-dl-meta="${esc(it.id)}">METADADOS</button>
            </div>
          </div>`;
      })
      .join('');
  }

  function extractCentroidCoords(geom) {
    if (!geom) return ['', ''];
    if (geom.type === 'Point') return [geom.coordinates[0], geom.coordinates[1]];
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const walk = (c) => {
      if (!Array.isArray(c)) return;
      if (typeof c[0] === 'number') {
        if (c[0] < minX) minX = c[0];
        if (c[0] > maxX) maxX = c[0];
        if (c[1] < minY) minY = c[1];
        if (c[1] > maxY) maxY = c[1];
      } else c.forEach(walk);
    };
    walk(geom.coordinates);
    if (!Number.isFinite(minX)) return ['', ''];
    return [((minX + maxX) / 2).toFixed(6), ((minY + maxY) / 2).toFixed(6)];
  }

  async function downloadCsvForLayer(layerId) {
    const it = ALL_ITEMS.find((x) => x.id === layerId);
    if (!it || !it.redistributable || !it.cfg.localFile) return;

    let gj = null;
    if (it.cfg.bundleKey && window.GEOAMESC_BUNDLE?.[it.cfg.bundleKey]) {
      gj = window.GEOAMESC_BUNDLE[it.cfg.bundleKey];
    } else {
      try {
        const r = await fetch(it.cfg.localFile);
        if (r.ok) gj = await r.json();
      } catch {
        // ignore
      }
    }
    if (!gj?.features?.length) {
      alert('Não foi possível carregar os registros desta camada para exportar em CSV.');
      return;
    }

    const keys = [];
    const seen = new Set();
    for (const f of gj.features.slice(0, 50)) {
      for (const k of Object.keys(f.properties || {})) {
        if (!seen.has(k)) {
          seen.add(k);
          keys.push(k);
        }
      }
    }
    const headers = [...keys, 'longitude_centro', 'latitude_centro'];
    const csvCell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const rows = [headers.map(csvCell).join(';')];
    for (const f of gj.features) {
      const props = f.properties || {};
      const [lon, lat] = extractCentroidCoords(f.geometry);
      const vals = keys.map((k) => csvCell(props[k]));
      vals.push(csvCell(lon), csvCell(lat));
      rows.push(vals.join(';'));
    }
    const blob = new Blob(['\ufeff' + rows.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `amesc_${layerId}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function openDlMetadataModal(itemId) {
    const it = ALL_ITEMS.find((x) => x.id === itemId);
    if (!it) return;
    const meta = it.metaEntry.metadata;
    document.getElementById('dlModalTitle').textContent = it.cleanName;

    const rowsHtml = Meta.FIELD_LABELS.map(([k, lbl]) => {
      const val = meta[k] || 'Não informado';
      const isUrl = typeof val === 'string' && /^https?:\/\//i.test(val);
      return `<tr><th>${esc(lbl)}</th><td>${isUrl ? `<a href="${esc(val)}" target="_blank" rel="noopener" style="color:#1d8ac7;word-break:break-all">${esc(val)}</a>` : esc(val)}</td></tr>`;
    }).join('');

    const actionBtns = [];
    if (it.redistributable && it.cfg.localFile) {
      actionBtns.push(`<a class="dl-meta-btn primary" href="${esc(it.cfg.localFile)}" download>Baixar arquivo (${esc(it.kind === 'doc' ? 'JSON' : 'GeoJSON')})</a>`);
      if (it.kind === 'layer') {
        actionBtns.push(`<button type="button" class="dl-meta-btn" data-modal-csv="${esc(it.id)}">Exportar tabela (CSV)</button>`);
      }
    }
    if (it.kind === 'layer') {
      actionBtns.push(`<a class="dl-meta-btn" href="index.html?layer=${encodeURIComponent(it.id)}">Visualizar no mapa</a>`);
    } else if (it.kind === 'basemap') {
      actionBtns.push(`<a class="dl-meta-btn" href="index.html?basemap=${encodeURIComponent(it.id)}">Visualizar no mapa</a>`);
    } else if (it.cfg.externalUrl) {
      actionBtns.push(`<a class="dl-meta-btn primary" href="${esc(it.cfg.externalUrl)}" target="_blank" rel="noopener">Acessar fonte oficial</a>`);
    }

    const bodyEl = document.getElementById('dlModalBody');
    bodyEl.innerHTML = `
      <div class="dl-meta-actions">${actionBtns.join('')}</div>
      <table class="gp-meta-table">${rowsHtml}</table>
    `;
    bodyEl.querySelector('[data-modal-csv]')?.addEventListener('click', (e) => {
      downloadCsvForLayer(e.currentTarget.dataset.modalCsv);
    });
    document.getElementById('dlModalBackdrop').classList.add('open');
  }

  searchInput?.addEventListener('input', () => {
    queryText = searchInput.value;
    renderResults();
  });

  clearBtn?.addEventListener('click', () => {
    if (!searchInput) return;
    searchInput.value = '';
    queryText = '';
    renderResults();
    searchInput.focus();
  });

  document.getElementById('dlCategoryList')?.addEventListener('click', (e) => {
    const b = e.target.closest('[data-sec-id]');
    if (!b) return;
    selectedSectionId = b.dataset.secId;
    renderSidebar();
    renderHeader();
    renderResults();
  });

  document.getElementById('dlResults')?.addEventListener('click', (e) => {
    const mb = e.target.closest('[data-dl-meta]');
    if (mb) {
      openDlMetadataModal(mb.dataset.dlMeta);
    }
  });

  document.getElementById('dlModalClose')?.addEventListener('click', () => {
    document.getElementById('dlModalBackdrop')?.classList.remove('open');
  });

  document.getElementById('dlModalBackdrop')?.addEventListener('click', (e) => {
    if (e.target.id === 'dlModalBackdrop') e.target.classList.remove('open');
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.getElementById('dlModalBackdrop')?.classList.remove('open');
    }
  });

  renderSidebar();
  renderHeader();
  renderResults();
})();
