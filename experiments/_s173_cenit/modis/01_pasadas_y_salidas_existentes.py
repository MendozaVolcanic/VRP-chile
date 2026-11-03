# -*- coding: utf-8 -*-
"""01 (S173, cenit MODIS de Chillán): lista de pasadas MODIS de Chillán con alerta de MIROVA y partición por cenit de
las salidas que YA existen (K de producción y brazo V del A/B de MOD-D, y la ablación del bow tie de S162).

POR QUE: antes de preparar una ablación nueva hay que saber (a) qué pasadas son, con su gránulo, su cenit y el VRP de
MIROVA, para que el workflow las pida por nombre; (b) si las salidas existentes ya contestan qué pieza corrige la caída
oblicua. La razón es VRP publicado / VRP de MIROVA en la MISMA pasada (pareo de s02 de S172, ±120 s).

Insumos: s02_v_main_pasadas.csv (s02 de S172 corrido sobre origin/main de hoy, ventana 2026-04-01 a 2026-11-02),
el JSON de records de Chillán de esa copia (gránulo, product_version, régimen), modd_resultado_f4.json (lectura del A/B
de MOD-D copiada de origin/loop/activo, sha256 312e2050...), s162_03_ablacion.json y objetivos_neg_resto_modis.json.

P1 (si lo medido estuviera roto, ¿se vería?): el Spearman de K tiene que reproducir el de S172 (-0,867, n 12) en su
    ventana; control positivo: una razón construida como cos(z) tiene que dar Spearman -1.
P2 (instrumento muerto): barajado del cenit dentro del sensor (200, semilla 173); un Spearman dentro del rango barajado
    no es dependencia. Un tramo sin pares se informa como SIN DATO, no como razón 0.
Uso: python -B 01_pasadas_y_salidas_existentes.py <raiz copia main>
"""
import csv, json, math, random, statistics, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1])
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def rango(v):
    o = sorted(v)
    n = len(o)
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and o[j + 1] == o[i]:
            j += 1
        for k in range(i, j + 1):
            r[k] = (i + j) / 2.0
        i = j + 1
    pos = {}
    for k, x in enumerate(o):
        pos.setdefault(x, []).append(r[k])
    return [statistics.mean(pos[x]) for x in v]


def spearman(a, b):
    if len(a) < 3:
        return None
    ra, rb = rango(a), rango(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def con_barajado(z, r, n=200, semilla=173):
    rho = spearman(r, z)
    rng = random.Random(semilla)
    bs = []
    for _ in range(n):
        zz = z[:]
        rng.shuffle(zz)
        s = spearman(r, zz)
        if s is not None:
            bs.append(s)
    bs.sort()
    lo, hi = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if bs else (None, None)
    return rho, lo, hi


def med(x):
    x = [v for v in x if v is not None]
    return round(statistics.median(x), 3) if x else None


def tramos(pares, clave_r):
    a = [p[clave_r] for p in pares if p["z"] < 30]
    b = [p[clave_r] for p in pares if p["z"] >= 30]
    return {"z<30": {"n": len(a), "mediana": med(a)}, "z>=30": {"n": len(b), "mediana": med(b)}}


salida = {}
# ------------------------------------------------------------------ control positivo del Spearman
zs = [2, 10, 20, 35, 50, 58, 63]
pr("== control positivo: razón = cos(z), Spearman", round(spearman([math.cos(math.radians(z)) for z in zs], zs), 3),
   "(tiene que ser -1)")

# ------------------------------------------------------------------ pasadas MODIS con alerta (s02 sobre main)
recs = json.load(open(RAIZ / "data/mirova_equivalent/NevadosDeChillan.json", encoding="utf-8"))["records"]
por = {(r["sensor"], r["datetime_utc"]): r for r in recs}
filas = [f for f in csv.DictReader(open(AQUI / "s02_v_main_pasadas.csv", encoding="utf-8")) if f["b"] == "MODIS"]
alertas = [f for f in filas if f["vrp_M"] not in ("", "None")]
pr(f"\n== pasadas MODIS nocturnas de Chillán en s02_v_main (2026-04-01 a 2026-11-02): {len(filas)}; con alerta de "
   f"MIROVA (lectura A, D-9 SN, ±120 s): {len(alertas)}")
lista = []
for f in sorted(alertas, key=lambda x: x["dt"]):
    r = por.get((f["sensor"], f["dt"]), {})
    disp = float(f["disp"]) if f["disp"] not in ("", "None") else 0.0
    pub = int(f["pub"] in ("1", "True"))
    vm = float(f["vrp_M"])
    reg = r.get("regimen") or {}
    e = {"dt": f["dt"], "sensor": f["sensor"], "z": round(float(f["z"]), 2), "vrp_mirova_mw": vm, "fuente_M": f["src_M"],
         "pub_K": pub, "disp_mw": disp, "razon": round(disp / vm, 4) if pub and vm > 0 else None,
         "granule": r.get("granule"), "product_version": r.get("product_version"),
         "via_codigo_mirova": r.get("via_codigo_mirova"), "codigo_sha": reg.get("codigo_sha"),
         "processed_utc": r.get("processed_utc"), "n_anomalous_pixels": r.get("n_anomalous_pixels"),
         "pc_vrp_mw": (r.get("primary_cluster") or {}).get("vrp_mw")}
    lista.append(e)
    pr(f"  {e['dt']} {e['sensor']:11s} z {e['z']:5.1f}  MIROVA {vm:7.3f} ({e['fuente_M']})  pub {pub} disp {disp:7.3f} "
       f"razon {e['razon']}  via {e['via_codigo_mirova']}  {e['granule']} ({e['product_version']}) sha {str(e['codigo_sha'])[:9]}")
salida["pasadas"] = lista

# ------------------------------------------------------------------ K por cenit, dos ventanas
for nombre, fin in (("ventana S172 (2026-04-01 a 2026-10-26)", "2026-10-26 23:59"), ("hasta 2026-11-02", "9999")):
    pares = [p for p in lista if p["razon"] is not None and p["dt"] <= fin and p["via_codigo_mirova"] is not True]
    z, rz = [p["z"] for p in pares], [p["razon"] for p in pares]
    rho, lo, hi = con_barajado(z, rz)
    t = tramos(pares, "razon")
    perd = [p for p in lista if p["dt"] <= fin and not p["pub_K"] and p["via_codigo_mirova"] is not True]
    pr(f"\n== K, {nombre}: pares {len(pares)}; Spearman razón vs cenit {None if rho is None else round(rho, 3)} "
       f"(barajado 95 % [{None if lo is None else round(lo, 3)}; {None if hi is None else round(hi, 3)}]); "
       f"z<30 n {t['z<30']['n']} mediana {t['z<30']['mediana']}; z>=30 n {t['z>=30']['n']} mediana {t['z>=30']['mediana']}")
    pr(f"   alertas sin publicar: {len(perd)}: " + ", ".join(f"{p['dt']} z {p['z']} M {p['vrp_mirova_mw']}" for p in perd))
    salida[f"K {nombre}"] = {"n": len(pares), "spearman": rho, "barajado": [lo, hi], "tramos": t,
                             "sin_publicar": [(p["dt"], p["z"], p["vrp_mirova_mw"]) for p in perd]}
mods = [p for p in lista if p["via_codigo_mirova"] is True]
pr(f"\n== records de producción ya escritos por la vía MOD-D entre las alertas: {len(mods)}")

# ------------------------------------------------------------------ salida existente 1: brazo V del A/B de MOD-D
md = json.load(open(AQUI / "modd_resultado_f4.json", encoding="utf-8"))["chillan"]
pv = [{"dt": p["dt"], "z": p["z"], "rb": p["razon_b"], "rk": p["razon_k"]} for p in md["pares"]]
pv_rec = [{"dt": p["dt"], "z": p["z"], "rb": p["razon"]} for p in md["recuperadas"]]
for nombre, conj in (("pares K y V (12)", pv), ("pares + recuperadas por V (16)", pv + pv_rec)):
    z, rb = [p["z"] for p in conj], [p["rb"] for p in conj]
    rho, lo, hi = con_barajado(z, rb)
    t = tramos(conj, "rb")
    pr(f"\n== MOD-D brazo V (lectura del A/B, {nombre}): Spearman razón vs cenit {round(rho, 3)} (barajado "
       f"[{round(lo, 3)}; {round(hi, 3)}]); z<30 n {t['z<30']['n']} mediana {t['z<30']['mediana']}; "
       f"z>=30 n {t['z>=30']['n']} mediana {t['z>=30']['mediana']}")
    salida[f"V {nombre}"] = {"spearman": rho, "barajado": [lo, hi], "tramos": t}
z, rk = [p["z"] for p in pv], [p["rk"] for p in pv]
rho, lo, hi = con_barajado(z, rk)
pr(f"   control: K de la misma lectura sobre los 12: Spearman {round(rho, 3)} (barajado [{round(lo, 3)}; {round(hi, 3)}])"
   f"; z<30 {tramos(pv, 'rk')['z<30']}; z>=30 {tramos(pv, 'rk')['z>=30']}")
pr("   cociente V/K por pasada, ordenado por cenit (la ganancia que el paquete entero da sobre K):")
for p in sorted(pv, key=lambda x: x["z"]):
    pr(f"     {p['dt']} z {p['z']:5.1f}  V/K {p['rb'] / p['rk']:6.2f}")
zz, g = [p["z"] for p in pv], [p["rb"] / p["rk"] for p in pv]
rho, lo, hi = con_barajado(zz, g)
pr(f"   Spearman (V/K) vs cenit {round(rho, 3)} (barajado [{round(lo, 3)}; {round(hi, 3)}])")
salida["V/K"] = {"spearman": rho, "barajado": [lo, hi]}

# ------------------------------------------------------------------ salida existente 2: bow tie S162
ab = json.load(open(AQUI / "s162_03_ablacion.json", encoding="utf-8"))
obj = {o["id"]: o for o in json.load(open(AQUI / "objetivos_neg_resto_modis.json", encoding="utf-8"))}
ch = [int(i) for i in ab if obj[int(i)]["volcan"] == "NevadosDeChillan"]
chd = [i for i in ch if ab[str(i)]["todos"]["npix"]]
pr(f"\n== ablación del bow tie S162 (03_ablacion.json): {len(ab)} pasadas; de Chillán {len(ch)}; de Chillán con "
   f"detección del port {len(chd)}")
for i in sorted(chd, key=lambda i: obj[i]["z"]):
    o, a = obj[i], ab[str(i)]
    pr(f"  id {i} {o['hora_utc']} z {o['z']:.1f} protegida {o['protegida']} MIROVA {o['mirova_vrp']} port todos "
       f"{a['todos']['vrp_mw']:.3f} | A_ant {a['A_centro_cubierto_ant']['vrp_mw']:.3f} | A_sig "
       f"{a['A_centro_cubierto_sig']['vrp_mw']:.3f}")
zc = sorted(obj[i]["z"] for i in ch)
pr(f"  cenit de las {len(ch)} pasadas de Chillán del lote: min {zc[0]:.1f} mediana {statistics.median(zc):.1f} "
   f"max {zc[-1]:.1f}; bajo 30°: {sum(z < 30 for z in zc)}")
salida["bowtie_s162_chillan"] = {"n": len(ch), "con_deteccion": len(chd), "bajo_30": sum(z < 30 for z in zc)}

json.dump(salida, open(AQUI / "01_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
(AQUI / "01_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
