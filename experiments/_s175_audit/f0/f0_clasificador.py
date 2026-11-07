"""F0 S175: clasificador de los pendientes de S160 sin eje, contra el código de hoy.

Cada pendiente lleva un predicado mecánico sobre el árbol de git (git show <commit>:<ruta> y una expresión regular)
que dice si el defecto descrito en S160 SIGUE en el código. Se evalúa en dos commits:
- S160 = d516b9d8c (el que auditó S160): el predicado tiene que dar «sigue» ahí (si no, el predicado no describe el
  defecto o el defecto nunca fue como se escribió);
- BASE = 752d348bc (S175).
Si sigue en los dos: ABIERTO. Si sigue en S160 y no en la base: RESUELTO (se busca el commit con git log -S). Si no
sigue en S160: el predicado no ve el defecto (NO CLASIFICA) o el archivo no existía (SIN DATO en S160).

Línea base roja (plan S175 §3 F0): la decisión 1 (#891) tiene que salir RESUELTA con su commit y la decisión 6 (C-10)
ABIERTA. Si dan lo mismo, el clasificador no clasifica.

Las dos preguntas: (1) si un pendiente estuviera resuelto, ¿lo vería? Sólo si el arreglo cambia el texto que el
predicado busca; un arreglo con otra forma da falso ABIERTO, por eso cada fila RESUELTA se ancla además a un commit.
(2) si el instrumento estuviera muerto (git show falla, regex vacía), ¿se vería? Sí: archivo ausente da «sin archivo»,
nunca «resuelto».
"""
import io
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
S160 = "d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
_cache = {}


def show(commit, ruta):
    k = (commit, ruta)
    if k not in _cache:
        p = subprocess.run(["git", "-C", REPO, "-c", "core.autocrlf=false", "show", f"{commit}:{ruta}"],
                           capture_output=True)
        _cache[k] = p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None
    return _cache[k]


def tiene(commit, ruta, patron):
    t = show(commit, ruta)
    if t is None:
        return None
    return re.search(patron, t, re.M) is not None


def orden(commit, ruta, primero, despues):
    t = show(commit, ruta)
    if t is None:
        return None
    a, b = t.find(primero), t.find(despues)
    return a >= 0 and b >= 0 and a < b


def commit_que_quita(ruta, patron_fijo):
    p = subprocess.run(["git", "-C", REPO, "log", "--format=%h %cs %s", "-S", patron_fijo, BASE, "--", ruta],
                       capture_output=True, text=True, encoding="utf-8")
    lineas = [x for x in p.stdout.splitlines() if x]
    return lineas[0] if lineas else "sin commit encontrado"


# (id, grupo, descripción corta, función(commit) -> True si el defecto SIGUE, None si no hay archivo,
#  (ruta, texto fijo) para buscar el commit que lo cambió)
P = []


def item(i, grupo, desc, f, rastro=None):
    P.append((i, grupo, desc, f, rastro))


# --- Línea base roja ---
item("dec1", "decisiones", "#891: el preámbulo del auditor no está en main (falta la regla del módulo csv)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "docs/_prompts/PREAMBULO-AUDITOR.md", r"módulo csv")),
     ("docs/_prompts/PREAMBULO-AUDITOR.md", "módulo csv"))
item("dec6", "decisiones", "C-10 sin mirar antes de dar D18 por vetada (fila C-10 «abierto»)",
     lambda c: tiene(c, "docs/COLA_CAMPO.md", r"^\| C-10 \|.*\| abierto \|\s*$"))

# --- Vencimientos ---
item("241", "vencimientos", "plataforma callada = «Cobertura: completa» (sin nota de plataforma)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "scripts/run_pipeline.py", r"faltan plataformas enteras")),
     ("scripts/run_pipeline.py", "faltan plataformas enteras"))
item("241b", "vencimientos", "plataforma callada sigue saliendo con código 0 en modo estricto (sin_granulos no cuenta)",
     lambda c: tiene(c, "pipeline/fetch.py", r'"sin_granulos":\s*False') if show(c, "pipeline/fetch.py") and "TIPOS_INCIDENCIA" in show(c, "pipeline/fetch.py") else tiene(c, "scripts/run_pipeline.py", r"return 0"))
item("242", "vencimientos", "vigilante por plataforma fuera de main (nrt-healthcheck sin vigilar_plataformas)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, ".github/workflows/nrt-healthcheck.yml", r"vigilar_plataformas\.py")),
     (".github/workflows/nrt-healthcheck.yml", "vigilar_plataformas.py"))
item("243", "vencimientos", "nadie mide la fracción MODIS product_version nrt (sin vigilante en audit ni workflows)",
     lambda c: not (tiene(c, "scripts/auto_audit_weekly.py", r"product_version") or
                    tiene(c, ".github/workflows/nrt-healthcheck.yml", r"product_version")))
item("245", "vencimientos", "la copia del consolidado acepta encogimientos sin aviso",
     lambda c: (lambda r: None if r is None else not r)(
         tiene(c, "scripts/sync_mirova_csv.sh", r"avisar_llaves_perdidas") if show(c, "scripts/sync_mirova_csv.sh")
         else tiene(c, ".github/workflows/sync-mirova-csv.yml", r"avisar_llaves_perdidas")),
     ("scripts/sync_mirova_csv.sh", "avisar_llaves_perdidas"))
item("245b", "vencimientos", "la copia que se encoge igual se commitea (avisa, no rechaza: decisión de Nicolás)",
     lambda c: tiene(c, "scripts/sync_mirova_csv.sh", r"\|\| true\s*\n\s*mv latest_consolidado\.csv\.new"))
item("247", "vencimientos", "nrt.yml sin guarda de token vacío",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, ".github/workflows/nrt.yml", r'-z "\$EARTHDATA_TOKEN"')),
     (".github/workflows/nrt.yml", 'EARTHDATA_TOKEN vacío'))
item("V3-01", "vencimientos", "protegida sin record no genera aviso en el auto-audit",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "scripts/auto_audit_weekly.py", r"def avisos_protegidas_sin_record")),
     ("scripts/auto_audit_weekly.py", "def avisos_protegidas_sin_record"))
item("V3-02", "vencimientos", "medir_cadencia_cron ignora workflow_dispatch",
     lambda c: tiene(c, "scripts/medir_cadencia_cron.py", r'r\.get\("event"\) != "schedule"'))
item("V3-02b", "vencimientos", "cadencia.json sin consumidor (sólo lo escribe nrt-healthcheck)",
     lambda c: (lambda t: None if t is None else len(re.findall(r"cadencia\.json", t)) == 1)(show(c, ".github/workflows/nrt-healthcheck.yml")))
item("V3-03", "vencimientos", "= 247 (logins con token vacío en la matriz)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, ".github/workflows/nrt.yml", r'-z "\$EARTHDATA_TOKEN"')))

# --- VIIRS 750 ---
item("F1-H6", "viirs750", "D32 ABIERTA en el catálogo (publicamos el cúmulo, MIROVA la suma)",
     lambda c: tiene(c, "docs/MIROVA_DIVERGENCES.md", r"^## D32:.*\*\*ABIERTA"))
item("V2-09", "viirs750", "umbrales de cumbre rigen hasta inner_radius (caja del paper apagada)",
     lambda c: tiene(c, "pipeline/profile.py", r'enable_roi1_box_paper", False') and
     not tiene(c, "pipeline/profiles/mirova_equivalent.yaml", r"^\s*enable_roi1_box_paper:\s*true"))
item("V2-10", "viirs750", "anomaly_pixels.dist_km desde el centro del volcán, rotulado «al cráter»",
     lambda c: tiene(c, "pipeline/process_viirs_mod.py", r'"dist_km": round\(float\(dist\[r, c\]\), 2\)') and
     tiene(c, "frontend/index.html", r"Distancia al cráter: \$\{px\.dist_km"))
item("V2-11", "viirs750", "VRE con convención de 6 h por detección (sin base física)",
     lambda c: tiene(c, "frontend/index.html", r"const DT_HOURS = 6;"))
item("V2-12", "viirs750", "tope de 50 GW juzga t_max_k antes de copiar t_max_i04_k",
     lambda c: orden(c, "pipeline/store.py", "    _apply_sanity_cap(record)", 'record["t_max_k"] = record["t_max_i04_k"]'))
item("V0a-01", "decisiones", "D34 (código de MIROVA V750) fuera del catálogo de main",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "docs/MIROVA_DIVERGENCES.md", r"^## D34")),
     ("docs/MIROVA_DIVERGENCES.md", "## D34"))
item("V0b-01", "decisiones", "K1 decide el tope D9 (n_nti_path == 0) en V750; K1 -0,8 vigente",
     lambda c: tiene(c, "pipeline/process_viirs_mod.py", r"and n_nti_path == 0") and
     tiene(c, "pipeline/profiles/mirova_equivalent.yaml", r"nti_k1_night:\s*-0\.8"))
item("V0b-03", "decisiones", "el mínimo de cumbre 0,003 gobierna el umbral del dETI (c1_deti_summit=_c1_sum)",
     lambda c: tiene(c, "pipeline/process_viirs.py", r"c1_deti_summit=_c1_sum"))
item("dec2", "decisiones", "D25 sin decidir con P2 de tolerancia 0 (no hay marca de lectura de D25)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "docs/MIROVA_DIVERGENCES.md", r"D25 tal como está NO SE ADOPTA")),
     ("docs/MIROVA_DIVERGENCES.md", "D25 tal como está NO SE ADOPTA"))
item("dec9", "decisiones", "K1 -0,7 y tope D9 sin decisión (= V0b-01)",
     lambda c: tiene(c, "pipeline/profiles/mirova_equivalent.yaml", r"nti_k1_night:\s*-0\.8") and
     tiene(c, "pipeline/process_viirs_mod.py", r"and n_nti_path == 0"))
for cid in ("C-02", "C-03", "C-06", "C-07", "C-08", "C-09", "C-10"):
    item(cid, "cola_campo", f"fila {cid} de docs/COLA_CAMPO.md en estado «abierto»",
         (lambda k: lambda c: tiene(c, "docs/COLA_CAMPO.md", rf"^\| {k} \|.*\| abierto( \(fecha fija\))? \|\s*$"))(cid))

# --- Inventario sin verificar de S160 ---
item("166", "inventario", "bandas RECALL_MIN del auto-audit sin recalibrar desde C0",
     lambda c: tiene(c, "scripts/auto_audit_weekly.py", r'RECALL_MIN = \{"VIIRS375": 93\.4, "VIIRS750": 79\.5, "MODIS": 95\.0\}'))
item("F2-210", "inventario", "BT_PHYSICAL_MAX_K = 500 K de MODIS aplicado a los tres sensores",
     lambda c: tiene(c, "pipeline/store.py", r"BT_PHYSICAL_MAX_K\s*=\s*500"))
item("F2-212", "inventario", "ETI con refit iterativo a 3 sigma; segundo pase reusa el ETI del primero",
     lambda c: tiene(c, "pipeline/process_viirs_mod.py", r'eti_for_second_pass = fp_diag\.get\("eti"\)'))
item("F2-230", "inventario", "unidad declarada de WOOSTER_COEFF omite el área",
     lambda c: tiene(c, "pipeline/process_viirs.py", r"WOOSTER_COEFF.*W/m² per \(W/m²/sr/µm\)"))
item("F2-231", "inventario", "index.html usa 111,0 km/grado para el bbox MIROVA (pipeline 111,32)",
     lambda c: tiene(c, "frontend/index.html", r"/ 111\.0\b|\* 111\.0\b|111\.0 \*"))
item("F2-232", "inventario", "respaldo de inner_radius 10 en index y 5 en diario",
     lambda c: tiene(c, "frontend/diario.html", r"\?\?\s*5\b|\|\|\s*5\b") and tiene(c, "frontend/index.html", r"innerKm\s*=\s*10|\?\?\s*10\b|\|\|\s*10\b"))
item("F2-234", "inventario", "noche: store.py <= 0 contra run_pipeline < 0.0",
     lambda c: tiene(c, "pipeline/store.py", r"solar_elev_deg\s*<=\s*0") and tiene(c, "scripts/run_pipeline.py", r"<\s*0\.0"))
item("F2-235", "inventario", "np.std (N) donde MIROVA usa N-1",
     lambda c: tiene(c, "pipeline/detection_context.py", r"np\.std\((?![^)]*ddof)"))
item("249", "inventario", "nrt-retry sólo reintenta con NASA_DOWN",
     lambda c: tiene(c, ".github/workflows/nrt-retry.yml", r"NASA_DOWN"))
item("250", "inventario", "L1B sin geolocalización descartado en silencio (sin incidencia)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, "scripts/run_pipeline.py", r'"sin_geolocalizacion"')),
     ("scripts/run_pipeline.py", "sin_geolocalizacion"))
item("251", "inventario", "NOAA-20 consultado en versiones que no existen",
     lambda c: tiene(c, "pipeline/fetch.py", r'"versions": \["2\.1", "2", "1"\]'))
item("252", "inventario", "earthaccess sin fijar (>=)",
     lambda c: tiene(c, "requirements.txt", r"^earthaccess>="))
item("254", "inventario", "reconstrucción de data/mirova falla por volcán con WARN (continuing)",
     lambda c: tiene(c, "scripts/sync_mirova_csv.sh", r"WARN: rebuild \$stem failed \(continuing\)") if show(c, "scripts/sync_mirova_csv.sh")
     else tiene(c, ".github/workflows/sync-mirova-csv.yml", r"WARN: rebuild"))
item("256", "inventario", "el consolidado bajado no se valida (200 con HTML se commitea)",
     lambda c: (lambda r: None if r is None else not r)(tiene(c, ".github/workflows/sync-mirova-csv.yml", r"guarda_llaves_consolidado\.py")),
     (".github/workflows/sync-mirova-csv.yml", "guarda_llaves_consolidado.py"))
item("255", "inventario", "healthcheck con cron 0 12 (arranca horas tarde)",
     lambda c: tiene(c, ".github/workflows/nrt-healthcheck.yml", r'cron:\s*"0 12 \* \* \*"'))


def fmt(v):
    return {True: "sigue", False: "no sigue", None: "sin archivo"}[v]


print(f"# S160 = {S160}; BASE = {BASE}")
print("id,grupo,en_S160,en_BASE,estado,commit_que_lo_cambia,descripcion")
res = {}
for i, g, desc, f, rastro in P:
    try:
        a, b = f(S160), f(BASE)
    except TypeError:
        a, b = None, None
    if a is None and b is None:
        est = "SIN DATO"
    elif a is False and b is not True:
        est = "NO CLASIFICA (el predicado no ve el defecto en S160)" if a is False else "SIN DATO"
    elif b is True:
        est = "ABIERTO"
    elif b is False:
        est = "RESUELTO"
    else:
        est = "SIN DATO"
    if a is None and b is True:
        est = "ABIERTO (archivo creado después de S160)"
    if a is None and b is False:
        est = "RESUELTO o nunca abierto en S160 (archivo creado después)"
    com = commit_que_quita(*rastro) if (rastro and b is False) else ""
    res[i] = est
    print(f"{i},{g},{fmt(a)},{fmt(b)},{est},{com},{desc}")

print("\n# Línea base roja")
print(f"dec1 = {res['dec1']}; dec6 = {res['dec6']}")
ok = res["dec1"].startswith("RESUELTO") and res["dec6"].startswith("ABIERTO")
print("ROJO REENCONTRADO: el clasificador distingue" if ok else "ROJO NO REENCONTRADO: el clasificador no clasifica")
