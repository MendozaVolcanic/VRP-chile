# -*- coding: utf-8 -*-
"""Verificador VC, S179. vc03: mediciones por afirmacion sobre la tabla por pasada de vc02 (filas.pkl), con las
funciones del propio lector (worktree s178-retro-lectura) donde la vara es el lector, y con codigo propio donde la
afirmacion dice que el lector no calcula algo.

Cada bloque imprime su encabezado con: que mide, denominador y ventana, y su control.
PREGUNTAS DEL INSTRUMENTO (comunes). (1) Si lo medido estuviera roto, lo veria? Cada bloque tiene un control positivo
propio (abajo). (2) Si el instrumento estuviera muerto? Todo bloque con denominador 0 lo imprime como SIN DATO y no
como cero.
Uso: python vc03_analisis.py [N_SORTEOS]
"""
import collections, copy, importlib.util, math, pickle, statistics, sys
from datetime import timedelta
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s178-lectura")
TMP = Path("D:/vrp-trabajo/temporales/s179-audit/vc")
N_SORTEOS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
spec = importlib.util.spec_from_file_location("leer_retro_vc", W / "experiments/_s172_retro_paquete/leer_retro.py")
LR = importlib.util.module_from_spec(spec)
sys.modules["leer_retro_vc"] = LR
spec.loader.exec_module(LR)
R = LR.Reglas()
F4 = R.F4
D = pickle.load(open(TMP / "filas.pkl", "rb"))
filas, osf_filas, osf_res, res = D["filas"], D["osf_filas"], D["osf_res"], D["res"]
BRAZO = {"MODIS": "V", "VIIRS375": "V-cercano", "VIIRS750": "V"}


def dec(s):
    return [f for f in filas if f["b"] == s and f["tramo"] == LR.TRAMO_DECIDE[s]]


def h(t):
    print("\n" + "=" * 100 + "\n" + t)


# ---------------------------------------------------------------- 0. control: la tabla es la de la lectura
h("0. CONTROL: veredictos de la tabla re-corrida (deben ser los de lectura_salida.txt)")
for s in LR.SENSORES:
    print(f"  {s}: fila {res[s]['fila']} | {res[s]['veredicto'][:80]} | motivos {res[s]['motivos']} | regla p2 "
          f"{res[s]['regla'].get('p2')} B {res[s]['regla'].get('B')} neto {res[s]['regla'].get('neto')}")

# ---------------------------------------------------------------- 501 / DEC-2
h("501. Perdidas solo OCR que K publica en F26-V VIIRS 375, con y sin la exencion N-3 (L4), brazo cercano y radiante."
  "\n   Denominador: pasadas evaluables de VIIRS 375 en F26-V (2026-02-01 a 03-31, noche). Control: la funcion del"
  "\n   lector con n3=True tiene que dar lo que trae lectura.json (extra.solo_ocr_que_k_publica).")
f375 = dec("VIIRS375")
print("  pasadas evaluables:", len(LR._ev(f375)), "| con lab_union protegida y lab de la tabla no:",
      sum(1 for f in LR._ev(f375) if f.get("lab_union") == "protegida" and f["lab"] != "protegida"))
for b in ("V-cercano", "V"):
    for n3 in (True, False):
        print(f"  brazo {b}, n3={n3}: {LR.solo_ocr_perdidas(f375, b, n3=n3)}")
print("  lectura.json extra.solo_ocr_que_k_publica (VIIRS375):", res["VIIRS375"]["extra"]["solo_ocr_que_k_publica"])
for f in LR._ev(f375):
    if f.get("lab_union") == "protegida" and f["lab"] != "protegida":
        print("   ", f["vol"], f["sensor"], f["dt"], "lab tabla", f["lab"], "vrp OCR", f.get("vrp_mirova_union"),
              "| pub K", LR._pub(f, "K"), "cercano", LR._pub(f, "V-cercano"), "radiante", LR._pub(f, "V"),
              "| es_n3", LR.es_n3(f))
# misma cuenta en VIIRS 750 (L4 tambien aplica alli)
f750 = dec("VIIRS750")
for n3 in (True, False):
    print(f"  VIIRS750 brazo V, n3={n3}: {LR.solo_ocr_perdidas(f750, 'V', n3=n3)}")
# veredicto del sensor 375 con la letra del §4.1 (sin exencion): se simula la fila 4
for b in ("V-cercano", "V"):
    sin = LR.solo_ocr_perdidas(f375, b, n3=False)
    print(f"  con la letra del §4.1 (sin N-3), brazo {b}: fila 4 por «perdida solo OCR que K publica» = {bool(sin)}")

# ---------------------------------------------------------------- 502
h("502. P2 de VIIRS 750 (brazo radiante) y de MODIS con y sin las pasadas del §3.1 (b). Ventana F26 que decide."
  "\n   Control: con todas las pasadas tiene que dar el B y el estado de lectura.json.")
for s in ("VIIRS750", "MODIS", "VIIRS375"):
    fs = dec(s)
    sb = [f for f in fs if not LR.es_pasada_b(f)]
    p, q = F4.p2(fs, BRAZO[s]), F4.p2(sb, BRAZO[s])
    print(f"  {s}: con (b) {p['estado']} B {p['B']} neto {p['neto']} | sin (b) {q['estado']} B {q['B']} neto {q['neto']} "
          f"| pasadas (b) quitadas {len(fs) - len(sb)} | lectura.json: fila con {res[s]['fila']}, regla_sin_pasadas_b "
          f"{res[s]['regla_sin_pasadas_b']}")
print("  claves de lectura.json que mencionan (b):", [k for k in res["VIIRS750"] if "b" in k.split("_")[-1:] or "pasadas_b" in k],
      "| extra:", {k: v for k, v in res["VIIRS750"]["extra"].items() if "pasadas_b" in k})

# ---------------------------------------------------------------- 503 / DEC-3
h("503. Sorteo del §7 con la via contra K (decision 2 de S174), estratos volcan x tramo de 10° de cenit, barajador"
  f"\n   del propio lector (barajar_en_estratos), {N_SORTEOS} sorteos, semilla 172. Brazo: el que decide."
  "\n   Control negativo: K contra K barajado da SIN SUSTRATO siempre. Control positivo: sin barajar reproduce el P2 de la lectura.")
for s in LR.SENSORES:
    fs = dec(s)
    b = BRAZO[s]
    obs = F4.p2(fs, b)
    rng = np.random.default_rng(LR.SEMILLA)
    c, netos, kk = collections.Counter(), [], collections.Counter()
    for _ in range(N_SORTEOS):
        x = LR.barajar_en_estratos(fs, rng)
        r = F4.p2(x, b)
        c[r["estado"]] += 1
        netos.append(r["neto"])
        kk[F4.p2(x, "K")["estado"]] += 1
    netos = np.array(netos)
    print(f"  {s} ({b}): observado {obs['estado']} B {obs['B']} neto {obs['neto']} | barajados {dict(c)} | GANA "
          f"{100 * c['GANA'] / N_SORTEOS:.1f} % | GANA o EMPATE {100 * (c['GANA'] + c['EMPATE']) / N_SORTEOS:.1f} % | "
          f"neto <= observado {int((netos <= obs['neto']).sum())} de {N_SORTEOS} | K contra K {dict(kk)}")
    if s == "VIIRS375":
        rng = np.random.default_rng(LR.SEMILLA)
        c2 = collections.Counter(F4.p2(LR.barajar_en_estratos(fs, rng), "V")["estado"] for _ in range(N_SORTEOS))
        print(f"     mismo sorteo con radiante (V): {dict(c2)} | GANA {100 * c2['GANA'] / N_SORTEOS:.1f} %")

# ---------------------------------------------------------------- 504
h("504. Cobertura del K-gemelo (D3) sobre las pasadas discordantes de P2 (las que deciden). Ventana F26 que decide."
  "\n   Control: el conteo de discordantes es el B y neto del P2 de la lectura (bloques).")
for s in LR.SENSORES:
    fs = dec(s)
    disc = F4.p2(fs, BRAZO[s])["discordantes"]
    clave = {(f["vol"], f["dt"]): f for f in fs}
    cub = [d for d in disc if clave[(d["vol"], d["dt"])].get("en_kgemelo")]
    bl = {d["bloque"] for d in disc}
    blc = {d["bloque"] for d in cub}
    print(f"  {s}: pasadas discordantes {len(disc)}, cubiertas por el K-gemelo {len(cub)} | bloques {len(bl)}, con alguna "
          f"pasada cubierta {len(blc)} | volcanes de las cubiertas {sorted(collections.Counter(d['vol'] for d in cub).items())}")
    print(f"     pasadas del tramo cubiertas por el K-gemelo: {sum(1 for f in fs if f.get('en_kgemelo'))} de {len(fs)}")

# ---------------------------------------------------------------- 505
h("505. Efecto de las capas de la referencia (historia y respaldo, fuera del manifiesto) sobre las etiquetas de F26 y DM."
  "\n   Control positivo: la union con capas tiene mas filas que sin capas (se imprime).")
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
L = W / "experiments/_s178_lectura/_congelado"
con = cargar_referencia_unificada(L / "registro_vrp_consolidado.csv", L / "registro_vrp_ocr.csv")
sin = cargar_referencia_unificada(L / "registro_vrp_consolidado.csv", L / "registro_vrp_ocr.csv", respaldo_path=None,
                                  historico_path=None)
print("  filas de la referencia: con capas", len(con), "| sin capas", len(sin))
coords = bp._coords_por_volcan()
no_r25 = [dict(f) for f in filas if f["tramo"] != "R25"]
a = copy.deepcopy(no_r25)
for f in a:
    for kk_ in ("lab", "lab_union", "vrp_mirova", "vrp_mirova_union"):
        f.pop(kk_, None)
LR.etiquetar_tabla(a, sin, coords)
dif = [(f["vol"], f["b"], f["dt"], f0.get("lab"), f.get("lab")) for f, f0 in zip(a, no_r25) if f.get("lab") != f0.get("lab")]
difu = [1 for f, f0 in zip(a, no_r25) if f.get("lab_union", f.get("lab")) != f0.get("lab_union", f0.get("lab"))]
print(f"  pasadas fuera de R25: {len(no_r25)} | etiqueta de la tabla distinta sin capas: {len(dif)} | de la union: {len(difu)}")
print("   ", dif[:10])

# ---------------------------------------------------------------- 506
h("506. Curva de cenit en R25 contra el OSF (el lector no la calcula). Filas OSF nocturnas, class 1, dentro del radio"
  "\n   interno, pareadas a ±120 s con una pasada nuestra evaluable que publica en los dos brazos (via del brazo que decide"
  "\n   y K), VRP > 0. Ventana R25 2025-02-15 a 12-31. Spearman razon contra cenit nuestro, nulo de 200 barajados semilla 172."
  "\n   Control positivo: una razon fabricada que crece con el cenit da Spearman positivo.")
idx = collections.defaultdict(list)
for f in filas:
    if f["tramo"] == "R25" and f.get("_evaluable"):
        idx[(f["vol"], f["b"])].append(f)


def pares_osf(s, b, solo_prot):
    out = []
    for o in osf_filas:
        if o["b"] != s or not o["noche"] or o["class"] != 1 or o["dist_crater_km"] > o["inner"]:
            continue
        if solo_prot and o["vrp_w"] < 1e6:
            continue
        cand = [f for f in idx.get((o["vol"], s), []) if abs((LR._dt(f["dt"]) - o["dt"]).total_seconds()) <= 120]
        if not cand:
            continue
        f = cand[0]
        if LR._pub(f, b) and LR._pub(f, "K") and LR._mag(f, b) > 0 and LR._mag(f, "K") > 0 and o["vrp_w"] > 0 and f.get("z") is not None:
            out.append((float(f["z"]), LR._mag(f, b) / (o["vrp_w"] / 1e6), LR._mag(f, "K") / (o["vrp_w"] / 1e6), f["vol"]))
    return out


def sp(x, y):
    return LR._spearman(x, y)


for s in LR.SENSORES:
    for solo in (False, True):
        P = pares_osf(s, BRAZO[s], solo)
        if len(P) < 3:
            print(f"  {s} {'>=1 MW' if solo else 'todas'}: n {len(P)} SIN DATO")
            continue
        z = [p[0] for p in P]
        rng = np.random.default_rng(172)
        for nom, i in (("via", 1), ("K", 2)):
            y = [p[i] for p in P]
            rho = sp(z, y)
            nul = [abs(sp(z, list(rng.permutation(y)))) for _ in range(200)]
            tr = collections.defaultdict(list)
            for zz, yy in zip(z, y):
                tr[int(zz // 10) * 10].append(yy)
            print(f"  {s} {'>=1 MW' if solo else 'todas'} {nom}: n {len(P)} rho {rho:+.3f} (p95 del nulo |rho| "
                  f"{np.percentile(nul, 95):.3f}) | mediana por tramo de 10°: "
                  + ", ".join(f"{k}:{statistics.median(v):.2f}(n{len(v)})" for k, v in sorted(tr.items())))
        print(f"     volcanes: {sorted(collections.Counter(p[3] for p in P).items())}")
zc = [float(i) for i in range(30)]
print("  control positivo: Spearman de una razon creciente con el cenit =", round(sp(zc, [1 + q / 10 for q in zc]), 3))

# ---------------------------------------------------------------- 507
h("507. Bajo 1 MW del OSF en R25 (el §4.2 manda informarlas; el lector no las calcula). Fila OSF nocturna, class 1,"
  "\n   VRP < 1 MW, dentro del radio interno; en 375 con la regla SN por analogia (VRP > 0,05 MW). Publica = el brazo"
  "\n   pareado a ±120 s publica. Control: con VRP >= 1 MW el mismo codigo reproduce las protegidas de p1_osf.")


def bajo1(s, b, piso, techo=1e6):
    n = pub = 0
    vols = collections.Counter()
    sin_par = 0
    for o in osf_filas:
        if o["b"] != s or not o["noche"] or o["class"] != 1 or o["dist_crater_km"] > o["inner"]:
            continue
        if not (piso < o["vrp_w"] < techo):
            continue
        cand = [f for f in idx.get((o["vol"], s), []) if abs((LR._dt(f["dt"]) - o["dt"]).total_seconds()) <= 120]
        if not cand:
            sin_par += 1
            continue
        n += 1
        vols[o["vol"]] += 1
        pub += LR._pub(cand[0], b)
    return n, pub, sin_par, vols


for s, piso in (("VIIRS375", 0.05e6), ("VIIRS375", 0.0), ("MODIS", 0.0)):
    for b in sorted({BRAZO[s], "V", "K"}):
        n, p, sp_, v = bajo1(s, b, piso)
        print(f"  {s} piso {piso / 1e6:.2f} MW brazo {b}: {p} de {n} ({100 * p / n:.1f} %)" if n else f"  {s}: SIN DATO",
              f"| filas sin pasada evaluable {sp_} | volcanes {len(v)}")
n, p, sp_, v = bajo1("VIIRS375", "V", 1e6 - 1e-6, float("inf"))
print(f"  control (>= 1 MW, VIIRS 375, radiante): {p} de {n}; p1_osf del lector: protegidas "
      f"{osf_res['por_sensor']['VIIRS375']['protegidas']} pub_via(radiante) {osf_res['por_sensor']['VIIRS375']['pub_via']}")

# ---------------------------------------------------------------- 508
h("508. Noche del operador en F26-V: noches-volcan, cuantas tienen todas las pasadas evaluables, cuantas tienen una"
  "\n   pasada NOAA-21 y cuantas serian limpias sin exigir NOAA-21. Control: la funcion del lector reproduce lectura.json.")
for s in ("VIIRS375", "VIIRS750"):
    fs = [f for f in dec(s) if f["estado"] != "sobra_en_via"]
    por = collections.defaultdict(list)
    for f in fs:
        por[(f["vol"], f["noche"])].append(f)
    n_todas_ev = sum(1 for v in por.values() if all(f.get("_evaluable") for f in v))
    n21 = sum(1 for v in por.values() if any("NOAA21" in f["sensor"] for f in v))
    lab21 = collections.Counter(f["lab"] for f in fs if "NOAA21" in f["sensor"] and f.get("_evaluable"))
    limpia_sin21 = sum(1 for v in por.values() if all(f.get("_evaluable") for f in v)
                       and [f for f in v if "NOAA21" not in f["sensor"]]
                       and all(f["lab"] == "neg_limpio" for f in v if "NOAA21" not in f["sensor"]))
    print(f"  {s}: noches-volcan {len(por)} | todas evaluables {n_todas_ev} | con alguna pasada NOAA-21 {n21} | "
          f"etiquetas de NOAA-21 evaluables {dict(lab21)} | limpias sin contar NOAA-21 {limpia_sin21}")
    print(f"     lector noche_operador: {LR.noche_operador(fs, BRAZO[s])} | lectura.json: {res[s]['noche_operador']}")

# ---------------------------------------------------------------- 509
h("509. Volcanes del nombre de la fila 6 de VIIRS 375: protegidas de la tabla en F26-V por volcan y protegidas OSF por"
  "\n   volcan en R25. Control: nombre_fila6 del lector reproduce el nombre de la lectura.")
print("  F26-V protegidas (tabla) por volcan:", dict(collections.Counter(f["vol"] for f in LR._ev(f375) if f["lab"] == "protegida")))
print("  R25 OSF protegidas por volcan:", osf_res["por_sensor"]["VIIRS375"]["por_volcan"])
print("  nombre_fila6:", LR.nombre_fila6(f375, osf_res, "VIIRS375"))

# ---------------------------------------------------------------- 511
h("511. Control «el nulo de runner puede fallar»: se rompe el K-gemelo a proposito y se mira si el control cambia."
  "\n   Mutacion A: KG := la via (radiante). Mutacion B: KG publica todo. Si «puede fallar» sigue True y la mediana d"
  "\n   del placebo no cambia, el control no depende del K-gemelo.")
base = LR.nulo_runner(R, filas, [])
print("  sin mutar:", base)
for nom, fn in (("KG = via", lambda f: dict(f["_t"].get("V", {"pub": 0, "mag": 0.0}))),
                ("KG publica todo con magnitud de K", lambda f: {"pub": 1, "mag": f["_t"]["K"]["mag"] or 0.5})):
    mu = copy.deepcopy([f for f in filas if f.get("_evaluable") and "KG" in f["_t"]])
    for f in mu:
        f["_t"]["KG"] = fn(f)
    r = LR.nulo_runner(R, mu, [])
    print(f"  mutacion «{nom}»: estado {r['estado']} | B {r['B']} | B contra placebo {r['B_contra_placebo']} | mediana d "
          f"placebo {r['mediana_d_placebo']}")
print("  -log10(1,2) =", round(-math.log10(1.2), 4))
m_pl = F4.m([f for f in filas if f.get("_evaluable")], "placebo")
P = F4.pares_m([f for f in filas if f.get("_evaluable")], "placebo")
print(f"  pares de m del placebo en todas las filas evaluables: {len(P)}; con K bajo MIROVA/1,2: "
      f"{sum(1 for p in P if p['k'] < p['m'] / 1.2)}; mediana d {m_pl.get('mediana_d')}")

# ---------------------------------------------------------------- 513
h("513. M de MODIS en F26-M (brazo radiante) y del placebo K x 1,2: criterio d y d′ (D-28). Control: la regla de la"
  "\n   via es la de lectura.json.")
fm = dec("MODIS")
for b in ("V", "placebo"):
    mm = F4.m(fm, b)
    dp = mm.get("dprima") or {}
    print(f"  {b}: n {mm['n']} regla(d) {mm['regla']} IC d {mm.get('ic95_d')} mediana d {mm.get('mediana_d')} | d′: "
          + str({k: dp.get(k) for k in list(dp)[:8]}))
    print("     volcanes de los pares:", dict(collections.Counter(p["vol"] for p in F4.pares_m(fm, b))))
print("  lectura.json MODIS m:", res["MODIS"]["regla"].get("m"), "m_n", res["MODIS"]["regla"].get("m_n"))
pl = res["MODIS"]["controles"]["c_placebo"]
print("  control placebo de la lectura (MODIS):", {k: pl.get(k) for k in ("m_regla", "mejora_d28", "estado")})

# ---------------------------------------------------------------- 514
h("514. Alertas de la tabla sin pasada nuestra (lista de C-cobertura): ventana del lector y recorte a los tramos."
  "\n   Control: el total con la ventana del lector reproduce la suma de lectura.json.")
L2 = W / "experiments/_s178_lectura/_congelado"
tabla = [r for r in con if r["source"] == "CONS"]
no = [f for f in filas if f["tramo"] != "R25"]
ventana = (min(f["noche"] for f in no), max(f["noche"] for f in no))
por_vb, ns, nv, _ = bp.indexar_referencia(tabla, coords, ventana, regla_minimas="SN")
nuestros = collections.defaultdict(list)
for f in no:
    nuestros[(f["vol"], f["b"])].append(LR._dt(f["dt"]))
import clase_mirova as clase
vistos, lista = set(), []
for (vol, b), xs in por_vb.items():
    ts = nuestros.get((vol, b), [])
    for dt, r in xs:
        if not bp.es_alerta(r["tipo"]) or (vol, b, r["fecha_utc"][:16]) in vistos:
            continue
        vistos.add((vol, b, r["fecha_utc"][:16]))
        if not any(abs((t - dt).total_seconds()) <= bp.TOL_S for t in ts):
            lista.append((vol, b, r["fecha_utc"][:16], clase.alerta_protegida(r, lectura="A"), r.get("vrp_mw")))
print("  ventana del lector:", ventana, "| total sin pasada:", len(lista), "| suma en lectura.json:",
      sum(D["sin_pasada"].values()))


def en_tramo(x):
    d = x[2][:10]
    return any(LR.tramo_de(x[1], d) == t for t in ("F26-V", "F26-M", "F26-M3", "DM"))


ent = [x for x in lista if en_tramo(x)]
print("  dentro de F26 o DM:", len(ent), "| protegidas", sum(1 for x in ent if x[3]), "| lista:", ent[:20])
f26 = [x for x in ent if x[2][:10] <= "2026-03-31"]
print("  dentro de F26 solamente:", len(f26), "| protegidas", sum(1 for x in f26 if x[3]), f26)
fuera = [x for x in lista if not en_tramo(x)]
print("  fuera de todo tramo (abril a septiembre, etc.):", len(fuera), "| meses", dict(collections.Counter(x[2][:7] for x in fuera)))

# ---------------------------------------------------------------- 517
h("517. Cifras del §7 con el codigo y el K de la lectura (dispatch a7a6ae360, K e7cfbaf54): protegidas, bajo 1 MW y"
  "\n   bloques noche-volcan donde K yerra (bajo1 perdida o negativo limpio publicado). El §7 sellado dice: protegidas"
  "\n   9 / 26 / 30; bajo 1 MW 5 / 158 / 25; bloques donde K yerra 6 (+1 de la protegida perdida) / 48 / 18.")
for s in LR.SENSORES:
    fs = LR._ev(dec(s))
    prot = sum(1 for f in fs if f["lab"] == "protegida")
    bj = sum(1 for f in fs if f["lab"] == "bajo1")
    bl = {F4._bloque(f) for f in fs if (f["lab"] == "bajo1" and not LR._pub(f, "K"))
          or (f["lab"] == "neg_limpio" and LR._pub(f, "K"))}
    pk = [(f["vol"], f["dt"]) for f in fs if f["lab"] == "protegida" and not LR._pub(f, "K")]
    todas = dec(s)
    prot_all = sum(1 for f in todas if f["lab"] == "protegida")
    print(f"  {s}: protegidas evaluables {prot} (todas las pasadas del tramo {prot_all}) | bajo 1 MW {bj} | bloques donde K "
          f"yerra en P2 {len(bl)} | protegidas que K pierde {pk}")

# ---------------------------------------------------------------- nuevo: P1-OSF por brazo en VIIRS 375
h("NUEVO. P1-OSF de VIIRS 375 se calcula con el brazo radiante (p1_osf(filas, osf) sin brazo, l. 1436); el que decide"
  "\n   en 375 es cercano. Se repite con cercano. Control: con radiante reproduce osf_res de la lectura.")
for b in ("V", "V-cercano"):
    fil2 = copy.deepcopy(filas)
    r = LR.p1_osf(fil2, osf_filas, b)
    for s in LR.SENSORES:
        x = r["por_sensor"][s]
        print(f"  brazo {b} {s}: protegidas {x['protegidas']} pub_via {x['pub_via']} candidatas {len(x['candidatas'])} "
              f"{x['candidatas'][:5]} sin_record {len(x['sin_record'])} defecto {len(x['defecto'])}")
