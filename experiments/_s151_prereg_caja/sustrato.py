# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. SUSTRATO del A/B de la caja de 5 x 5 km (D18): en cuantas pasadas la caja PUEDE cambiar
algo, por brazo, sensor y volcan, sobre datos que ya estan en GitHub (las ramas de salida de los A/B de S147 a S151).

EL FENOMENO. La caja no inventa ni borra calor: cambia QUE UMBRAL se le aplica a cada pixel. Dentro de la caja de
5 x 5 km centrada en el ancla de deteccion rige el umbral permisivo de cumbre (C1 0,003, C2 5 de noche); fuera,
el estricto de escena (C1 0,010, C2 10). Hoy el permisivo rige en todo el circulo de `inner_radius_km` (3 a 20 km).
Asi que un pixel alertado solo puede verse afectado si esta DENTRO del circulo y FUERA de la caja (corona C-K):
ahi pasa del umbral permisivo al estricto. Y al reves, en la franja dentro de la caja pero fuera del circulo
(K-C: solo existe donde inner_radius_km < 3,54 km, la semidiagonal de la caja, o sea Lastarria y Planchon
Peteroa) el umbral se afloja.

LA CUENTA, POR PASADA PUBLICADA (predicado del tablero ejecutado con node, A97). Con los pixeles alertados del
record (`anomaly_pixels`, posicion por pixel):
  intacta    tiene al menos un pixel en C y K a la vez: ese pixel conserva el umbral permisivo, el cumulo de
             la cumbre sobrevive y la pasada sigue publicada (salvo un cambio de seleccion del cumulo, que solo
             el A/B mide). Si ademas tiene pixeles en C-K, la caja puede cambiar su MAGNITUD.
  expuesta   todos sus pixeles dentro del circulo estan en C-K: si ninguno pasa el umbral estricto, la pasada
             deja de publicarse. Es el UNICO caso donde la caja puede apagar una publicacion. Es un TECHO: cuantas
             sobreviven al umbral estricto no se puede saber sin el dNTI por pixel, que el record no guarda
             (S130 ya pago por confundir "donde cae" con "si sobrevive").
Y, sin publicar, las pasadas con pixeles alertados en K-C: alli la caja afloja, pero un cumulo a mas de 3 km
del ancla sigue fuera del gate del tablero (circulo), asi que solo cambia algo si se une a uno de la cumbre.

CONTROLES (A110: cada uno puede fallar, y se mide antes de leer el sustrato):
  C1 geometria, positivo: puntos uniformes alrededor de cada ancla, clasificados con la MISMA funcion que los
     pixeles (lat/lon a km como pipeline/scan_geometry.py::roi_mask_bbox, circulo por haversine como
     vent_dist_per_pixel); la fraccion en la caja de los que caen en el circulo tiene que dar el area teorica
     (caja dentro del circulo / circulo), calculada por otro camino (grilla en km). Tolerancia 2 % relativo.
  C2 reproduccion, puede fallar: con el brazo sin Test 1 del run 35521542153 y la referencia congelada de S146,
     los cumulos publicados fuera de la caja tienen que dar los seis numeros de
     experiments/_s148_caja_traza/origen_43_de_135_salida.txt, fila "centroide del cumulo, caja desde el ancla
     de deteccion": VIIRS 375 0/135 y 58/105, VIIRS 750 1/13 y 21/36, MODIS 0/1 y 15/39.
  C3 cero estructural, negativo: en los volcanes con inner_radius_km >= 3,6 ningun pixel puede estar en K-C
     (la semidiagonal de la caja es 3,54 km). Uno solo delata una caja y un circulo con centros distintos.
  C4 el inner del tablero (frontend/index.html) y el de volcanoes.yaml son el mismo para los 11 Tier A.

FUENTES. Brazos B (`_s146_ab_sin_test1`) y F (`_s147_ab_sin_test1_max`) de los runs mensuales de abril a
septiembre (codigo de septiembre, ya con #535), y C0, F y K del run de Nevados de Chillan (38560317428, la
erupcion). MODIS con F no sirve (con banda 21, `max` apaga el detector, S147), asi que el MODIS del candidato es
K (`_s149_ab_sin_test1_b22_max`): Lascar de marzo a junio y Chillan. Se leen con `git show` de la rama
`origin/s146-ab/<run>` a un cache local (nunca `git archive`, nunca el repo de los TIF).
REFERENCIA. Para septiembre y octubre, la congelada del pre-registro de F y K (`_s151_prereg_fk_11/_congelado_v1`,
con sus capas). Para abril a agosto, la union del repo; antes del 2026-06-13 decide la tabla sola (A119).

Uso: python sustrato.py [--cache DIR] > sustrato_salida.txt
"""
from __future__ import annotations

import argparse, collections, json, math, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1"),
           str(RAIZ / "experiments" / "_s148_caja")):
    sys.path.insert(0, _p)
import yaml  # noqa: E402
import evaluar as ev  # noqa: E402
import clase_mirova as cm  # noqa: E402
import lectura_caja as lc  # noqa: E402  (anclas() y en_caja(): la geometria de S148, igual a roi_mask_bbox)
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
bp = ev.bp

B, F, K, C0 = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max", "_s149_ab_sin_test1_b22_max", "_s146_ab_control"
SAL = "experiments/_s146_ab_sin_test1/salidas"
CONG_V1 = RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v1"
INICIO_OCR_DECIDE = "2026-06-13"   # A119
SENS = ("MODIS", "VIIRS375", "VIIRS750")
SEMIDIAGONAL = 2.5 * math.sqrt(2)

# (run, desde, hasta, brazos, volcanes o None = los 11, referencia: "union" o "v1")
FUENTES = [
    ("35639417826", "2026-04-01", "2026-04-30", (B, F), None, "union"),
    ("35599902448", "2026-05-01", "2026-05-31", (B, F), None, "union"),
    ("35675490175", "2026-06-01", "2026-06-30", (B, F), None, "union"),
    ("35728617326", "2026-07-01", "2026-07-31", (B, F), None, "union"),
    ("35759688167", "2026-08-01", "2026-08-27", (B, F), None, "union"),
    ("35548121381", "2026-09-01", "2026-09-18", (B, F), None, "v1"),
    ("38560317428", "2026-09-14", "2026-10-07", (C0, B, F, K), ("NevadosDeChillan",), "v1"),
    ("35632736532", "2026-03-01", "2026-03-31", (K,), ("Lascar",), "union"),
    ("35648804271", "2026-04-01", "2026-04-30", (K,), ("Lascar",), "union"),
    ("35671459235", "2026-05-01", "2026-05-31", (K,), ("Lascar",), "union"),
    ("35679063864", "2026-06-01", "2026-06-30", (K,), ("Lascar",), "union"),
]
# El job de Chaiten del brazo B de abril se repitio en 37823348991 (A108, S150); se usa la repeticion.
REPETICION = {("35639417826", B, "Chaiten"): "37823348991"}
# experiments/_s148_caja_traza/origen_43_de_135_salida.txt, fila "centroide del cumulo, caja desde el ancla".
ESPERADO_C2 = {("VIIRS375", "pos"): (0, 135), ("VIIRS375", "neg_limpio"): (58, 105),
               ("VIIRS750", "pos"): (1, 13), ("VIIRS750", "neg_limpio"): (21, 36),
               ("MODIS", "pos"): (0, 1), ("MODIS", "neg_limpio"): (15, 39)}


# ---------------------------------------------------------------- datos
def bajar(cache, run, brazo, vol):
    """El JSON de un brazo y volcan, desde la rama de salida del run. None si el run no lo tiene."""
    run_real = REPETICION.get((run, brazo, vol), run)
    dst = Path(cache) / run_real / brazo / (vol + ".json")
    if not dst.exists():
        r = subprocess.run(["git", "-C", str(RAIZ), "show", "origin/s146-ab/%s:%s/%s/%s/%s.json" % (run_real, SAL, run_real, brazo, vol)],
                           capture_output=True)
        if r.returncode != 0:
            return None
        dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(r.stdout)
    return dst


def armar_dir(cache, run, brazo, vols):
    """Directorio con <vol>.json de ese brazo (ev.cargar_brazo lee asi). Devuelve (dir, volcanes que faltan)."""
    d = Path(cache) / "_vista" / run / brazo; d.mkdir(parents=True, exist_ok=True); faltan = []
    for v in vols:
        src = bajar(cache, run, brazo, v)
        if src is None:
            faltan.append(v); continue
        (d / (v + ".json")).write_bytes(src.read_bytes())
    return d, faltan


def crudos(d, vols, desde, hasta):
    out = {}
    for v in vols:
        p = d / (v + ".json")
        if not p.exists():
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
            if b is not None and desde <= t[:10] <= hasta:
                out[(v, b, t[:16])] = r
    return out


def filas_ref(cual, solo_tabla, hist=True):
    if cual == "v1":
        filas = cargar_referencia_unificada(CONG_V1 / "registro_vrp_consolidado.csv", CONG_V1 / "registro_vrp_ocr.csv",
                                            historico_path=CONG_V1 / "consolidado_filas_perdidas.csv",
                                            respaldo_path=CONG_V1 / "respaldo_20260408.csv")
    elif cual == "s146":
        c = RAIZ / "experiments" / "_s146_ab_sin_test1" / "_congelado"
        kw = {} if hist else {"historico_path": None}
        filas = cargar_referencia_unificada(c / "registro_vrp_consolidado.csv", c / "registro_vrp_ocr.csv", **kw)
    else:
        filas = cargar_referencia_unificada()
    return [f for f in filas if f["source"] == "CONS"] if solo_tabla else filas


# ---------------------------------------------------------------- geometria (la misma funcion para pixeles y control)
def clase_pixel(lat, lon, ancla, inner):
    """'CK' en circulo y caja; 'C' solo circulo (corona donde la caja endurece); 'K' solo caja (donde afloja);
    'X' en ninguno. Caja: lectura_caja.en_caja (= roi_mask_bbox). Circulo: haversine al ancla (= vent_dist_per_pixel)."""
    en_k = lc.en_caja(lat, lon, ancla)
    en_c = ev._hav(lat, lon, ancla[0], ancla[1]) <= inner
    return ("CK" if en_k else "C") if en_c else ("K" if en_k else "X")


def area_teorica(inner, paso=0.005):
    """Fraccion del circulo cubierta por la caja, por otro camino que los puntos: si la caja entera cabe en el
    circulo (inner >= semidiagonal) es 25 / (pi inner^2); si no, grilla directa en km (sin lat/lon)."""
    if inner >= SEMIDIAGONAL:
        return 25.0 / (math.pi * inner * inner)
    n = int(inner / paso) + 1; dentro = en_caja = 0
    for i in range(-n, n + 1):
        x = i * paso
        for j in range(-n, n + 1):
            y = j * paso
            if x * x + y * y <= inner * inner:
                dentro += 1; en_caja += abs(x) <= 2.5 and abs(y) <= 2.5
    return en_caja / dentro


def control_c1(anclas, inner):
    import random
    rnd = random.Random(0); ok = True
    print("== C1. GEOMETRIA: fraccion del circulo que cae en la caja, puntos uniformes contra el area teorica")
    for v in bp.VOLS:
        a, R = anclas[v], inner[v]
        n_c = n_ck = 0
        for _ in range(40000):
            dy, dx = rnd.uniform(-R - 0.5, R + 0.5), rnd.uniform(-R - 0.5, R + 0.5)
            lat = a[0] + dy / 111.0; lon = a[1] + dx / (111.0 * math.cos(math.radians(a[0])))
            c = clase_pixel(lat, lon, a, R)
            n_c += c in ("C", "CK"); n_ck += c == "CK"
        obs, teo = n_ck / n_c, area_teorica(R)
        bien = abs(obs - teo) <= 0.02 * teo + 0.005
        ok &= bien
        print("   %-20s inner %4.1f km | observado %.4f | teorico %.4f | %s" % (v, R, obs, teo, "OK" if bien else "FALLA"))
    print("   C1:", "OK" if ok else "FALLA")
    return ok


def control_c2(cache, anclas, inner, coords):
    run, ventana = "35521542153", ("2026-09-01", "2026-09-20")
    d, faltan = armar_dir(cache, run, B, bp.VOLS)
    print("\n== C2. REPRODUCCION de origen_43_de_135 (run %s, brazo B, %s a %s; faltan %s)" % (run, ventana[0], ventana[1], faltan or "ninguno"))
    resultados = {}
    for etiqueta, hist in (("sin la capa historica (estado de S148)", False), ("con la capa historica (S150)", True)):
        filas = filas_ref("s146", False, hist=hist)
        por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
        recs = ev.cargar_brazo(d, coords, inner, ventana); bp.etiquetar(recs, por_vb, ns, nv)
        obt = {}
        for (s, lab) in ESPERADO_C2:
            sel = [r for r in recs if r["b"] == s and r["lab"] == lab and r["pub"] and r["pc_lat"] is not None]
            obt[(s, lab)] = (sum(not lc.en_caja(r["pc_lat"], r["pc_lon"], anclas[r["vol"]]) for r in sel), len(sel))
        resultados[etiqueta] = obt
        print("   %-40s %s | %s" % (etiqueta, " ".join("%s %s %d/%d" % (s, l[:3], *obt[(s, l)]) for s, l in ESPERADO_C2),
                                    "REPRODUCE" if obt == ESPERADO_C2 else "no reproduce"))
    ok = any(o == ESPERADO_C2 for o in resultados.values())
    print("   C2:", "OK (al menos una de las dos referencias reproduce los seis numeros)" if ok else "FALLA")
    return ok


# ---------------------------------------------------------------- cuenta
def anotar(recs, crudo, por_vb, anclas, inner):
    """A cada pasada: protegida (A y B), clases de sus pixeles, y su categoria para la caja."""
    for r in recs:
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        r["prot_A"] = any(cm.alerta_protegida(f, lectura="A") for f in filas)
        r["prot_B"] = any(cm.alerta_protegida(f, lectura="B") for f in filas)
        x = crudo.get((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M")))
        px = (x or {}).get("anomaly_pixels") or []
        cl = collections.Counter(clase_pixel(p["lat"], p["lon"], anclas[r["vol"]], inner[r["vol"]]) for p in px
                                 if p.get("lat") is not None)
        r["px"] = cl; r["trunc"] = len(px) >= 100
        if not r["pub"]:
            r["cat"] = "no_pub"
        elif cl["CK"]:
            r["cat"] = "intacta_mag" if cl["C"] else "intacta"
        elif cl["C"]:
            r["cat"] = "expuesta"
        else:
            r["cat"] = "pub_sin_px_en_circulo"


def grupo(r):
    """protegida_A; protegida_B (solo con la lectura B: VRP de 1 MW o mas en una fila que no es RUTINA, a cualquier
    distancia, asi que puede ser una pasada etiquetada far_ref); muy_bajo (alerta bajo el corte); neg_limpio; otras."""
    if r["prot_A"]:
        return "protegida_A"
    if r["prot_B"]:
        return "protegida_B"
    if r["lab"] == "pos":
        return "muy_bajo"
    return {"neg_limpio": "neg_limpio"}.get(r["lab"], "otras")


GRUPOS = ("protegida_A", "protegida_B", "muy_bajo", "neg_limpio", "otras")
CATS = ("intacta", "intacta_mag", "expuesta", "pub_sin_px_en_circulo")


def tabla(recs, clave, titulo, claves):
    c = collections.defaultdict(collections.Counter)
    for r in recs:
        k = clave(r)
        c[k]["pasadas"] += 1
        if r["pub"]:
            c[k]["pub|" + grupo(r)] += 1
            c[k]["%s|%s" % (r["cat"], grupo(r))] += 1
        c[k]["trunc"] += r["trunc"] and r["pub"]
        c[k]["reverso"] += (not r["pub"]) and r["px"]["K"] > 0
        c[k]["reverso_pub"] += r["pub"] and r["px"]["K"] > 0
    print("\n== " + titulo)
    print("   publicadas por grupo de MIROVA (pA protegida lectura A, pB solo lectura B, MB Muy Bajo, neg negativo limpio,")
    print("   otr sin_info/far_ref) y, de ellas, EXPUESTAS (todo su calor del circulo cae fuera de la caja: la caja puede")
    print("   apagarlas) y con MAGNITUD en juego (tienen calor dentro y fuera de la caja). rev: sin publicar con calor en K-C.")
    print("   %-28s %6s | %-24s | %-24s | %-24s | %4s %4s" % ("", "pasad", "publicadas pA/pB/MB/neg/otr", "EXPUESTAS pA/pB/MB/neg/otr",
                                                          "MAGNITUD pA/pB/MB/neg/otr", "trnc", "rev"))
    for k in claves:
        x = c.get(k, collections.Counter())
        f = lambda pref: "/".join("%d" % x["%s|%s" % (pref, g)] for g in GRUPOS)
        print("   %-28s %6d | %-24s | %-24s | %-24s | %4d %4d" % ("|".join(k) if isinstance(k, tuple) else k, x["pasadas"],
              f("pub"), f("expuesta"), f("intacta_mag"), x["trunc"], x["reverso"]))
    return c


def poder(n):
    if n == 0:
        return "n 0: el veto NO PUEDE FALLAR por esta via (ninguna protegida publicada esta expuesta)"
    return "n %d | fraccion de perdida detectable con 80 %% de probabilidad: %.1f %%" % (n, 100 * (1 - 0.2 ** (1 / n)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path(tempfile.gettempdir()) / "vrp_s151_caja_cache"))
    a = ap.parse_args()
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); anclas = lc.anclas()

    # C4
    cfg = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vs = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    inner_yaml = {(v.get("name") or v.get("id")): v.get("inner_radius_km") for v in (vs.values() if isinstance(vs, dict) else vs)}
    dif = {v: (inner[v], inner_yaml.get(v)) for v in bp.VOLS if inner[v] != inner_yaml.get(v)}
    ok4 = not dif
    print("== C4. inner del tablero contra volcanoes.yaml en los 11 Tier A:", "OK, iguales" if ok4 else "DIFIEREN %s" % dif)
    print("   inner por volcan: %s | semidiagonal de la caja %.2f km" % (", ".join("%s %g" % (v, inner[v]) for v in bp.VOLS), SEMIDIAGONAL))

    ok1 = control_c1(anclas, inner)
    ok2 = control_c2(a.cache, anclas, inner, coords)

    todos = []
    print("\n== DATOS (cada fuente con su ventana y su referencia)")
    for run, desde, hasta, brazos, vols, ref in FUENTES:
        vols = list(vols or bp.VOLS)
        tramos = [(desde, hasta)]
        if desde < INICIO_OCR_DECIDE <= hasta:   # A119: el tramo que decide la tabla sola, aparte
            tramos = [(desde, "2026-06-12"), (INICIO_OCR_DECIDE, hasta)]
        for brazo in brazos:
            d, faltan = armar_dir(a.cache, run, brazo, vols)
            for t0, t1 in tramos:
                solo_tabla = t0 < INICIO_OCR_DECIDE
                filas = filas_ref(ref, solo_tabla)
                por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (t0, t1))
                recs = [r for r in ev.cargar_brazo(d, coords, inner, (t0, t1)) if r["vol"] in vols]
                bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
                anotar(recs, crudos(d, vols, t0, t1), por_vb, anclas, inner)
                for r in recs:
                    r["brazo"], r["run"], r["mes"] = brazo, run, r["noche"][:7]
                todos += recs
                print("   run %s %-28s %s a %s | referencia %s%s | pasadas nocturnas %5d | faltan %s" % (
                    run, brazo, t0, t1, ref, " (solo tabla, A119)" if solo_tabla else "", len(recs), faltan or "-"))

    # C3: cero estructural
    malos = [(r["vol"], r["b"], str(r["dt"])) for r in todos if inner[r["vol"]] >= 3.6 and r["px"]["K"] > 0]
    ok3 = not malos
    print("\n== C3. pixeles en K-C en volcanes con inner >= 3,6 km: %d %s | %s" % (len(malos), malos[:5], "OK" if ok3 else "FALLA"))
    print("\n== CONTROLES: C1 %s | C2 %s | C3 %s | C4 %s" % (ok1, ok2, ok3, ok4))

    sel =lambda brazo, s: [r for r in todos if r["brazo"] == brazo and r["b"] == s and r["run"] != "38560317428"]
    for brazo, sensores in ((B, ("VIIRS375", "VIIRS750", "MODIS")), (F, ("VIIRS375", "VIIRS750"))):
        for s in sensores:
            rr = sel(brazo, s)
            tabla(rr, lambda r: (r["mes"],), "%s %s POR MES (runs mensuales, 11 Tier A)" % (brazo, s),
                  [(m,) for m in sorted({r["mes"] for r in rr})])
            tabla(rr, lambda r: (r["vol"],), "%s %s POR VOLCAN (abril a septiembre)" % (brazo, s), [(v,) for v in bp.VOLS])
    kl = [r for r in todos if r["brazo"] == K and r["b"] == "MODIS" and r["vol"] == "Lascar"]
    tabla(kl, lambda r: (r["mes"],), "K MODIS, LASCAR, POR MES (el unico MODIS del candidato fuera de la erupcion)",
          [(m,) for m in sorted({r["mes"] for r in kl})])
    ndc = [r for r in todos if r["run"] == "38560317428"]
    tabla(ndc, lambda r: (r["brazo"], r["b"], "erupcion" if r["noche"] >= "2026-09-28" else "reposo"),
          "NEVADOS DE CHILLAN, run 38560317428 (2026-09-14 a 10-07), por brazo, sensor y fase",
          [(br, s, f) for br in (C0, B, F, K) for s in SENS for f in ("reposo", "erupcion")])

    # Ventana V1 (2026-08-29 a 2026-10-08): lo que hay en disco de ella (septiembre 1 a 18 en 11 volcanes; Chillan
    # hasta 10-07), que es la estimacion del sustrato de la corrida que se pre-registra.
    v1 = [r for r in todos if r["noche"] >= "2026-08-29" and not (r["run"] == "35548121381" and r["vol"] == "NevadosDeChillan"
                                                                  and r["noche"] >= "2026-09-14")]
    for brazo, sensores in ((B, ("VIIRS375", "VIIRS750", "MODIS")), (F, ("VIIRS375", "VIIRS750")), (K, ("MODIS",))):
        for s in sensores:
            rr = [r for r in v1 if r["brazo"] == brazo and r["b"] == s]
            c = tabla(rr, lambda r: (r["vol"],), "V1 EN DISCO: %s %s por volcan (sep 1-18 y Chillan 09-14 a 10-07)" % (brazo, s),
                      [(v,) for v in bp.VOLS])
            tot = collections.Counter()
            for x in c.values():
                tot.update(x)
            print("   TOTAL %s %s: publicadas %s | expuestas %s | magnitud %s" % (brazo, s,
                  "/".join(str(tot["pub|" + g]) for g in GRUPOS), "/".join(str(tot["expuesta|" + g]) for g in GRUPOS),
                  "/".join(str(tot["intacta_mag|" + g]) for g in GRUPOS)))
            print("      veto lectura A (protegidas expuestas): %s" % poder(tot["expuesta|protegida_A"]))
            print("      veto lectura B (protegidas A o B expuestas): %s" % poder(tot["expuesta|protegida_A"] + tot["expuesta|protegida_B"]))
            print("      negativos limpios publicados por este brazo %d | techo de lo que la caja puede quitar de la suma: %d "
                  "negativos limpios expuestos | techo de lo que puede agregarle: %d Muy Bajo publicadas y expuestas" % (
                      tot["pub|neg_limpio"], tot["expuesta|neg_limpio"], tot["expuesta|muy_bajo"]))
    # Lo que se compara con MIROVA (prediccion_mirova.py): que fraccion de NUESTRAS publicaciones tiene el cumulo
    # publicado fuera de la caja, en los 8 volcanes donde el punto de referencia de MIROVA es el crater. MIROVA
    # tiene fuera de su caja entre 0,9 y 2,2 % de sus alertas VIIRS 375 de V1 (cota inferior y superior por el
    # tramo ambiguo de 2,5 a 3,54 km).
    centrados = [v for v in bp.VOLS if v not in ("Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa")]
    print("\n== PUBLICACIONES CON EL CUMULO FUERA DE LA CAJA, 8 volcanes con el centro de MIROVA en el crater")
    for etiqueta, base in (("V1 en disco", v1), ("abril a septiembre, runs mensuales", [r for r in todos if r["run"] != "38560317428"])):
        for brazo, sensores in ((B, SENS), (F, ("VIIRS375", "VIIRS750")), (K, ("MODIS",))):
            for s in sensores:
                rr = [r for r in base if r["brazo"] == brazo and r["b"] == s and r["pub"] and r["vol"] in centrados and r["pc_lat"] is not None]
                if not rr:
                    continue
                fuera = [r for r in rr if not lc.en_caja(r["pc_lat"], r["pc_lon"], anclas[r["vol"]])]
                pos = [r for r in rr if r["lab"] == "pos"]; posf = [r for r in pos if r in fuera]
                neg = [r for r in rr if r["lab"] == "neg_limpio"]; negf = [r for r in neg if r in fuera]
                print("   %-36s %-28s %-8s publicadas %4d, fuera %4d (%.1f %%) | alertas %4d, fuera %3d | negativos %4d, fuera %3d" % (
                    etiqueta, brazo, s, len(rr), len(fuera), 100 * len(fuera) / len(rr), len(pos), len(posf), len(neg), len(negf)))

    print("\n== PASADAS EXPUESTAS DEL CANDIDATO (F en VIIRS, K en MODIS) que son alertas de MIROVA: las unicas que la caja puede perder")
    for r in sorted(todos, key=lambda r: r["dt"]):
        cand = (r["brazo"] == F and r["b"] != "MODIS") or (r["brazo"] == K and r["b"] == "MODIS")
        if cand and r["pub"] and r["cat"] == "expuesta" and grupo(r) in ("protegida_A", "protegida_B", "muy_bajo"):
            print("   %s %-20s %-8s %s | %s | VRP MIROVA %s | pixeles: en caja y circulo %d, solo circulo %d | cumulo a %s km | run %s" % (
                r["brazo"], r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"), grupo(r), r.get("vrp_ref"), r["px"]["CK"],
                r["px"]["C"], r["pc_dist"], r["run"]))
    return 0 if (ok1 and ok2 and ok3 and ok4) else 1


if __name__ == "__main__":
    sys.exit(main())
