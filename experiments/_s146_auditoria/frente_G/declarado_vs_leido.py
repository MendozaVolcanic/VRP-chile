"""Frente G: para cada atributo, de que SECCION del YAML lo lee profile.py, con que default,
y si el YAML operacional trae la clave EN ESA seccion (A89b) o en otra. Tambien: claves del YAML que nadie lee."""
import json, os, re, yaml, subprocess
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, "..", "..", ".."))
attrs = json.load(open(os.path.join(here, "perfil_efectivo.json"), encoding="utf-8"))
prof = open(os.path.join(root, "pipeline/profile.py"), encoding="utf-8").read()
ypath = os.path.join(root, "pipeline/profiles/mirova_equivalent.yaml")
Y = yaml.safe_load(open(ypath, encoding="utf-8"))
SEC = {"_cfg": None, "_t": "thresholds", "_bg": "background", "_p": "paths", "_s": "sensors"}
def donde(key):
    out = []
    if key in Y: out.append("raiz")
    for s, d in Y.items():
        if isinstance(d, dict) and key in d: out.append(s)
    return out
def git(*a):
    return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
res = {}; leidas = set()
for m in re.finditer(r'(_cfg|_t|_bg|_p|_s)\.get\(\s*"([a-z0-9_]+)"', prof): leidas.add(m.group(2))
for m in re.finditer(r'(_cfg|_t|_bg|_p|_s)\[\s*"([a-z0-9_]+)"\s*\]', prof): leidas.add(m.group(2))
for a in attrs:
    m = re.search(r"^" + re.escape(a) + r"\b[^\n]*=((?:[^\n]*\n){1,5})", prof, flags=re.M)
    if not m: continue
    g = re.search(r'(_cfg|_t|_bg|_p|_s)(?:\.get\(\s*|\[\s*)"([a-z0-9_]+)"\s*(?:,\s*([^)\n]+))?', m.group(0))
    if not g: continue
    sec, key, default = SEC[g.group(1)] or "raiz", g.group(2), (g.group(3) or "").strip()
    esta_en = donde(key)
    ult = git("log", "-1", "--format=%as %h %s", "-G", r"^\s*" + key + r"\s*:", "--", "pipeline/profiles/mirova_equivalent.yaml")
    res[a] = {"seccion_que_lee_el_codigo": sec, "clave": key, "default_en_profile_py": default,
              "yaml_operacional_la_trae_en": esta_en,
              "origen_del_valor": ("YAML" if sec in esta_en else ("DEFAULT de profile.py (clave en otra seccion: %s)" % esta_en if esta_en else "DEFAULT de profile.py (clave ausente del YAML)")),
              "ultimo_commit_linea_yaml": ult[:150] or None}
json.dump(res, open(os.path.join(here, "declarado_vs_leido.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
mal = {a: r for a, r in res.items() if r["yaml_operacional_la_trae_en"] and r["seccion_que_lee_el_codigo"] not in r["yaml_operacional_la_trae_en"]}
print("atributos resueltos:", len(res), "de", len(attrs))
print("CLAVE ESCRITA EN OTRA SECCION QUE LA LEIDA:", json.dumps(mal, indent=1, ensure_ascii=False))
por_default = {a: (attrs[a], r["default_en_profile_py"]) for a, r in res.items() if r["origen_del_valor"].startswith("DEFAULT")}
print("valor por DEFAULT (no escrito en YAML):", len(por_default))
for a, v in por_default.items(): print("   ", a, v)
todas = set(Y) | {k for d in Y.values() if isinstance(d, dict) for k in d}
print("claves del YAML que profile.py NO lee:", sorted(k for k in todas if k not in leidas and k not in ("thresholds","background","paths","sensors")))
for a in ("ENABLE_FIRST_PASS_TESTS_2_AND_3","ENABLE_SINGLE_PIXEL_SUB_MW_MODE","ENABLE_TEST1_INTERMEDIATE_BG","ENABLE_TEST1_PRIORITY_WEAK_CLUSTER","ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750","ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS","ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS","ENABLE_DUAL_ROI_FIRST_PASS","ENABLE_DUAL_ROI_SECOND_PASS","ENABLE_UNSUITABLE_FILTERS_267_273","ENABLE_VRP_TIR_CONSISTENCY_GATE"):
    print(a, res.get(a, {}).get("origen_del_valor"), "|", res.get(a, {}).get("ultimo_commit_linea_yaml"))
