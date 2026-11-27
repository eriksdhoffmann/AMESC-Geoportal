ROOT = r'C:\Users\Win11\Downloads\AMESC-Geoportal'
SRC_JM = r'C:\Users\Win11\Downloads\Geopotal Jacinto Machado\js\app.js'

app = open(SRC_JM, encoding='utf-8').read()

repls = [
    ('Geoportal Municipal de Jacinto Machado', 'Geoportal Regional da AMESC'),
    ('JACINTO_CENTER', 'AMESC_CENTER'),
    ('JACINTO_URBAN_CENTER', 'AMESC_CENTER'),
    ('JACINTO_BOUNDS', 'AMESC_BOUNDS'),
    ('RIGEO_PDF_URL', 'SIGSC_WMS'),
    ('RIGEO_ITEM_URL', 'SIGSC_WMS'),
    ("    PENDING_MUNICIPAL_LAYERS,\n", ""),
    ("let drawerTab = 'layers'; // 'layers' | 'order' | 'legend'", "let drawerTab = 'layers'; // 'layers' | 'municipios' | 'order' | 'legend'"),
    ("zoom: 12,\n    minZoom: 10,", "zoom: 10,\n    minZoom: 8,"),
    ("engine.enableLayer('limite_municipal_ibge');\n  engine.enableLayer('localidades_jacinto');\n  engine.enableLayer('sgb_setores_risco');",
     "engine.enableLayer('amesc_municipios');\n  engine.enableLayer('amesc_localidades_osm');\n  engine.enableLayer('amesc_setores_risco_sgb');"),
    ("'recortar limite jacinto machado ibge'", "'recortar limite amesc municipio ibge'"),
    ("Recortar mapa ao limite oficial de Jacinto Machado (IBGE)", "Recortar mapa ao limite selecionado (AMESC / Município)"),
    ('IBGE 4208708 — 430,704 km²', 'AMESC — 15 Municípios'),
    ('IBGE 4208708', 'AMESC (15 Municípios)'),
    ('430,704 km²', 'Extremo Sul Catarinense'),
    ('de Jacinto Machado', 'da região AMESC'),
    ('em Jacinto Machado', 'na região AMESC'),
    ('Jacinto Machado — SC', 'AMESC — Extremo Sul Catarinense (SC)'),
    ('Jacinto Machado', 'Região AMESC'),
]
for a, b in repls:
    app = app.replace(a, b)

# Add selectMunicipality helper + wire headerMunSelect + tabMunicipios
mun_logic = """
  // ==================== SELETOR DOS 15 MUNICÍPIOS (ESTILO SEPLAN/DIVISAS SC) ====================
  function getAmsecMunicipiosList() {
    return (window.AMESC_INDICADORES?.municipios || []).slice().sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
  }

  function selectMunicipality(cdMun, { zoom = true } = {}) {
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
  }

  // Popular dropdown do cabeçalho
  (() => {
    const sel = document.getElementById('headerMunSelect');
    if (!sel) return;
    for (const m of getAmsecMunicipiosList()) {
      const opt = document.createElement('option');
      opt.value = m.cd_mun;
      opt.textContent = m.nome;
      sel.appendChild(opt);
    }
    sel.addEventListener('change', () => selectMunicipality(sel.value));
  })();

  function renderMunicipiosTab(container) {
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
  }
"""

app = app.replace('  function renderLayerDrawer() {', mun_logic + '\n  function renderLayerDrawer() {', 1)

# Wire tabMunicipios in renderLayerDrawer & click events
app = app.replace(
    "    document.getElementById('tabLayers')?.classList.toggle('active', drawerTab === 'layers');\n    document.getElementById('tabOrder')?.classList.toggle('active', drawerTab === 'order');",
    "    document.getElementById('tabLayers')?.classList.toggle('active', drawerTab === 'layers');\n    document.getElementById('tabMunicipios')?.classList.toggle('active', drawerTab === 'municipios');\n    document.getElementById('tabOrder')?.classList.toggle('active', drawerTab === 'order');"
)
app = app.replace(
    "    if (drawerTab === 'order') {\n      renderOrderTab(body);\n      return;\n    }",
    "    if (drawerTab === 'municipios') {\n      renderMunicipiosTab(body);\n      return;\n    }\n    if (drawerTab === 'order') {\n      renderOrderTab(body);\n      return;\n    }"
)
app = app.replace(
    "  document.getElementById('tabLayers')?.addEventListener('click', () => { drawerTab = 'layers'; renderLayerDrawer(); });",
    "  document.getElementById('tabLayers')?.addEventListener('click', () => { drawerTab = 'layers'; renderLayerDrawer(); });\n  document.getElementById('tabMunicipios')?.addEventListener('click', () => { drawerTab = 'municipios'; renderLayerDrawer(); });"
)

# Replace socio modal + add municipios modal inside openNavSection
socio_start = app.find("    } else if (navId === 'socio') {")
help_start = app.find("    } else if (navId === 'help') {")
if socio_start != -1 and help_start != -1:
    new_modals = """    } else if (navId === 'municipios') {
      modalTitle.textContent = '15 Municípios da AMESC — Extremo Sul Catarinense (SEPLAN / IBGE)';
      const muns = getAmsecMunicipiosList();
      const fmtN = (n, d = 0) => Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
      const cur = engine.getSelectedMunicipality();
      modalBody.innerHTML = `
        <div class="gp-hero-banner" style="margin-bottom:14px">
          <h3>Mosaico Regional Integrado × Consulta Individual por Município</h3>
          <p style="margin:4px 0 8px">Inspirado no portal oficial de Divisas Intermunicipais de SC (SEPLAN/DITER), escolha qualquer um dos <b>15 municípios da AMESC</b> para focar no mapa, isolar seu perímetro ou acessar sua Carta de Suscetibilidade SGB/CPRM.</p>
          <div class="gp-btn-row">
            <button class="gp-btn primary" data-modal-pick-mun="ALL">Ver Mosaico Completo (15 Municípios)</button>
            <a class="gp-btn" href="https://divisasintermunicipais.sc.gov.br/" target="_blank" rel="noopener">Portal Divisas SC (SEPLAN) ↗</a>
          </div>
        </div>
        <div class="gp-mun-grid-modal">
          ${muns.map((m) => `
            <div class="gp-mun-card ${String(cur) === String(m.cd_mun) ? 'active' : ''}">
              <div class="gp-mun-card-top">
                <span class="gp-mun-card-name">${escapeHtml(m.nome)}</span>
                <span class="gp-mun-card-code">${m.cd_mun}</span>
              </div>
              <div class="gp-mun-card-stats">
                <span><b>Pop. 2022:</b> ${fmtN(m.pop_2022)} hab.</span>
                <span><b>Área:</b> ${fmtN(m.area_ibge_km2 || m.area_km2, 1)} km²</span>
                <span><b>Densidade:</b> ${fmtN(m.densidade_2022, 1)} hab/km²</span>
                <span><b>PIB (${escapeHtml(m.pib_ano || '2023')}):</b> R$ ${fmtN((m.pib_total_mil || 0)/1000, 1)} mi</span>
              </div>
              <div class="gp-mun-card-actions">
                <button class="gp-btn primary" data-modal-pick-mun="${m.cd_mun}">Abrir no Mapa</button>
                ${m.rigeo?.pdf_url ? `<a class="gp-btn" href="${escapeHtml(m.rigeo.pdf_url)}" target="_blank" rel="noopener">SGB PDF ↗</a>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      `;
      modalBody.querySelectorAll('[data-modal-pick-mun]').forEach((b) => {
        b.addEventListener('click', () => {
          closeModal();
          selectMunicipality(b.dataset.modalPickMun);
        });
      });
    } else if (navId === 'socio') {
      modalTitle.textContent = 'Painel Socioeconômico Comparativo — AMESC (15 Municípios)';
      const ind = window.AMESC_INDICADORES || {};
      const tot = ind.totais || {};
      const muns = (ind.municipios || []).slice().sort((a, b) => (b.pop_2022 || 0) - (a.pop_2022 || 0));
      const fmtN = (n, d = 0) => Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
      const fmtBRL = (n) => 'R$ ' + fmtN(n, 2);

      modalBody.innerHTML = `
        <div class="gp-hero-banner" style="margin-bottom:14px">
          <h3>Indicadores Oficiais Integrados da AMESC — Censo IBGE 2022, PIB 2023, PAM &amp; DataSUS/CNES</h3>
          <p style="margin:4px 0 0">Comparativo oficial dos <b>15 municípios do Extremo Sul Catarinense</b> com foco interativo no mapa.</p>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:16px">
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid #033c8e;border-radius:8px;padding:10px 12px">
            <div style="font-size:11px;font-weight:700;color:#64748b">POPULAÇÃO TOTAL AMESC (2022)</div>
            <div style="font-size:21px;font-weight:900;color:#0f172a">${fmtN(tot.pop_2022)} hab.</div>
            <div style="font-size:11px;color:#475569">${fmtN(tot.domicilios_2022)} domicílios • 15 municípios</div>
          </div>
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid #059669;border-radius:8px;padding:10px 12px">
            <div style="font-size:11px;font-weight:700;color:#64748b">ÁREA TERRITORIAL AMESC</div>
            <div style="font-size:21px;font-weight:900;color:#0f172a">${fmtN(tot.area_km2, 1)} km²</div>
            <div style="font-size:11px;color:#475569">${fmtN(tot.densidade_2022, 2)} hab./km²</div>
          </div>
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid #d97706;border-radius:8px;padding:10px 12px">
            <div style="font-size:11px;font-weight:700;color:#64748b">PIB REGIONAL AMESC (2023)</div>
            <div style="font-size:21px;font-weight:900;color:#0f172a">R$ ${fmtN((tot.pib_total_mil || 0)/1e6, 2)} bi</div>
            <div style="font-size:11px;color:#475569">Per capita médio: ${fmtBRL(tot.pib_per_capita)}</div>
          </div>
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:3px solid #dc2626;border-radius:8px;padding:10px 12px">
            <div style="font-size:11px;font-weight:700;color:#64748b">SAÚDE ATIVA (DATASUS/CNES)</div>
            <div style="font-size:21px;font-weight:900;color:#0f172a">${fmtN(tot.cnes_ativos)} unid.</div>
            <div style="font-size:11px;color:#475569">Estabelecimentos nos 15 municípios</div>
          </div>
        </div>

        <div style="overflow-x:auto;border:1px solid #e2e8f0;border-radius:8px;background:#fff">
          <table class="gp-meta-table" style="font-size:12px">
            <thead>
              <tr style="background:#f1f5f9">
                <th>Município</th>
                <th>Pop. 2022</th>
                <th>Urbana %</th>
                <th>Área (km²)</th>
                <th>PIB 2023 (R$ mi)</th>
                <th>PIB p/ cap.</th>
                <th>CNES</th>
                <th>Principal Cultura (PAM)</th>
                <th>Mapa</th>
              </tr>
            </thead>
            <tbody>
              ${muns.map((m) => {
                const topCrop = m.top_culturas?.[0] ? `${m.top_culturas[0].produto} (${fmtN(m.top_culturas[0].area_ha)} ha)` : '—';
                return `
                  <tr>
                    <td><b>${escapeHtml(m.nome)}</b></td>
                    <td>${fmtN(m.pop_2022)}</td>
                    <td>${fmtN(m.pop_urbana_pct, 1)}%</td>
                    <td>${fmtN(m.area_ibge_km2 || m.area_km2, 1)}</td>
                    <td>${fmtN((m.pib_total_mil || 0)/1000, 1)}</td>
                    <td>${fmtBRL(m.pib_per_capita)}</td>
                    <td>${m.cnes_ativos || 0}</td>
                    <td>${escapeHtml(topCrop)}</td>
                    <td><button class="gp-opt-btn" data-socio-mun="${m.cd_mun}">Focar</button></td>
                  </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
        <div class="gp-btn-row" style="margin-top:12px">
          <a class="gp-btn primary" href="data/amesc_indicadores.json" download>Baixar Indicadores Completos (JSON) ↓</a>
        </div>
      `;
      modalBody.querySelectorAll('[data-socio-mun]').forEach((b) => {
        b.addEventListener('click', () => {
          closeModal();
          selectMunicipality(b.dataset.socioMun);
        });
      });
"""
    app = app[:socio_start] + new_modals + app[help_start:]

open(f'{ROOT}/js/app.js', 'w', encoding='utf-8').write(app)
print('Wrote js/app.js', len(app))
