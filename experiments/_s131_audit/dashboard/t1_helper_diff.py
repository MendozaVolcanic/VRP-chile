# -*- coding: utf-8 -*-
"""S131 T1 - Diff semantico de helpers replicados + tablas inner_radius_km.
READ-ONLY. Reimplementa en Python la semantica JS de cada vista y mide sobre
data real cuantos records disparan cada divergencia."""
import io, json, os, re, sys, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
          "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
          "Tupungatito", "Villarrica"]

# ---------- Parte A: tablas inner_radius_km ----------
yml = {v['name']: v.get('inner_radius_km') for v in
       yaml.safe_load(open(os.path.join(ROOT, 'volcanoes.yaml'), encoding='utf-8'))['volcanoes']}

idx_txt = open(os.path.join(ROOT, 'frontend/index.html'), encoding='utf-8').read()
mos_txt = open(os.path.join(ROOT, 'frontend/mosaico.html'), encoding='utf-8').read()
dia_txt = open(os.path.join(ROOT, 'frontend/diario.html'), encoding='utf-8').read()


def js_volcanoes(txt):
    out = {}
    for m in re.finditer(r'\{\s*name:\s*"([^"]+)".*?\}', txt):
        blk = m.group(0)
        ir = re.search(r'inner_radius_km:\s*([\d.]+)', blk)
        out[m.group(1)] = float(ir.group(1)) if ir else None
    return out


idx_tab = js_volcanoes(idx_txt)
mos_tab = js_volcanoes(mos_txt)
_m = re.search(r'const INNER_RADIUS_KM = \{(.*?)\};', dia_txt, re.S)
dia_tab = {k: float(v) for k, v in re.findall(r'(\w+):\s*([\d.]+)', _m.group(1))}

print("=== T1-A  inner_radius_km: volcanoes.yaml (45) vs las 3 vistas ===")
print("yaml=%d  index.VOLCANOES_ALL=%d  mosaico.VOLCANOES=%d  diario.INNER_RADIUS_KM=%d"
      % (len(yml), len(idx_tab), len(mos_tab), len(dia_tab)))
rows = []
for name in sorted(yml):
    y = yml[name]

    def eq(a, b):
        if a is None and b is None:
            return True  # ambos sin inner_radius_km declarado -> alineados
        if a is None or b is None:
            return False
        return float(a) == float(b)

    bad, missing = [], []
    for label, tab in (("index", idx_tab), ("mosaico", mos_tab), ("diario", dia_tab)):
        if name not in tab:
            missing.append(label)
        elif not eq(y, tab[name]):
            bad.append("%s=%s" % (label, tab[name]))
    if bad or missing:
        rows.append((name, y, bad, missing))
for name, y, bad, missing in rows:
    print("  %-24s yaml=%-5s desalineado=%-14s ausente_en=%s"
          % (name, y, bad or '-', missing or '-'))
print("  volcanes con desalineacion de VALOR: %d"
      % sum(1 for r in rows if r[2]))
print("  volcanes ausentes de alguna tabla JS: %d/45" % sum(1 for r in rows if r[3]))
print("  fallback si ausente: index/mosaico `?? 10` (index.html:1798,1905,3065,3239,3299)"
      " ; diario `?? 5` (diario.html:249,327)")

# ---------- Parte B: semantica de mirovaEqVrp ----------


def eq_index(r, inner_km, include_far=False):
    """index.html:972 (== mosaico.html:245)."""
    if not r:
        return 0.0
    pc = r.get('primary_cluster')
    if not pc:
        vfb = r.get('vrp_mw')
        if vfb is None:
            vfb = r.get('vrp_mir_mw')
        if vfb is None:
            vfb = 0.0
        return 0.0 if vfb > 50000 else vfb
    dc = r.get('distance_class')
    if dc and dc != 'summit' and not include_far:
        return 0.0
    cd = pc.get('centroid_dist_km')
    if not include_far and cd is not None and cd > inner_km:
        return 0.0
    v = pc.get('vrp_mw') or 0.0
    return 0.0 if v > 50000 else v


def eq_diario(r, inner_km, include_far=False):
    """diario.html:239 - orden invertido, fallback sin cap ni vrp_mir_mw."""
    if not r:
        return 0.0
    dc = r.get('distance_class')
    if dc and dc != 'summit' and not include_far:
        return 0.0
    pc = r.get('primary_cluster')
    if not pc:
        v = r.get('vrp_mw')
        return 0.0 if v is None else v  # SIN cap 50000, SIN vrp_mir_mw
    cd = pc.get('centroid_dist_km')
    if not include_far and cd is not None and cd > inner_km:
        return 0.0
    v = pc.get('vrp_mw') or 0.0
    return 0.0 if v > 50000 else v


def sensor_group_index(s):
    if not s:
        return None
    if s.startswith('MODIS'):
        return 'MODIS'
    if '750' in s:
        return 'VIIRS750'
    if s.startswith('VIIRS'):
        return 'VIIRS375'
    return None


def sensor_bucket_diario(s):
    if not s:
        return None
    if s.startswith('MODIS'):
        return 'MODIS'
    if s.endswith('_750'):
        return 'VIIRS750'
    if s.startswith('VIIRS'):
        return 'VIIRS375'
    return None


print("\n=== T1-B  Divergencias de mirovaEqVrp sobre los 11 Tier A ===")
tot = 0
d_order = d_cap = d_mir = d_inner = d_sensor = 0
no_pc = 0
per_vol, dates, sensors = {}, [], set()
val_diff = 0
for vol in TIER_A:
    recs = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                          encoding='utf-8'))['records']
    inner_dia = dia_tab.get(vol, 5)
    inner_idx = idx_tab.get(vol, 10)
    c = dict(n=len(recs), no_pc=0, order=0, cap=0, mir=0, inner=0, sensor=0, valdiff=0,
             inner_idx=inner_idx, inner_dia=inner_dia)
    for r in recs:
        tot += 1
        if r.get('datetime_utc'):
            dates.append(r['datetime_utc'])
        sensors.add(r.get('sensor'))
        pc = r.get('primary_cluster')
        dc = r.get('distance_class')
        if not pc:
            no_pc += 1
            c['no_pc'] += 1
            if dc and dc != 'summit':
                c['order'] += 1
                d_order += 1  # unico caso donde el ORDEN de los chequeos importa
            v = r.get('vrp_mw')
            if v is not None and v > 50000:
                c['cap'] += 1
                d_cap += 1
            if v is None and r.get('vrp_mir_mw') is not None:
                c['mir'] += 1
                d_mir += 1
        a, b = eq_index(r, inner_idx), eq_diario(r, inner_dia)
        if a != b:
            c['valdiff'] += 1
            val_diff += 1
            if (a > 0) != (b > 0) and pc and pc.get('centroid_dist_km') is not None \
                    and inner_idx != inner_dia:
                c['inner'] += 1
                d_inner += 1
        if sensor_group_index(r.get('sensor')) != sensor_bucket_diario(r.get('sensor')):
            c['sensor'] += 1
            d_sensor += 1
    per_vol[vol] = c

ventana = (min(dates), max(dates)) if dates else ('-', '-')
print("denominador = %d records de los 11 Tier A; ventana %s .. %s UTC"
      % (tot, ventana[0], ventana[1]))
print("  records sin primary_cluster (rama fallback alcanzable): %d (%.2f%%)"
      % (no_pc, 100.0 * no_pc / tot))
print("  D1 ORDEN invertido alcanzable (sin pc AND distance_class!=summit): %d (%.4f%%)"
      % (d_order, 100.0 * d_order / tot))
print("  D2 CAP 50000 ausente en fallback diario (vrp_mw>50000 sin pc): %d" % d_cap)
print("  D3 vrp_mir_mw faltante en fallback (vrp_mw None y vrp_mir_mw presente): %d" % d_mir)
print("  D4 inner_km distinto index/diario -> flip visible/invisible: %d" % d_inner)
print("  D5 sensorGroup(index) != sensorBucket(diario): %d" % d_sensor)
print("  TOTAL records donde eq_index(r) != eq_diario(r): %d (%.4f%%)"
      % (val_diff, 100.0 * val_diff / tot))
print("\n  por volcan  (inner index/diario | n | sin_pc | order | cap | mir | inner | sensor | valdiff):")
for v, c in per_vol.items():
    print("    %-22s %2s/%-2s n=%6d sin_pc=%6d order=%4d cap=%3d mir=%3d inner=%5d sensor=%4d valdiff=%5d"
          % (v, c['inner_idx'], c['inner_dia'], c['n'], c['no_pc'], c['order'],
             c['cap'], c['mir'], c['inner'], c['sensor'], c['valdiff']))
print("\n  sensores presentes en data: %s" % sorted(x for x in sensors if x))

# ---------- Parte C: campos de fallback ----------
print("\n=== T1-C  presencia de vrp_mir_mw / vrp_mw en el corpus ===")
n_mir = n_vrp_none = 0
for vol in TIER_A:
    for r in json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                            encoding='utf-8'))['records']:
        if 'vrp_mir_mw' in r:
            n_mir += 1
        if r.get('vrp_mw') is None:
            n_vrp_none += 1
print("  records con clave vrp_mir_mw: %d / %d" % (n_mir, tot))
print("  records con vrp_mw == None : %d / %d" % (n_vrp_none, tot))

# ---------- Parte D: diff TEXTUAL normalizado de cada helper ----------
import difflib


def grab(txt, name):
    """Cuerpo de `function name(...)` por conteo de llaves; None si no existe."""
    m = re.search(r'\n(?:function|const)\s+' + re.escape(name) + r'\b', txt)
    if not m:
        return None
    i = txt.index('{', m.start())
    depth, j = 0, i
    while j < len(txt):
        if txt[j] == '{':
            depth += 1
        elif txt[j] == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    return txt[m.start() + 1:j + 1]


def norm(body, rename):
    """Quita comentarios y espacio; renombra parametros a nombres canonicos."""
    b = re.sub(r'//[^\n]*', '', body)
    b = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
    for a, z in rename.items():
        b = re.sub(r'\b' + re.escape(a) + r'\b', z, b)
    return re.sub(r'\s+', ' ', b).strip()


REN_DIA = {'volcanoName': 'INNER', 'includeFarDistance': 'includeFar'}
REN_IDX = {'includeFarDistance': 'includeFar'}
HELPERS = ["mirovaEqVrp", "mirovaEqVrpCore", "f5CoreMagnitude", "isCirrusArtifact",
           "isDiffuseFieldArtifact", "isThermalArtifact", "parseUtcMs",
           "eqVrpDisplay", "mirovaEqVrpDisplay", "isValidDetection",
           "isSummitDetection", "getLevel", "LEVELS", "sensorGroup", "sensorBucket",
           "_havKm"]
print("\n=== T1-D  diff textual normalizado (comentarios y espacio fuera) ===")
for h in HELPERS:
    bi, bm, bd = grab(idx_txt, h), grab(mos_txt, h), grab(dia_txt, h)
    ni = norm(bi, REN_IDX) if bi else None
    nm = norm(bm, REN_IDX) if bm else None
    nd = norm(bd, REN_DIA) if bd else None
    pres = "".join('X' if x else '-' for x in (ni, nm, nd))
    same_im = (ni == nm) if (ni and nm) else None
    same_id = (ni == nd) if (ni and nd) else None
    print("  %-24s [idx,mos,dia]=%s  idx==mos:%-5s idx==dia:%-5s"
          % (h, pres, same_im, same_id))
    if same_im is False:
        print("      idx: %s" % ni[:400])
        print("      mos: %s" % nm[:400])
    if same_id is False:
        print("      idx: %s" % ni[:400])
        print("      dia: %s" % nd[:400])
