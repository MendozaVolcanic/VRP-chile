# -*- coding: utf-8 -*-
"""S150. Evaluador de la prueba de Nevados de Chillan en erupcion (PREREGISTRO_NDC.md, version 2).

Escrito porque los evaluadores existentes miden las predicciones de S149 y no estas (verificador del
pre-registro, H4). Reutiliza armar_tabla.py por pares (etiquetador de banco_paridad, filtro diurno y
predicado del tablero ejecutado con node: nada de eso se reimplementa aca) y le agrega lo que esta
prueba necesita leer directo de los records: el tope D9 (`primary_cluster.d9_capped`), la version del
producto por pasada y la etiqueta summit/far.

Uso:
  python medir_ndc.py --raiz DIR --ref _congelado_ndc --out medir_ndc_salida.json [--brazos C0=perfil ...]
DIR tiene una carpeta por perfil con NevadosDeChillan.json adentro (la union que arma evaluar_ventana.py).

Las dos preguntas del instrumento, y su respuesta (ver probar_medir_ndc.py):
1. Si lo que mide estuviera roto, lo veria: con brazos identicos todo da 0 perdidas y 100 % de
   determinismo; con una perdida sembrada a mano en una alerta de 1 MW o mas, P1 la reporta.
2. Si el instrumento estuviera muerto, se veria distinto: imprime el sustrato que encontro (alertas por
   sensor y fase); un sustrato en cero se marca SIN DATO y no se emite veredicto.
"""
import argparse, collections, io, json, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
bp = ev.bp
ARMAR = RAIZ / "experiments" / "_s149_prereg_invierno" / "armar_tabla.py"
VOL = "NevadosDeChillan"
DESDE, HASTA, INICIO_ACTIVIDAD = "2026-09-14", "2026-10-07", "2026-09-28"
PRE_ACTIVIDAD = ("2026-09-26", "2026-09-27")
BRAZOS = {"C0": "_s146_ab_control", "T0": "_s150_sin_tope_d9", "E": "_s150_etiqueta_cumulo", "B": "_s146_ab_sin_test1",
          "F": "_s147_ab_sin_test1_max", "J": "_s149_ab_sin_test1_b22", "K": "_s149_ab_sin_test1_b22_max",
          "KE": "_s150_k_etiqueta", "KET": "_s150_k_etiqueta_sin_tope", "G": "_s149_ab_sin_test1_gemelo"}
PARES = [("C0", "T0"), ("C0", "E"), ("C0", "B"), ("B", "F"), ("C0", "F"), ("B", "J"), ("J", "K"), ("K", "KE"),
         ("KE", "KET"), ("C0", "J"), ("C0", "K"), ("C0", "KE"), ("C0", "KET"), ("B", "G")]
SENS_V = ("VIIRS375", "VIIRS750")
FUERTE = 1.0


def fase(k):
    return "actividad" if k.split("|")[2][:10] >= INICIO_ACTIVIDAD else "reposo"


def tabla(raiz, ref, a, b, tmp):
    out = tmp / ("t_%s_%s.json" % (a, b))
    r = subprocess.run([sys.executable, str(ARMAR), "--control", str(raiz / BRAZOS[a]), "--brazo", str(raiz / BRAZOS[b]),
                        "--cons", str(ref / "registro_vrp_consolidado.csv"), "--ocr", str(ref / "registro_vrp_ocr.csv"),
                        "--desde", DESDE, "--hasta", HASTA, "--out", str(out)], capture_output=True, text=True)
    if r.returncode != 0:   # D-10 del auditor D: no se descarta el error de armar_tabla
        raise SystemExit("armar_tabla fallo para %s/%s:\n%s" % (a, b, r.stderr[-2000:]))
    return json.loads(out.read_text(encoding="utf-8"))["pasadas"]


def crudos(raiz, nombre):
    """Lo que el tablero no expone y esta prueba necesita: tope, version del producto, etiqueta."""
    p = raiz / BRAZOS[nombre] / (VOL + ".json"); out = {}
    if not p.exists():
        return None
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
        if b is None or not (DESDE <= t[:10] <= HASTA):
            continue
        pc = r.get("primary_cluster") or {}
        out["|".join((VOL, b, t[:16]))] = {"pv": r.get("product_version"), "d9": bool(pc.get("d9_capped")),
                                           "dc": r.get("distance_class"), "pc_dist": pc.get("centroid_dist_km"),
                                           "pc_vrp": pc.get("vrp_mw")}
    return out


def perdidas(T, sensores, umbral):
    """Alertas de MIROVA de `umbral` MW o mas que el control publica y el brazo no."""
    return sorted(k for k, v in T.items() if len(v) == 2 and k.split("|")[1] in sensores and v["control"]["lab"] == "pos"
                  and (v["control"]["vrp_ref"] or 0) >= umbral and v["control"]["pub"] and not v["brazo"]["pub"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True); ap.add_argument("--ref", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()
    raiz, ref = Path(a.raiz), Path(a.ref)
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / "_tmp_medir_ndc"; tmp.mkdir(parents=True, exist_ok=True)
    faltan = [n for n in BRAZOS if not (raiz / BRAZOS[n] / (VOL + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos: %s. No se evalua a medias." % faltan)
    T = {p: tabla(raiz, ref, p[0], p[1], tmp) for p in PARES}
    R = {n: crudos(raiz, n) for n in BRAZOS}
    res = {"ventana": [DESDE, HASTA], "veredicto": {}}

    # 0. Sustrato, de la tabla C0 contra si misma (pasadas que procesamos, de noche, con la etiqueta del evaluador)
    S = collections.Counter()
    for k, v in T[("C0", "B")].items():
        c = v.get("control")
        if c is None:
            continue
        s, f = k.split("|")[1], fase(k)
        if c["lab"] == "pos":
            S[(s, f, "alertas")] += 1; S[(s, f, "alertas_1MW")] += (c["vrp_ref"] or 0) >= FUERTE
        elif c["lab"] == "neg_limpio":
            S[(s, f, "neg_limpio")] += 1
        if c["rutina_pasada"] and c["noche_con_alerta_sensor"]:
            S[(s, f, "rutina_en_noche_activa")] += 1
    print("== 0. SUSTRATO (pasadas nocturnas procesadas por C0, etiqueta del evaluador)")
    for s in ("MODIS",) + SENS_V:
        for f in ("reposo", "actividad"):
            print("   %-8s %-9s alertas %3d (1 MW o mas %3d) | negativos limpios %3d | RUTINA en noche activa %3d" % (
                s, f, S[(s, f, "alertas")], S[(s, f, "alertas_1MW")], S[(s, f, "neg_limpio")], S[(s, f, "rutina_en_noche_activa")]))
    res["sustrato"] = {"|".join(k): n for k, n in S.items()}
    if sum(n for k, n in S.items() if k[2] == "alertas" and k[1] == "actividad") == 0:
        print("   SIN DATO: no hay alertas en actividad. No se emite veredicto."); return 2

    # 1. Cobertura pareja y alertas fuertes con record en todos los brazos
    print("\n== 1. COBERTURA")
    claves = {n: set(R[n]) for n in BRAZOS}; base = claves["C0"]; mal = False
    for n in BRAZOS:
        d1, d2 = base - claves[n], claves[n] - base
        if d1 or d2:
            mal = True; print("   %-4s le faltan %d pasadas de C0 y tiene %d que C0 no" % (n, len(d1), len(d2)))
    fuertes = [k for k, v in T[("C0", "B")].items() if v.get("control", {}).get("lab") == "pos" and (v["control"]["vrp_ref"] or 0) >= FUERTE]
    sin_rec = {k: [n for n in BRAZOS if k not in claves[n]] for k in fuertes}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    print("   alertas de 1 MW o mas sin record en algun brazo:", sin_rec or "ninguna")
    print("   " + ("COBERTURA DESPAREJA: INDECIDIBLE. Repetir los jobs cortos con el mismo codigo." if mal or sin_rec else "cobertura pareja: OK"))
    res["cobertura_ok"] = not (mal or sin_rec)

    # 2. Version del producto por pasada (H5): las alertas fuertes deben tener la misma version en todos los brazos
    print("\n== 2. VERSION DEL PRODUCTO POR PASADA")
    mezcla = [k for k in base if len({R[n][k]["pv"] for n in BRAZOS if k in R[n]}) > 1]
    mezcla_f = [k for k in mezcla if k in fuertes]
    print("   pasadas con version distinta entre brazos: %d (alertas de 1 MW o mas: %d)" % (len(mezcla), len(mezcla_f)))
    if mezcla_f:
        print("   INDECIDIBLE: %s. Re-despachar cuando el producto estandar este disponible para toda la ventana." % mezcla_f)
    res["version_ok"] = not mezcla_f

    # 3. Determinismo G contra B, por sensor
    print("\n== 3. DETERMINISMO (G contra B)")
    det_ok = True; difiere_gb = set()
    for s in ("MODIS",) + SENS_V:
        amb = [(k, v) for k, v in T[("B", "G")].items() if k.split("|")[1] == s and len(v) == 2]
        ig = sum(1 for k, v in amb if v["control"]["pub"] == v["brazo"]["pub"])
        difiere_gb |= {k for k, v in amb if v["control"]["pub"] != v["brazo"]["pub"]}
        ok = bool(amb) and ig / len(amb) >= .98; det_ok &= ok
        print("   %-8s %d pasadas, misma decision %d (%.1f %%) | %s" % (s, len(amb), ig, 100 * ig / len(amb) if amb else 0, "OK" if ok else "FALLA: INDECIDIBLE"))
    res["determinismo_ok"] = det_ok

    # 4. Control del cableado de la etiqueta: E tiene que ser C0 reetiquetado, pasada por pasada (A116, A118)
    print("\n== 4. CONTROL DE LA ETIQUETA (E = C0 reetiquetado)")
    inner = bp.inner_desde_html().get(VOL)
    malE = []
    for k, e in R["E"].items():
        c = R["C0"].get(k)
        if c is None:
            continue
        if k.split("|")[1] == "MODIS" and c["pc_dist"] is not None and c["dc"] is not None and inner is not None:
            esperado = "summit" if c["pc_dist"] <= inner else "far"
        else:
            esperado = c["dc"]
        if e["dc"] != esperado or e["pc_vrp"] != c["pc_vrp"] or e["d9"] != c["d9"]:
            malE.append(k)
    k0835 = "|".join((VOL, "MODIS", "2026-10-01 08:35"))
    e0835 = T[("C0", "E")].get(k0835, {}).get("brazo", {}).get("pub")
    print("   pasadas donde E no es C0 reetiquetado: %d | E publica 2026-10-01 08:35: %s" % (len(malE), e0835))
    cable_ok = not malE and e0835 == 1
    print("   " + ("cableado OK" if cable_ok else "CABLEADO ROTO: INDECIDIBLE para E y KE; trazar por etapa (A75)."))
    res["cableado_etiqueta_ok"] = cable_ok

    controles = res["cobertura_ok"] and res["version_ok"] and det_ok
    print("\n== CONTROLES:", "OK" if controles else "FALLAN: los vetos de abajo se informan pero NO deciden")

    def informar_perdidas(nombre, par, sensores, umbral=FUERTE):
        p = perdidas(T[par], sensores, umbral)
        ruido = [k for k in p if k in difiere_gb]
        netas = [k for k in p if k not in difiere_gb]
        print("   %s (%s contra %s): perdidas de %.1f MW o mas: %d%s" % (nombre, par[1], par[0], umbral, len(netas),
              (" (y %d descontadas porque el gemelo tambien cambia ahi)" % len(ruido)) if ruido else ""))
        for k in netas:
            c = T[par][k]["control"]; print("      %s | MIROVA %.2f MW | %s" % (k, c["vrp_ref"], c["plataforma"]))
        return netas

    # 5. Vetos VIIRS
    print("\n== 5. VETOS VIIRS (P1, P2): cero perdidas de alertas de 1 MW o mas")
    for nombre, pares in (("P1", (("B", "F"), ("C0", "F"))), ("P2", (("C0", "B"),))):
        netas = sum((informar_perdidas(nombre, par, SENS_V) for par in pares), [])
        res["veredicto"][nombre] = "VETADO" if netas else "CUMPLE"

    # 6. MODIS: deteccion (banda 22), tope y etiqueta
    print("\n== 6. MODIS")
    # P3: atribucion de la banda 22 y de max por separado
    pj = informar_perdidas("P3a banda 22", ("B", "J"), ("MODIS",)); pk = informar_perdidas("P3b max", ("J", "K"), ("MODIS",))
    res["veredicto"]["P3"] = "FALLA" if (pj or pk) else "CUMPLE"
    # P4: el candidato completo publica las alertas MODIS de 1 MW o mas
    fM = [k for k in fuertes if k.split("|")[1] == "MODIS"]
    for n in ("KE", "KET"):
        par = ("C0", n); pub = [k for k in fM if T[par].get(k, {}).get("brazo", {}).get("pub")]
        print("   P4 %s publica %d de %d alertas MODIS de 1 MW o mas: %s" % (n, len(pub), len(fM), sorted(set(fM) - set(pub)) or "todas"))
        res["veredicto"]["P4_" + n] = "CUMPLE" if fM and len(pub) == len(fM) else ("SIN DATO" if not fM else "FALLA")
    # P5: el tope D9 no cambia ninguna decision de publicar (T0 contra C0; KET contra KE)
    for par in (("C0", "T0"), ("KE", "KET")):
        cambia = [k for k, v in T[par].items() if len(v) == 2 and v["control"]["pub"] != v["brazo"]["pub"]]
        dmag = [k for k, v in T[par].items() if len(v) == 2 and v["control"]["pub"] and v["brazo"]["pub"] and abs((v["control"]["disp"] or 0) - (v["brazo"]["disp"] or 0)) > 1e-6]
        print("   P5 %s contra %s: decisiones de publicar distintas %d | publicadas en los dos con magnitud distinta %d" % (par[1], par[0], len(cambia), len(dmag)))
        for k in cambia[:12]:
            print("      cambia: %s | lab %s | MIROVA %s" % (k, T[par][k]["control"]["lab"], T[par][k]["control"]["vrp_ref"]))
        res["veredicto"]["P5_" + par[1]] = "CUMPLE" if not cambia else "FALLA"

    # 7. Costo MODIS (informativo): publicaciones en negativos limpios, separando las topadas en 5 MW
    print("\n== 7. COSTO MODIS (informativo): publicaciones en negativos limpios y en RUTINA de noche activa")
    for n in ("C0", "T0", "E", "B", "J", "K", "KE", "KET"):
        par = ("C0", n) if n != "C0" else ("C0", "B")
        lado = "brazo" if n != "C0" else "control"
        for f in ("reposo", "actividad"):
            neg = [k for k, v in T[par].items() if k.split("|")[1] == "MODIS" and fase(k) == f and lado in v and v[lado]["lab"] == "neg_limpio"]
            pub = [k for k in neg if T[par][k][lado]["pub"]]
            top = [k for k in pub if R[n].get(k, {}).get("d9")]
            print("   %-4s %-9s negativos limpios %3d | publica %3d (topadas en 5 MW: %d)" % (n, f, len(neg), len(pub), len(top)))

    # 8. VIIRS por tramo y magnitud pareada en actividad (informativo)
    print("\n== 8. RECALL POR TRAMO Y MAGNITUD EN ACTIVIDAD (informativo)")
    for n in ("C0", "T0", "B", "F", "KE", "KET"):
        par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
        for s in ("MODIS",) + SENS_V:
            pos = [T[par][k] for k in T[par] if k.split("|")[1] == s and fase(k) == "actividad" and lado in T[par][k] and T[par][k][lado]["lab"] == "pos"]
            if not pos:
                continue
            tr = collections.Counter()
            for v in pos:
                m = v[lado]["vrp_ref"] or 0; t = "bajo 1 MW" if m < 1 else "1 MW o mas"
                tr[(t, "n")] += 1; tr[(t, "pub")] += v[lado]["pub"]
            raz = sorted(v[lado]["disp"] / v[lado]["vrp_ref"] for v in pos if v[lado]["pub"] and v[lado]["vrp_ref"])
            med = raz[len(raz) // 2] if raz else float("nan")
            print("   %-4s %-8s bajo 1 MW %d de %d | 1 MW o mas %d de %d | razon de magnitud mediana %.2f (n %d)" % (
                n, s, tr[("bajo 1 MW", "pub")], tr[("bajo 1 MW", "n")], tr[("1 MW o mas", "pub")], tr[("1 MW o mas", "n")], med, len(raz)))

    # 9. Antes de la primera alerta (26 y 27 de septiembre): que publica cada brazo, y donde (informativo, P8)
    print("\n== 9. ANTES DE LA PRIMERA ALERTA (26 y 27 de septiembre, informativo)")
    for n in ("C0", "B", "F", "KE"):
        par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
        pubs = [(k, T[par][k][lado]) for k in sorted(T[par]) if k.split("|")[2][:10] in PRE_ACTIVIDAD and lado in T[par][k] and T[par][k][lado]["pub"]]
        print("   %-4s publica %d:" % (n, len(pubs)) + "".join("\n      %s | %.3f MW a %s km" % (k, v["disp"], v["pc_dist"]) for k, v in pubs))

    print("\n== VEREDICTOS (deciden sólo con los controles en OK):", json.dumps(res["veredicto"], ensure_ascii=False))
    res["controles_ok"] = controles
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
