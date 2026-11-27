import json, os, re
root = r'C:\Users\Win11\Downloads\AMESC-Geoportal'
cat = open(f'{root}/js/catalog.js', encoding='utf-8').read()
files = sorted(set(re.findall(r"localFile:\s*'([^']+)'", cat)))
missing, total_feats, total_kb = [], 0, 0
for lf in files:
    p = os.path.join(root, lf)
    if not os.path.exists(p): missing.append(lf)
    elif lf.endswith('.geojson'):
        d = json.load(open(p, encoding='utf-8'))
        total_feats += len(d.get('features', []))
        total_kb += os.path.getsize(p)/1024
print(f'AMESC CATALOG: {len(files)} files | missing={missing} | total_features={total_feats:,} | total_size={total_kb/1024:.2f} MB')
