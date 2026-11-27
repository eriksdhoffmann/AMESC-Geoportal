import re

# 1. index.html: remove "15 Municípios" nav button & bump ?v=20261127-5
p_html = r'C:\Users\Win11\Downloads\AMESC-Geoportal\index.html'
html = open(p_html, encoding='utf-8').read()
html = re.sub(r'\s*<button class="gp-nav-btn" data-nav="municipios">15 Municípios</button>', '', html)
html = html.replace('?v=20261127-4', '?v=20261127-5')
open(p_html, 'w', encoding='utf-8').write(html)

# 2. js/app.js:
p_app = r'C:\Users\Win11\Downloads\AMESC-Geoportal\js\app.js'
app = open(p_app, encoding='utf-8').read()

# 2a. Start with Satelite HD only (0 vector layers)
for lid in ['amesc_municipios', 'amesc_localidades_osm', 'amesc_setores_risco_sgb']:
    app = re.sub(rf"\s*engine\.enableLayer\('{lid}'\);", '', app)

# 2b. Remove "Carta SGB ↗" from municipality cards
app = re.sub(r"\s*\$\{rigeoPdf \? `<a class=\"gp-opt-btn\"[^>]+>Carta SGB ↗</a>` : ''\}", '', app)

# 2c. Make "Início" (navId === 'home') reset directly to clean Satelite HD + 0 layers + ALL 15 cities (no modal)
old_home = "    modalBackdrop?.classList.add('open');\n\n    if (navId === 'home') {"
old_home_crlf = old_home.replace('\n', '\r\n')
new_home = """    if (navId === 'home') {
      modalBackdrop?.classList.remove('open');
      setNavActive('map');
      tools.disableSwipe();
      engine.clearAllLayers();
      engine.setBasemapActive('satelite_global', true, true);
      selectMunicipality('ALL');
      renderLayerDrawer();
      return;
    }

    modalBackdrop?.classList.add('open');

    if (false) {"""
if old_home_crlf in app:
    app = app.replace(old_home_crlf, new_home.replace('\n', '\r\n'), 1)
elif old_home in app:
    app = app.replace(old_home, new_home, 1)
else:
    raise RuntimeError('old_home not found')

open(p_app, 'w', encoding='utf-8').write(app)
print('Applied all 4 UI cleanups successfully!')
