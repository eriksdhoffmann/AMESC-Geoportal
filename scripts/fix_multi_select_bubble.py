from pathlib import Path

# 1. Fix double-toggle bubbling + multi-select dropdown label in js/app.js
p_app = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\js\app.js")
s_app = p_app.read_text(encoding="utf-8")
eol_app = "\r\n" if "\r\n" in s_app else "\n"
s_app_lf = s_app.replace("\r\n", "\n")

old_btn = """              <button class="gp-opt-btn" data-pick-mun="${m.cd_mun}" style="${isSel ? 'background:#033c8e;color:#fff;border-color:#033c8e' : ''}">${isSel ? '✓ Selecionado' : 'Selecionar'}</button>"""
new_btn = """              <button type="button" class="gp-opt-btn" style="${isSel ? 'background:#033c8e;color:#fff;border-color:#033c8e' : ''}">${isSel ? '✓ Selecionado' : 'Selecionar'}</button>"""
assert old_btn in s_app_lf, "old_btn not found!"
s_app_lf = s_app_lf.replace(old_btn, new_btn, 1)

old_hdr = """    const headerSel = document.getElementById('headerMunSelect');
    if (headerSel) {
      headerSel.value = codes.length === 1 ? codes[0] : 'ALL';
    }"""
new_hdr = """    const headerSel = document.getElementById('headerMunSelect');
    if (headerSel) {
      let multiOpt = headerSel.querySelector('option[value="__MULTI__"]');
      if (codes.length > 1) {
        if (!multiOpt) {
          multiOpt = document.createElement('option');
          multiOpt.value = '__MULTI__';
          headerSel.insertBefore(multiOpt, headerSel.firstChild);
        }
        multiOpt.textContent = `${codes.length} municípios selecionados`;
        headerSel.value = '__MULTI__';
      } else {
        if (multiOpt) multiOpt.remove();
        headerSel.value = codes.length === 1 ? codes[0] : 'ALL';
      }
    }"""
assert old_hdr in s_app_lf, "old_hdr not found!"
s_app_lf = s_app_lf.replace(old_hdr, new_hdr, 1)

old_change = """    sel.addEventListener('change', () => selectMunicipality(sel.value));"""
new_change = """    sel.addEventListener('change', () => {
      if (sel.value === '__MULTI__') return;
      selectMunicipality(sel.value);
    });"""
assert old_change in s_app_lf, "old_change not found!"
s_app_lf = s_app_lf.replace(old_change, new_change, 1)

p_app.write_text(s_app_lf.replace("\n", eol_app), encoding="utf-8")

# 2. Explicitly add fillRule: 'evenodd' to buildMunicipalMask in js/layer-engine.js
p_eng = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\js\layer-engine.js")
s_eng = p_eng.read_text(encoding="utf-8")
eol_eng = "\r\n" if "\r\n" in s_eng else "\n"
s_eng_lf = s_eng.replace("\r\n", "\n")

old_poly = """        fillColor: '#ffffff',
        fillOpacity: 1,
        interactive: false,"""
new_poly = """        fillColor: '#ffffff',
        fillOpacity: 1,
        fillRule: 'evenodd',
        interactive: false,"""
assert old_poly in s_eng_lf, "old_poly not found!"
s_eng_lf = s_eng_lf.replace(old_poly, new_poly, 1)
p_eng.write_text(s_eng_lf.replace("\n", eol_eng), encoding="utf-8")

# 3. Bump cache-busting query in index.html
p_idx = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\index.html")
s_idx = p_idx.read_text(encoding="utf-8")
s_idx = s_idx.replace("?v=20261127-6", "?v=20261127-7")
p_idx.write_text(s_idx, encoding="utf-8")

print("ALL PATCHED OK!")
