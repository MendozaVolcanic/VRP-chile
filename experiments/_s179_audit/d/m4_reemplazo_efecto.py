# -*- coding: utf-8 -*-
"""M4 (frente D, S179). Que cambiaria en la serie PUBLICADA si se reemplaza K por la via con los artefactos que ya
existen (D2 y D4 de la retrospectiva), y que se saca de la serie con la regla A del plan #981 (apartar la pasada K
sin par en la via).

Fenomeno: K escribe un record por cada granulo que roza el volcan; la via descarta el granulo de borde y no deja record.
Si esa pasada de K publicaba una anomalia, apartarla la quita de lo que el operador ve en la historia.

Vara (preambulo del encargo): "publica" = predicado del tablero ejecutado con node por scripts/banco_paridad.py
(cargar_nuestros -> correr_node) sobre frontend/index.html de 438a60a1e. "alerta" y "protegida" = lectura A con D-9 SN,
con scripts/vigilancia_sombra.py::pasadas_de_alerta (la misma maquina que usa la vigilancia de la guardia) sobre la
referencia de 438a60a1e (latest_consolidado.csv + OCR + historico + respaldo). Pareo +-120 s (TOL_S).

Las dos preguntas del instrumento:
1. Si lo que mido estuviera roto (la via callando lo que K publica), esta medicion lo veria?  Si en las ventanas con
   artefacto (F26 2026-02-01..03-31, DM 2026-10-01..10-16, R25 2025-02-15..12-31). NO ve las ventanas de P4 (enero,
   abril a septiembre y 2026-10-17 en adelante): sus artefactos no estan bajados. NO es la lectura con candado de la
   retrospectiva y no la reemplaza (otra referencia, otro lector).
2. Si el instrumento estuviera muerto, el resultado se veria distinto?  Controles: (a) el conteo de pasadas K sin par
   tiene que reproducir la tabla 2.2 del plan (MODIS 217 en total); (b) control positivo: se quita a proposito de la
   union un record de la via cuya pasada K publica y es protegida, y la medicion tiene que contar una perdida mas;
   (c) en R25 la referencia de 438a60a1e casi no tiene filas: ahi "protegida" es SIN DATO y solo se informa "publica".

Denominadores: se imprimen con cada numero. Uso:
  python m4_reemplazo_efecto.py <snapshot main> <carpeta base> <D2> <D4> <carpeta union (temporal)> <salida.json>
"""
import sys, io, os, json, re, collections
from datetime import date, timedelta, datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MAIN, BASE, D2, D4, UNION, OUT = sys.argv[1:7]
sys.path.insert(0, MAIN)
sys.path.insert(0, os.path.join(MAIN, "scripts"))
OUT = os.path.abspath(OUT)   # la salida va a la carpeta desde donde se llama, no a la instantanea del codigo
os.chdir(MAIN)
import vigilancia_sombra as vs
import banco_paridad as bp
import referencia_mirova_unificada as rmu
aa = vs.aa
PROD = Path(BASE) / "data" / "mirova_equivalent"
CONS = os.path.join(BASE, "latest_consolidado.csv")
OCR = os.path.join(BASE, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")
HIST = Path(BASE) / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv"
RESP = Path(BASE) / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv"
PAT = re.compile(r"^trozo-(?P<v>[A-Za-z]+)-(?P<i>\d+)-(?P<a>\d{4}-\d\d-\d\d)_(?P<b>\d{4}-\d\d-\d\d)-intento-(?P<n>\d+)$")
VENTANAS = {"R25": ("2025-02-15", "2025-12-31"), "F26": ("2026-02-01", "2026-03-31"), "DM": ("2026-10-01", "2026-10-16")}
FAMS = ("MODIS", "VIIRS375", "VIIRS750")


def fam(s):
    s = str(s or "")
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def minuto(r):
    return r["dt"].strftime("%Y-%m-%d %H:%M")


# 1. union D2 + D4: intento mas alto de cada trozo, solo records dentro de la ventana del trozo (reglas 2.2 del plan)
trozos = collections.defaultdict(dict)
for carpeta in (D2, D4):
    for p in Path(carpeta).iterdir():
        m = PAT.match(p.name)
        if m:
            trozos[(m["v"], m["a"], m["b"])][int(m["n"])] = p / (m["v"] + ".json")
union = collections.defaultdict(dict)
dias_cubiertos = collections.defaultdict(set)
dup = 0
proc = collections.defaultdict(list)
marcas = collections.Counter()
perfiles = collections.Counter()
for (v, a, b), ints in sorted(trozos.items()):
    d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
    dias_cubiertos[v] |= {(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)}
    for r in json.loads(ints[max(ints)].read_text(encoding="utf-8"))["records"]:
        if not (a <= (r.get("datetime_utc") or "")[:10] <= b):
            continue
        k = (r["datetime_utc"], r["sensor"])
        dup += k in union[v]
        union[v][k] = r
        f = fam(r["sensor"])
        marcas[(f, str(r.get("via_codigo_mirova")))] += 1
        perfiles[(r.get("regimen") or {}).get("perfil")] += 1
        if r.get("processed_utc"):
            proc[f].append(str(r["processed_utc"]))
os.makedirs(UNION, exist_ok=True)
for v in bp.VOLS:
    recs = sorted(union.get(v, {}).values(), key=lambda r: r["datetime_utc"])
    with open(os.path.join(UNION, v + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"volcano": v, "records": recs}, fh)
n_union = sum(len(x) for x in union.values())
print(f"UNION D2+D4: {n_union} records en {len(union)} volcanes; {len(trozos)} trozos; claves repetidas entre trozos: {dup}")
print("  marcas por familia:", {a + "|" + b: n for (a, b), n in sorted(marcas.items())})
print("  regimen.perfil:", dict(perfiles))
for f in FAMS:
    print(f"  processed_utc de la via, {f}: de {min(proc[f])} a {max(proc[f])}")

# 2. pasadas K de produccion (438a60a1e) sin par en la union, en los dias cubiertos
sin_par = collections.defaultdict(set)
n_op = collections.Counter()
solo_via = collections.Counter()
for v in bp.VOLS:
    recs = json.loads((PROD / (v + ".json")).read_text(encoding="utf-8"))["records"]
    opk = set()
    for r in recs:
        if (r.get("datetime_utc") or "")[:10] in dias_cubiertos[v]:
            k = (r["datetime_utc"], r["sensor"])
            opk.add(k)
            n_op[fam(r["sensor"])] += 1
            if k not in union[v]:
                sin_par[v].add(k)
    for k in union[v]:
        if k not in opk:
            solo_via[fam(k[1])] += 1
tot_sp = collections.Counter(fam(k[1]) for v in sin_par for k in sin_par[v])
print("\nPASADAS K SIN PAR en la via (dias de D2 y D4), por familia:", dict(tot_sp), " [control (a): el plan dice MODIS 217]")
print("  sobre pasadas operacionales:", dict(n_op))
print("  solo en la via:", dict(solo_via))

# 3. predicado del tablero y etiquetas
coords = aa._coords_por_volcan()
inner = bp.inner_desde_html()
filas = rmu.cargar_referencia_unificada(CONS, OCR, respaldo_path=RESP, historico_path=HIST)
res = {"union_records": n_union, "sin_par_por_familia": dict(tot_sp), "operacionales_por_familia": dict(n_op),
       "solo_via_por_familia": dict(solo_via), "ventanas": {}}
perdidas_detalle = []


def medir(win, quitar=None):
    """quitar: (vol, datetime_utc, sensor) que se saca de la union (control positivo)."""
    bp.DATA = PROD
    prod = bp.cargar_nuestros(coords, inner, win)
    udir = UNION
    if quitar:
        udir = UNION + "_ctrl"
        os.makedirs(udir, exist_ok=True)
        for v in bp.VOLS:
            with open(os.path.join(UNION, v + ".json"), encoding="utf-8") as fh:
                d = json.load(fh)
            if v == quitar[0]:
                d["records"] = [r for r in d["records"] if (r["datetime_utc"], r["sensor"]) != tuple(quitar[1:])]
            with open(os.path.join(udir, v + ".json"), "w", encoding="utf-8") as fh:
                json.dump(d, fh)
    via = bp.cargar_nuestros(coords, inner, win, data=udir)
    prod = [r for r in prod if r["noche"] in dias_cubiertos[r["vol"]]]
    pasadas = vs.pasadas_de_alerta(filas, prod, via, win)
    pasadas = [p for p in pasadas if p["fecha_utc"][:10] in dias_cubiertos[p["volcano"]]]
    return prod, via, pasadas


for nombre, win in VENTANAS.items():
    prod, via, pasadas = medir(win)
    fila = {"ventana": win}
    viak = {(r["vol"], minuto(r), r["sensor"]): r for r in via}
    for f in FAMS:
        pf = [r for r in prod if r["b"] == f]
        sp = [r for r in pf if (minuto(r), r["sensor"]) in sin_par[r["vol"]]]
        com = [(r, viak[(r["vol"], minuto(r), r["sensor"])]) for r in pf if (r["vol"], minuto(r), r["sensor"]) in viak]
        al = [p for p in pasadas if p["sensor"] == f]
        prot = [p for p in al if p["protegida"]]
        d = {"pasadas_K_nocturnas": len(pf), "K_publica": sum(r["pub"] for r in pf),
             "sin_par": len(sp), "sin_par_que_K_publica": sum(r["pub"] for r in sp),
             "sin_par_publicadas_detalle": [[r["vol"], minuto(r), r["sensor"], round(r.get("disp") or 0, 3)] for r in sp if r["pub"]],
             "comunes": len(com), "comunes_K_publica_via_no": sum(1 for a, b in com if a["pub"] and not b["pub"]),
             "comunes_via_publica_K_no": sum(1 for a, b in com if b["pub"] and not a["pub"]),
             "alertas_mirova": len(al), "protegidas": len(prot),
             "protegidas_K_publica": sum(1 for p in prot if p["prod_pub"] is True),
             "protegidas_via_publica": sum(1 for p in prot if p["sombra_pub"] is True),
             "protegidas_K_publica_y_via_calla": [[p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]] for p in prot
                                                  if p["prod_pub"] is True and p["sombra_pub"] is False],
             "protegidas_K_publica_y_via_sin_record": [[p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]] for p in prot
                                                       if p["prod_pub"] is True and p["sombra_pub"] is None],
             "protegidas_via_publica_y_K_no": sum(1 for p in prot if p["sombra_pub"] is True and p["prod_pub"] is not True),
             "no_protegidas_K_publica_y_via_no": sum(1 for p in al if not p["protegida"] and not p["minima"]
                                                     and p["prod_pub"] is True and p["sombra_pub"] is not True),
             "no_protegidas_via_publica_y_K_no": sum(1 for p in al if not p["protegida"] and not p["minima"]
                                                     and p["sombra_pub"] is True and p["prod_pub"] is not True)}
        fila[f] = d
        perdidas_detalle += [(nombre, f, *x) for x in d["protegidas_K_publica_y_via_calla"] + d["protegidas_K_publica_y_via_sin_record"]]
    res["ventanas"][nombre] = fila
    print(f"\n== {nombre} {win[0]} a {win[1]} ==")
    for f in FAMS:
        d = fila[f]
        print(f"  {f}: pasadas K nocturnas {d['pasadas_K_nocturnas']} (K publica {d['K_publica']}); sin par {d['sin_par']}, de ellas K publica {d['sin_par_que_K_publica']}")
        print(f"      comunes {d['comunes']}: K publica y la via no {d['comunes_K_publica_via_no']}; la via publica y K no {d['comunes_via_publica_K_no']}")
        print(f"      alertas de MIROVA {d['alertas_mirova']}, protegidas {d['protegidas']}: K publica {d['protegidas_K_publica']}, la via publica {d['protegidas_via_publica']}; "
              f"K publica y la via calla {len(d['protegidas_K_publica_y_via_calla'])}; K publica y la via sin record {len(d['protegidas_K_publica_y_via_sin_record'])}; "
              f"la via publica y K no {d['protegidas_via_publica_y_K_no']}")
        print(f"      alertas no protegidas (sobre 0,05 MW): K publica y la via no {d['no_protegidas_K_publica_y_via_no']}; la via publica y K no {d['no_protegidas_via_publica_y_K_no']}")
        for x in d["sin_par_publicadas_detalle"][:15]:
            print("        sin par que K publica:", x)

print("\nPROTEGIDAS que hoy se publican y el reemplazo dejaria sin publicar (todas las ventanas):", perdidas_detalle or "ninguna")

# 4. control positivo (b): quitar de la union un record de la via de una pasada protegida que K publica
cand = None
prod, via, pasadas = medir(VENTANAS["F26"])
for p in pasadas:
    if p["protegida"] and p["prod_pub"] is True and p["sombra_pub"] is True:
        t = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S")
        vrec = [r for r in via if r["vol"] == p["volcano"] and r["b"] == p["sensor"]
                and abs((r["dt"].replace(tzinfo=None) - t).total_seconds()) <= bp.TOL_S]
        if len(vrec) == 1:
            cand = (p, (p["volcano"], minuto(vrec[0]), vrec[0]["sensor"]))
            break
if cand:
    p0, clave = cand
    _, _, pasadas2 = medir(VENTANAS["F26"], quitar=clave)
    antes = sum(1 for p in pasadas if p["protegida"] and p["prod_pub"] is True and p["sombra_pub"] is None)
    despues = sum(1 for p in pasadas2 if p["protegida"] and p["prod_pub"] is True and p["sombra_pub"] is None)
    ok = despues == antes + 1
    print(f"\nCONTROL POSITIVO (b): quitado de la union el record de la via {clave} (protegida de MIROVA {p0['vrp_mirova_mw']} MW). "
          f"K publica y la via sin record, en F26: {antes} -> {despues}. {'OK, la medicion lo ve' if ok else 'FALLA'}")
    res["control_positivo"] = {"clave": clave, "antes": antes, "despues": despues, "ok": ok}
else:
    print("\nCONTROL POSITIVO (b): SIN DATO, no hubo candidata")
    res["control_positivo"] = None
res["processed_utc_via"] = {f: [min(proc[f]), max(proc[f])] for f in proc}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, ensure_ascii=False, default=str)
