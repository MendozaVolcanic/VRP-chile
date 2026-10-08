# -*- coding: utf-8 -*-
"""S150. Evaluador de la prueba de Nevados de Chillan en erupcion (PREREGISTRO_NDC.md, version 3).

Reutiliza armar_tabla.py por pares (etiquetador de banco_paridad, filtro diurno y predicado del tablero
ejecutado con node: nada de eso se reimplementa aca) y le agrega lo que esta prueba necesita leer directo de
los records y de los logs: el tope D9 (`primary_cluster.d9_capped`), la version del producto, la etiqueta,
y los flags que cada job dice haber leido (linea FLAGS_BRAZO del log, escrita por el workflow desde S150).

Uso:
  python medir_ndc.py --raiz DIR --logs DIR --ref _congelado_ndc --out salida.json [--tmp DIR]
--raiz tiene una carpeta por perfil con NevadosDeChillan.json; --logs tiene <perfil>_NevadosDeChillan.log.

Cambios de la version 3 (verificador de la v2, docs/audit_s150/VERIFICADOR_PREREGISTRO_NDC_V2.md):
  N2  P5 se evalua solo en las pasadas que el control tiene topadas; las demas son control de ruido.
  N3  cableado de TODOS los brazos: flags leidos (log) contra declarados, y huella en los records donde la
      hay (sin Test 1, sin tope, etiqueta). Sin logs no hay veredicto.
  N4  el cableado de la etiqueta compara la etiqueta solo donde el cumulo es el mismo en los dos jobs.
  N5  una perdida donde el gemelo tambien cambia ya no se descuenta: vuelve INDECIDIBLE ese par, y solo
      en los pares cuyo control es de la familia de B (G no mide el ruido de C0).
  N6  T0 informa la magnitud sin tope en las pasadas que C0 tiene topadas.
  N7  imprime el sha256 de frontend/index.html (el predicado que se uso).

Las dos preguntas del instrumento (probar_medir_ndc.py): con brazos identicos y bien cableados da cero
perdidas y controles OK; con cada defecto sembrado (perdida VIIRS, perdida MODIS, flag mal leido, tope que no
se apago, etiqueta sin aplicar, decision cambiada por el tope) lo reporta. Un sustrato en cero es SIN DATO.
"""
import argparse, collections, hashlib, io, json, subprocess, sys
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
# Lo que cada brazo DECLARA (diff_perfiles_ndc_salida.txt). (test1, conectiva_prosa, b22, etiqueta_cumulo, tope)
DECLARADO = {"C0": (True, False, False, False, 5.0), "T0": (True, False, False, False, None), "E": (True, False, False, True, 5.0),
             "B": (False, False, False, False, 5.0), "F": (False, True, False, False, 5.0), "J": (False, False, True, False, 5.0),
             "K": (False, True, True, False, 5.0), "KE": (False, True, True, True, 5.0), "KET": (False, True, True, True, None),
             "G": (False, False, False, False, 5.0)}
CLAVES_FLAGS = ("ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY",
                "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER", "PATH_D_ONLY_CAP_MW")
FAMILIA_B = {"B", "F", "J", "K", "KE", "KET", "G"}   # brazos sin Test 1: el gemelo de B mide su ruido
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
    """Lo que el tablero no expone y esta prueba necesita, por pasada."""
    p = raiz / BRAZOS[nombre] / (VOL + ".json"); out = {}
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
        if b is None or not (DESDE <= t[:10] <= HASTA):
            continue
        pc = r.get("primary_cluster") or {}
        out["|".join((VOL, b, t[:16]))] = {
            "pv": r.get("product_version"), "d9": bool(pc.get("d9_capped")), "dc": r.get("distance_class"),
            "pc_dist": pc.get("centroid_dist_km"), "pc_vrp": pc.get("vrp_mw"), "t1": bool(r.get("triggered_test1")),
            "cumulo": (pc.get("centroid_lat"), pc.get("centroid_lon"), pc.get("n_pixels"))}
    return out


def flags_leidos(logs, nombre):
    p = logs / ("%s_%s.log" % (BRAZOS[nombre], VOL))
    if not p.exists():
        return None
    for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if linea.startswith("FLAGS_BRAZO "):
            return json.loads(linea[len("FLAGS_BRAZO "):])
    return None


def perdidas(T, sensores, umbral):
    """Alertas de MIROVA de `umbral` MW o mas que el control publica y el brazo no."""
    return sorted(k for k, v in T.items() if len(v) == 2 and k.split("|")[1] in sensores and v["control"]["lab"] == "pos"
                  and (v["control"]["vrp_ref"] or 0) >= umbral and v["control"]["pub"] and not v["brazo"]["pub"])


def main():
    ap = argparse.ArgumentParser()
    for k in ("raiz", "logs", "ref", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()
    raiz, logs, ref = Path(a.raiz), Path(a.logs), Path(a.ref)
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / "_tmp_medir_ndc"; tmp.mkdir(parents=True, exist_ok=True)
    faltan = [n for n in BRAZOS if not (raiz / BRAZOS[n] / (VOL + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos: %s. No se evalua a medias." % faltan)
    sha_html = hashlib.sha256((RAIZ / "frontend" / "index.html").read_bytes()).hexdigest()
    print("predicado del tablero: frontend/index.html sha256", sha_html)
    T = {p: tabla(raiz, ref, p[0], p[1], tmp) for p in PARES}
    R = {n: crudos(raiz, n) for n in BRAZOS}
    res = {"ventana": [DESDE, HASTA], "sha256_index_html": sha_html, "veredicto": {}, "indecidible": []}

    # 0. Sustrato
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
    print("\n== 0. SUSTRATO (pasadas nocturnas procesadas por C0, etiqueta del evaluador)")
    for s in ("MODIS",) + SENS_V:
        for f in ("reposo", "actividad"):
            print("   %-8s %-9s alertas %3d (1 MW o mas %3d) | negativos limpios %3d" % (
                s, f, S[(s, f, "alertas")], S[(s, f, "alertas_1MW")], S[(s, f, "neg_limpio")]))
    res["sustrato"] = {"|".join(k): n for k, n in S.items()}
    if sum(n for k, n in S.items() if k[2] == "alertas" and k[1] == "actividad") == 0:
        print("   SIN DATO: no hay alertas en actividad. No se emite veredicto."); return 2

    # 1. Cobertura
    print("\n== 1. COBERTURA")
    claves = {n: set(R[n]) for n in BRAZOS}; base = claves["C0"]; mal = False
    for n in BRAZOS:
        d1, d2 = base - claves[n], claves[n] - base
        if d1 or d2:
            mal = True; print("   %-4s le faltan %d pasadas de C0 y tiene %d que C0 no" % (n, len(d1), len(d2)))
    fuertes = sorted(k for k, v in T[("C0", "B")].items() if v.get("control", {}).get("lab") == "pos" and (v["control"]["vrp_ref"] or 0) >= FUERTE)
    sin_rec = {k: [n for n in BRAZOS if k not in claves[n]] for k in fuertes}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    print("   alertas de 1 MW o mas sin record en algun brazo:", sin_rec or "ninguna")
    res["cobertura_ok"] = not (mal or sin_rec)
    print("   " + ("cobertura pareja: OK" if res["cobertura_ok"] else "COBERTURA DESPAREJA: INDECIDIBLE. Repetir los jobs cortos con el mismo codigo."))

    # 2. Version del producto por pasada (H5)
    print("\n== 2. VERSION DEL PRODUCTO POR PASADA")
    mezcla = sorted(k for k in base if len({R[n][k]["pv"] for n in BRAZOS if k in R[n]}) > 1)
    mezcla_f = [k for k in mezcla if k in fuertes]
    print("   pasadas con version distinta entre brazos: %d (alertas de 1 MW o mas: %d) %s" % (len(mezcla), len(mezcla_f), mezcla_f or ""))
    res["version_ok"] = not mezcla_f

    # 3. Cableado de cada brazo (N3): flags leidos contra declarados, y huella en los records
    print("\n== 3. CABLEADO DE CADA BRAZO")
    cable = {}
    for n in BRAZOS:
        problemas = []
        fl = flags_leidos(logs, n)
        if fl is None:
            problemas.append("sin linea FLAGS_BRAZO en el log")
        else:
            leido = tuple(fl.get(c) for c in CLAVES_FLAGS)
            if fl.get("PROFILE_NAME") != BRAZOS[n] or fl.get("DATA_SUBDIR") != BRAZOS[n]:
                problemas.append("perfil o directorio distinto: %s" % fl.get("PROFILE_NAME"))
            if leido != DECLARADO[n]:
                problemas.append("flags leidos %s contra declarados %s" % (leido, DECLARADO[n]))
        test1, _, _, etiqueta, tope = DECLARADO[n]
        if not test1 and any(v["t1"] for v in R[n].values()):
            problemas.append("declara sin Test 1 y hay records con triggered_test1")
        if tope is None and any(v["d9"] for v in R[n].values()):
            problemas.append("declara sin tope y hay records con d9_capped")
        cable[n] = problemas
        print("   %-4s %s" % (n, "OK" if not problemas else "ROTO: " + "; ".join(problemas)))
    # etiqueta (N4): donde el cumulo es el mismo en el brazo con etiqueta y su par sin ella, la etiqueta MODIS
    # tiene que ser la del centroide contra el inner, y el resto igual
    inner = bp.inner_desde_html().get(VOL)
    for con, sin in (("E", "C0"), ("KE", "K"), ("KET", "KE")):
        comparadas, mal_e = 0, []
        for k, e in R[con].items():
            c = R[sin].get(k)
            if c is None or k.split("|")[1] != "MODIS" or e["cumulo"] != c["cumulo"] or e["pc_dist"] is None or c["dc"] is None:
                continue
            comparadas += 1
            if e["dc"] != ("summit" if e["pc_dist"] <= inner else "far"):
                mal_e.append(k)
        print("   etiqueta %s (contra %s): %d pasadas MODIS con el mismo cumulo, %d con etiqueta que no sale del cumulo" % (con, sin, comparadas, len(mal_e)))
        if mal_e:
            cable[con].append("etiqueta que no sale del cumulo en %d pasadas" % len(mal_e))
    k0835 = "|".join((VOL, "MODIS", "2026-10-01 08:35"))
    e0835 = T[("C0", "E")].get(k0835, {}).get("brazo", {}).get("pub")
    print("   E publica 2026-10-01 08:35:", e0835)
    if e0835 != 1:
        cable["E"].append("no publica 2026-10-01 08:35")
    res["cableado"] = {n: (not p) for n, p in cable.items()}

    # 4. Ruido entre jobs: G contra B por sensor; y en cada par, cuantas decisiones cambian en pasadas que
    # ninguna diferencia declarada deberia tocar (referencia para leer P5)
    print("\n== 4. DETERMINISMO (G contra B)")
    det_ok = True; difiere_gb = set()
    for s in ("MODIS",) + SENS_V:
        amb = [(k, v) for k, v in T[("B", "G")].items() if k.split("|")[1] == s and len(v) == 2]
        ig = sum(1 for k, v in amb if v["control"]["pub"] == v["brazo"]["pub"])
        difiere_gb |= {k for k, v in amb if v["control"]["pub"] != v["brazo"]["pub"]}
        ok = bool(amb) and ig / len(amb) >= .98; det_ok &= ok
        print("   %-8s %d pasadas, misma decision %d (%.1f %%) | %s" % (s, len(amb), ig, 100 * ig / len(amb) if amb else 0, "OK" if ok else "FALLA"))
    res["determinismo_ok"] = det_ok

    controles = res["cobertura_ok"] and res["version_ok"] and det_ok
    print("\n== CONTROLES GENERALES:", "OK" if controles else "FALLAN: ningun veredicto decide")
    res["controles_ok"] = controles

    def veredicto_perdidas(nombre, pares, sensores):
        """VETADO si hay perdidas netas; INDECIDIBLE si las unicas perdidas caen donde el gemelo tambien cambia
        y el control es de la familia de B; CUMPLE si no hay ninguna. Un brazo mal cableado: INDECIDIBLE."""
        netas, ruidosas = [], []
        for par in pares:
            for k in perdidas(T[par], sensores, FUERTE):
                c = T[par][k]["control"]
                linea = "%s contra %s: %s | MIROVA %.2f MW | %s" % (par[1], par[0], k, c["vrp_ref"], c["plataforma"])
                (ruidosas if (k in difiere_gb and par[0] in FAMILIA_B) else netas).append(linea)
        brazos = {b for p in pares for b in p}
        rotos = [b for b in brazos if not res["cableado"][b]]
        if rotos or not controles:
            v = "INDECIDIBLE"
        elif netas:
            v = "VETADO"
        elif ruidosas:
            v = "INDECIDIBLE"
        else:
            v = "CUMPLE"
        print("   %s: %s%s" % (nombre, v, (" (brazos mal cableados: %s)" % rotos) if rotos else ""))
        for l in netas: print("      perdida: " + l)
        for l in ruidosas: print("      perdida donde el gemelo tambien cambia: " + l)
        res["veredicto"][nombre] = v
        return v

    # 5. Vetos VIIRS
    print("\n== 5. VETOS VIIRS (alertas de 1 MW o mas)")
    veredicto_perdidas("P1", (("B", "F"), ("C0", "F")), SENS_V)
    veredicto_perdidas("P2", (("C0", "B"),), SENS_V)

    # 6. MODIS
    print("\n== 6. MODIS")
    veredicto_perdidas("P3a_banda22", (("B", "J"),), ("MODIS",))
    veredicto_perdidas("P3b_max", (("J", "K"),), ("MODIS",))
    fM = [k for k in fuertes if k.split("|")[1] == "MODIS"]
    for n in ("KE", "KET"):
        par = ("C0", n); pub = [k for k in fM if T[par].get(k, {}).get("brazo", {}).get("pub")]
        v = "SIN DATO" if not fM else ("INDECIDIBLE" if not (res["cableado"][n] and controles) else ("CUMPLE" if len(pub) == len(fM) else "FALLA"))
        print("   P4 %s publica %d de %d alertas MODIS de 1 MW o mas: %s | %s" % (n, len(pub), len(fM), v, sorted(set(fM) - set(pub)) or ""))
        res["veredicto"]["P4_" + n] = v
    # P5 (N1, N2): solo en las pasadas que el control tiene topadas; el resto mide ruido entre jobs
    for par in (("C0", "T0"), ("KE", "KET")):
        topadas = [k for k in T[par] if len(T[par][k]) == 2 and R[par[0]].get(k, {}).get("d9")]
        cambia = [k for k in topadas if T[par][k]["control"]["pub"] != T[par][k]["brazo"]["pub"]]
        resto = [k for k in T[par] if len(T[par][k]) == 2 and k not in topadas]
        ruido = sum(1 for k in resto if T[par][k]["control"]["pub"] != T[par][k]["brazo"]["pub"])
        print("   P5 %s contra %s: pasadas topadas en el control %d, cambia la decision en %d | ruido en las %d no topadas: %d" % (
            par[1], par[0], len(topadas), len(cambia), len(resto), ruido))
        for k in cambia:
            c, b = T[par][k]["control"], T[par][k]["brazo"]
            print("      %s | lab %s | MIROVA %s | publica %d -> %d | MW %.3f -> %.3f | sin tope el cumulo da %s MW" % (
                k, c["lab"], c["vrp_ref"], c["pub"], b["pub"], c["disp"] or 0, b["disp"] or 0, R[par[1]].get(k, {}).get("pc_vrp")))
        v = "SIN DATO" if not topadas else ("INDECIDIBLE" if not (res["cableado"][par[0]] and res["cableado"][par[1]] and controles) else ("CUMPLE" if not cambia else "FALLA"))
        res["veredicto"]["P5_" + par[1]] = v
        print("      P5 %s: %s" % (par[1], v))
    # N6: magnitud sin tope en las pasadas que C0 tiene topadas
    print("   magnitud de las pasadas topadas en C0, con y sin tope (cumulo):")
    for k in sorted(k for k, v in R["C0"].items() if v["d9"]):
        lab = T[("C0", "T0")].get(k, {}).get("control", {}).get("lab")
        print("      %s | lab %s | C0 %.3f | T0 %s" % (k, lab, R["C0"][k]["pc_vrp"] or 0, R["T0"].get(k, {}).get("pc_vrp")))

    # 7. Costo MODIS (informativo)
    print("\n== 7. COSTO MODIS (informativo): publicaciones en negativos limpios")
    for n in ("C0", "T0", "E", "B", "J", "K", "KE", "KET"):
        par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
        for f in ("reposo", "actividad"):
            neg = [k for k, v in T[par].items() if k.split("|")[1] == "MODIS" and fase(k) == f and lado in v and v[lado]["lab"] == "neg_limpio"]
            pub = [k for k in neg if T[par][k][lado]["pub"]]
            top = [k for k in pub if R[n].get(k, {}).get("d9")]
            print("   %-4s %-9s negativos limpios %3d | publica %3d (topadas en 5 MW: %d)" % (n, f, len(neg), len(pub), len(top)))

    # 8. Recall y magnitud en actividad (informativo)
    print("\n== 8. RECALL POR TRAMO Y MAGNITUD EN ACTIVIDAD (informativo)")
    for n in ("C0", "T0", "B", "F", "J", "K", "KE", "KET"):
        par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
        for s in ("MODIS",) + SENS_V:
            pos = [T[par][k] for k in T[par] if k.split("|")[1] == s and fase(k) == "actividad" and lado in T[par][k] and T[par][k][lado]["lab"] == "pos"]
            if not pos:
                continue
            tr = collections.Counter()
            for v in pos:
                t = "bajo 1 MW" if (v[lado]["vrp_ref"] or 0) < 1 else "1 MW o mas"
                tr[(t, "n")] += 1; tr[(t, "pub")] += v[lado]["pub"]
            raz = sorted(v[lado]["disp"] / v[lado]["vrp_ref"] for v in pos if v[lado]["pub"] and v[lado]["vrp_ref"])
            med = raz[len(raz) // 2] if raz else float("nan")
            print("   %-4s %-8s bajo 1 MW %d de %d | 1 MW o mas %d de %d | razon de magnitud mediana %.2f (n %d)" % (
                n, s, tr[("bajo 1 MW", "pub")], tr[("bajo 1 MW", "n")], tr[("1 MW o mas", "pub")], tr[("1 MW o mas", "n")], med, len(raz)))

    # 9. Antes de la primera alerta (informativo, P8)
    print("\n== 9. ANTES DE LA PRIMERA ALERTA (26 y 27 de septiembre, informativo)")
    for n in ("C0", "B", "F", "KE"):
        par = ("C0", n) if n != "C0" else ("C0", "B"); lado = "brazo" if n != "C0" else "control"
        pubs = [(k, T[par][k][lado]) for k in sorted(T[par]) if k.split("|")[2][:10] in PRE_ACTIVIDAD and lado in T[par][k] and T[par][k][lado]["pub"]]
        print("   %-4s publica %d:" % (n, len(pubs)) + "".join("\n      %s | %.3f MW a %s km" % (k, v["disp"], v["pc_dist"]) for k, v in pubs))

    print("\n== VEREDICTOS (deciden solo con los controles generales en OK):", json.dumps(res["veredicto"], ensure_ascii=False))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
