from pathlib import Path

# 1. Clean up Download nav link and tile in index.html + bump ?v=20261127-8
p_idx = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\index.html")
s_idx = p_idx.read_text(encoding="utf-8")

s_idx = s_idx.replace(
    '<a class="gp-nav-btn" href="downloads.html" target="_blank" rel="opener" style="text-decoration:none">Download ↗</a>',
    '<a class="gp-nav-btn" href="downloads.html" style="text-decoration:none">Download</a>',
)
s_idx = s_idx.replace(
    '<a class="gp-home-tile" href="downloads.html" target="_blank" rel="opener">',
    '<a class="gp-home-tile" href="downloads.html">',
)
s_idx = s_idx.replace('Downloads &amp; Catálogo', 'Downloads')
s_idx = s_idx.replace('?v=20261127-7', '?v=20261127-8')
p_idx.write_text(s_idx, encoding="utf-8")

# 2. Support ?nav=home|socio|help in js/app.js so header links from downloads.html work seamlessly
p_app = Path(r"C:\Users\Win11\Downloads\AMESC-Geoportal\js\app.js")
s_app = p_app.read_text(encoding="utf-8")
eol = "\r\n" if "\r\n" in s_app else "\n"
s_lf = s_app.replace("\r\n", "\n")

old_tail = "  renderLayerDrawer();\n})();"
new_tail = """  renderLayerDrawer();

  // Suporte a ?nav=home|socio|help vindo da página de Downloads
  const initNav = new URLSearchParams(window.location.search).get('nav');
  if (initNav && ['home', 'socio', 'help'].includes(initNav)) {
    openNavSection(initNav);
  }
})();"""

assert old_tail in s_lf, "old_tail not found!"
s_lf = s_lf.replace(old_tail, new_tail, 1)
p_app.write_text(s_lf.replace("\n", eol), encoding="utf-8")

print("PATCHED index.html and js/app.js OK!")
