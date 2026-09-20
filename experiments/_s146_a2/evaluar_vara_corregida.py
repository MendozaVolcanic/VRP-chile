"""S146 - re-evaluacion de la bateria del Apendice A con la vara corregida para A2.

CRITERIO: docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md, escrito y hasheado ANTES de este script
(hash en experiments/_s146_a2/HASH_PRE_REGISTRO.txt). Este script lo aplica; no lo define.

QUE MIDE. Por brazo y por caso, el veredicto de la bateria con (a) la vara vieja (cumulo primario
con VRP > 0 a <= 5 km de la cumbre del catalogo) y (b) la vara nueva (para A2, a <= 5 km de la
fisura de Fimmvorduhals segun GVP BGVN 35:3; los otros ocho casos sin cambio). Mas los controles.

READ-ONLY: lee los resultado_apendice.json commiteados de S136 y S137 y apendice_a.yaml. No importa
ni modifica nada de S136/S137, no toca pipeline/ ni data/. Escribe solo en experiments/_s146_a2/out/.

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si lo que mide estuviera roto (la vara nueva regala aciertos), fallaria? Si: N1 pone la misma
    caja a la misma distancia de la cumbre en otros tres rumbos de la misma escena, y N2 aplica el
    mismo desplazamiento a los otros ocho volcanes, donde no hay fisura. Una vara que regala
    aciertos llena esas cajas.
(2) Si el instrumento estuviera muerto (no mirara posiciones), el resultado se veria distinto? Si:
    C0a exige reproducir los veredictos commiteados con la vara vieja, y C0b exige que con radio
    0,01 km todos los positivos caigan a fallo.

LIMITE DECLARADO: la bateria guarda UN cumulo por pasada (el primario, anclado al crater). Los nulos
miden "el primario cae en la caja", no "hay alguna alerta en la caja".
"""
import io
import json
import math
import sys
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]

RADIO_KM = 5.0            # pre-registro seccion 3: el mismo INNER_KM de S136
RADIO_SENS_KM = 3.0       # sensibilidad informativa, no decisoria
TOL_NTI = 0.06            # control de validez de S136, sin tocar
# Pre-registro seccion 1: GVP BGVN 35:3, "63 38.1' N, 19 26.4' W"
FISURA = {"A2": (63.0 + 38.1 / 60.0, -(19.0 + 26.4 / 60.0))}
PASADA_FIGURA = {"A2": "04:40"}   # titulo de la figura A2 del paper

BRAZOS = [
    ("B21 min (produccion)", "experiments/_s136/out_apendice"),
    ("B21 max (prosa)", "experiments/_s136/out_apendice_prosa"),
    ("B22 min", "experiments/_s137/out_apendice_b22"),
    ("B22 max", "experiments/_s137/out_apendice_b22_prosa"),
    ("B22 sinBT min", "experiments/_s137/out_apendice_b22_sincompuerta"),
    ("B22 sinBT max", "experiments/_s137/out_apendice_b22_sincompuerta_prosa"),
    ("B22 sinBT loc min", "experiments/_s137/out_apendice_b22_sincompuerta_fondolocal"),
    ("B22 sinBT loc max", "experiments/_s137/out_apendice_b22_sincompuerta_fondolocal_prosa"),
]


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p = math.radians
    a = (math.sin(p(la2 - la1) / 2) ** 2
         + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(p(lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def rumbo(la1, lo1, la2, lo2):
    p = math.radians
    dl = p(lo2 - lo1)
    y = math.sin(dl) * math.cos(p(la2))
    x = math.cos(p(la1)) * math.sin(p(la2)) - math.sin(p(la1)) * math.cos(p(la2)) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def punto_desde(lat, lon, dist_km, rumbo_deg):
    R = 6371.0088
    d = dist_km / R
    br = math.radians(rumbo_deg)
    la1, lo1 = math.radians(lat), math.radians(lon)
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(br))
    lo2 = lo1 + math.atan2(math.sin(br) * math.sin(d) * math.cos(la1),
                           math.cos(d) - math.sin(la1) * math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)


def con_magnitud(p):
    return (p.get("vrp_pc_mw") or 0) > 0 and p.get("dist_crater_km") is not None


def filtro_validez(caso, pasadas):
    """Control de validez por NTI de S136, identico. Devuelve (pasadas_utiles, motivo_indet)."""
    if not pasadas:
        return None, "sin pasadas"
    npap = caso.get("nti_paper")
    if npap is None:
        return pasadas, None
    en_banda = [p for p in pasadas if isinstance(p.get("nti_max"), (int, float))
                and abs(p["nti_max"] - npap) <= TOL_NTI]
    if not en_banda:
        return None, "control de validez NTI"
    return en_banda, None


def estado_caja(p, cumbre, centro, radio):
    """'DENTRO' / 'FUERA' / 'INDET' para el cumulo primario de la pasada p respecto de una caja.
    centro None => la caja es la cumbre. Sin pc_lat/pc_lon se usa la cota de A93."""
    if not con_magnitud(p):
        return "FUERA"
    if centro is None:
        return "DENTRO" if p["dist_crater_km"] <= radio else "FUERA"
    if p.get("pc_lat") is not None and p.get("pc_lon") is not None:
        return "DENTRO" if hav(p["pc_lat"], p["pc_lon"], *centro) <= radio else "FUERA"
    D = hav(*cumbre, *centro)
    d = p["dist_crater_km"]
    if abs(d - D) > radio:
        return "FUERA"          # cota inferior ya supera el radio
    return "INDET"              # un acierto no se prueba con el radio solo


def veredicto(caso, pasadas, centro, radio):
    """Predicado de S136 con la caja centrada en `centro` (None = cumbre)."""
    utiles, motivo = filtro_validez(caso, pasadas)
    if utiles is None:
        return "INDETERMINADO", motivo
    cumbre = (caso["lat"], caso["lon"])
    est = [estado_caja(p, cumbre, centro, radio) for p in utiles]
    nd, ni = est.count("DENTRO"), est.count("INDET")
    positivo = caso["veredicto"] == "detecta"
    if nd:
        return ("CONFORME" if positivo else "NO CONFORME (falso positivo)"), f"{nd} de {len(utiles)}"
    if ni:
        return "INDECIDIBLE (sin posicion)", f"{ni} pasadas con cota A93 que no decide"
    return ("NO CONFORME (falso negativo)" if positivo else "CONFORME"), f"0 de {len(utiles)}"


def corto(v):
    return {"CONFORME": "OK", "NO CONFORME (falso negativo)": "FN",
            "NO CONFORME (falso positivo)": "FP", "INDETERMINADO": "INDET",
            "INDECIDIBLE (sin posicion)": "INDEC"}.get(v, v)


def main():
    casos_yaml = {c["caso"]: c for c in
                  yaml.safe_load((RAIZ / "experiments/_s136/apendice_a.yaml").read_text(encoding="utf-8"))["casos"]}
    orden = sorted(casos_yaml)
    datos = {}
    for nombre, ruta in BRAZOS:
        d = json.loads((RAIZ / ruta / "resultado_apendice.json").read_text(encoding="utf-8"))
        datos[nombre] = {c["caso"]: c for c in d}

    cumbre_a2 = (casos_yaml["A2"]["lat"], casos_yaml["A2"]["lon"])
    D_FIS = hav(*cumbre_a2, *FISURA["A2"])
    R_FIS = rumbo(*cumbre_a2, *FISURA["A2"])
    print("=" * 100)
    print("PUNTO DE REFERENCIA A2 (GVP BGVN 35:3): lat %.4f lon %.4f ; a %.2f km rumbo %.1f de la cumbre"
          % (FISURA["A2"][0], FISURA["A2"][1], D_FIS, R_FIS))
    print("radio decisorio %.1f km ; radio de sensibilidad %.1f km" % (RADIO_KM, RADIO_SENS_KM))
    salida = {"punto_fisura": {"lat": FISURA["A2"][0], "lon": FISURA["A2"][1],
                               "dist_cumbre_km": round(D_FIS, 3), "rumbo": round(R_FIS, 2)},
              "brazos": {}}

    # ---------------- C0a identidad, C0b control positivo
    print("\n" + "=" * 100 + "\nC0a IDENTIDAD: vara vieja reimplementada vs veredicto commiteado")
    iguales = total = 0
    for nombre, _ in BRAZOS:
        for k in orden:
            v, _d = veredicto(casos_yaml[k], datos[nombre][k]["pasadas"], None, RADIO_KM)
            total += 1
            if v == datos[nombre][k]["resultado"]:
                iguales += 1
            else:
                print(f"  DISCREPA  {nombre}  {k}: mio={v!r}  commiteado={datos[nombre][k]['resultado']!r}")
    print(f"  reproduce {iguales} de {total}")
    caen = tot_pos = 0
    for nombre, _ in BRAZOS:
        for k in orden:
            if casos_yaml[k]["veredicto"] != "detecta":
                continue
            centro = FISURA.get(k)
            v, _d = veredicto(casos_yaml[k], datos[nombre][k]["pasadas"], centro, 0.01)
            tot_pos += 1
            caen += v in ("NO CONFORME (falso negativo)", "INDETERMINADO")
    print(f"C0b CONTROL POSITIVO (vara nueva, radio 0,01 km): {caen} de {tot_pos} positivos caen a fallo o indeterminado")
    salida["C0a"] = {"iguales": iguales, "total": total}
    salida["C0b"] = {"caen": caen, "total": tot_pos}

    # ---------------- tabla brazo por caso
    print("\n" + "=" * 100 + "\nTABLA BRAZO x CASO   (vieja -> nueva ; solo A2 puede cambiar)")
    print("%-24s" % "brazo" + "".join("%-13s" % k for k in orden) + "vieja    nueva")
    for nombre, _ in BRAZOS:
        fila, okv, okn, res = [], 0, 0, {}
        for k in orden:
            c = casos_yaml[k]
            vv, _ = veredicto(c, datos[nombre][k]["pasadas"], None, RADIO_KM)
            vn, dn = veredicto(c, datos[nombre][k]["pasadas"], FISURA.get(k), RADIO_KM)
            okv += vv == "CONFORME"
            okn += vn == "CONFORME"
            fila.append(f"{corto(vv)}->{corto(vn)}")
            res[k] = {"vieja": vv, "nueva": vn, "detalle_nueva": dn}
        print("%-24s" % nombre + "".join("%-13s" % f for f in fila) + f"{okv}/9      {okn}/9")
        salida["brazos"][nombre] = {"casos": res, "conformes_vieja": okv, "conformes_nueva": okn}

    # ---------------- C1 negativos
    print("\n" + "=" * 100 + "\nC1 NEGATIVOS: veredicto vara vieja vs vara nueva (identidad por construccion de la regla)")
    dif = 0
    for nombre, _ in BRAZOS:
        for k in orden:
            if casos_yaml[k]["veredicto"] == "detecta":
                continue
            r = salida["brazos"][nombre]["casos"][k]
            dif += r["vieja"] != r["nueva"]
    print(f"  negativos que cambian de veredicto: {dif} de {3 * len(BRAZOS)}")
    salida["C1_negativos_que_cambian"] = dif

    # ---------------- detalle A2
    print("\n" + "=" * 100 + "\nDETALLE A2: cumulos primarios con magnitud, por brazo y pasada")
    for nombre, _ in BRAZOS:
        print(f"  {nombre}")
        det = []
        for p in datos[nombre]["A2"]["pasadas"]:
            if not con_magnitud(p):
                continue
            tiene = p.get("pc_lat") is not None
            sep = hav(p["pc_lat"], p["pc_lon"], *FISURA["A2"]) if tiene else None
            rb = rumbo(*cumbre_a2, p["pc_lat"], p["pc_lon"]) if tiene else None
            cota = None if tiene else abs(p["dist_crater_km"] - D_FIS)
            print("    %s  vrp=%8.3f MW  n_px=%s  d_cumbre=%6.2f  rumbo=%s  sep_fisura=%s  cota_A93=%s  nti=%s"
                  % (p["inicio"][11:16], p["vrp_pc_mw"], p.get("n_pixels_pc"), p["dist_crater_km"],
                     "  s/d" if rb is None else "%5.1f" % rb,
                     "  s/d" if sep is None else "%5.2f" % sep,
                     "  -" if cota is None else "%5.2f" % cota, p.get("nti_max")))
            det.append({"hora": p["inicio"][11:16], "vrp": p["vrp_pc_mw"], "d_cumbre": p["dist_crater_km"],
                        "rumbo": rb, "sep_fisura": sep, "cota_A93": cota})
        salida["brazos"][nombre]["A2_cumulos"] = det

    # ---------------- secundarios A2: radio 3 km y solo pasada de la figura
    print("\n" + "=" * 100 + "\nSECUNDARIOS A2 (informativos, no decisorios)")
    for nombre, _ in BRAZOS:
        c = casos_yaml["A2"]
        ps = datos[nombre]["A2"]["pasadas"]
        v3, _ = veredicto(c, ps, FISURA["A2"], RADIO_SENS_KM)
        fig = [p for p in ps if p["inicio"][11:16] == PASADA_FIGURA["A2"]]
        vf, _ = veredicto(c, fig, FISURA["A2"], RADIO_KM)
        print("  %-24s radio 3 km: %-32s solo pasada 04:40 (n=%d): %s" % (nombre, v3, len(fig), vf))
        salida["brazos"][nombre]["A2_radio3"] = v3
        salida["brazos"][nombre]["A2_solo_figura"] = vf

    # ---------------- N1 y N2
    giros = [90.0, 180.0, 270.0]
    print("\n" + "=" * 100 + "\nN1 NULO EN A2: misma caja (5 km) a %.2f km de la cumbre, rumbo girado +90/+180/+270" % D_FIS)
    for nombre, _ in BRAZOS:
        ps, _m = filtro_validez(casos_yaml["A2"], datos[nombre]["A2"]["pasadas"])
        celdas = []
        for g in giros:
            centro = punto_desde(*cumbre_a2, D_FIS, (R_FIS + g) % 360)
            est = [estado_caja(p, cumbre_a2, centro, RADIO_KM) for p in ps]
            celdas.append("CON CUMULO" if "DENTRO" in est else ("INDET" if "INDET" in est else "VACIA"))
        print("  %-24s rumbo %5.1f: %-11s rumbo %5.1f: %-11s rumbo %5.1f: %-11s"
              % (nombre, (R_FIS + 90) % 360, celdas[0], (R_FIS + 180) % 360, celdas[1],
                 (R_FIS + 270) % 360, celdas[2]))
        salida["brazos"][nombre]["N1"] = celdas

    print("\n" + "=" * 100 + "\nN2 NULO EN LOS OTROS 8 CASOS: caja de 5 km a %.2f km, rumbos %.1f +0/+90/+180/+270" % (D_FIS, R_FIS))
    tot = {"VACIA": 0, "CON CUMULO": 0, "INDET": 0}
    for nombre, _ in BRAZOS:
        cnt = {"VACIA": 0, "CON CUMULO": 0, "INDET": 0}
        llenas = []
        for k in orden:
            if k == "A2":
                continue
            c = casos_yaml[k]
            cumbre = (c["lat"], c["lon"])
            ps = datos[nombre][k]["pasadas"]
            for g in [0.0] + giros:
                rb = (R_FIS + g) % 360
                centro = punto_desde(*cumbre, D_FIS, rb)
                est = [estado_caja(p, cumbre, centro, RADIO_KM) for p in ps]
                e = "CON CUMULO" if "DENTRO" in est else ("INDET" if "INDET" in est else "VACIA")
                cnt[e] += 1
                if e != "VACIA":
                    llenas.append(f"{k}@{rb:.0f}:{e}")
        for e in cnt:
            tot[e] += cnt[e]
        print("  %-24s vacias %2d  con cumulo %2d  indet %2d  de 32   %s"
              % (nombre, cnt["VACIA"], cnt["CON CUMULO"], cnt["INDET"], " ".join(llenas)))
        salida["brazos"][nombre]["N2"] = {**cnt, "no_vacias": llenas}
    print("  TOTAL: %s de %d" % (tot, 32 * len(BRAZOS)))
    salida["N2_total"] = tot

    # ---------------- poder de los nulos (diagnostico, NO parte del criterio pre-registrado)
    print("\n" + "=" * 100 + "\nPODER DE LOS NULOS (diagnostico agregado despues del pre-registro, no decide nada):")
    print("pasadas cuyo cumulo primario con magnitud queda en el anillo %.2f a %.2f km de la cumbre,"
          % (D_FIS - RADIO_KM, D_FIS + RADIO_KM))
    print("o sea las unicas que PODRIAN caer en alguna caja desplazada. Si son cero, el nulo esta ciego.")
    salida["poder_nulos"] = {}
    for nombre, _ in BRAZOS:
        en_anillo, con_mag = [], 0
        for k in orden:
            for p in datos[nombre][k]["pasadas"]:
                if not con_magnitud(p):
                    continue
                if k != "A2":
                    con_mag += 1
                if k != "A2" and abs(p["dist_crater_km"] - D_FIS) <= RADIO_KM:
                    en_anillo.append("%s %s d=%.2f" % (k, p["inicio"][11:16], p["dist_crater_km"]))
        print("  %-24s %d de %d pasadas con magnitud (8 casos sin A2)   %s"
              % (nombre, len(en_anillo), con_mag, "; ".join(en_anillo)))
        salida["poder_nulos"][nombre] = {"en_anillo": en_anillo, "con_magnitud": con_mag}

    # ---------------- veredicto final A2 por brazo segun pre-registro seccion 4
    print("\n" + "=" * 100 + "\nVEREDICTO FINAL A2 POR BRAZO (pre-registro seccion 4) y total del brazo")
    for nombre, _ in BRAZOS:
        b = salida["brazos"][nombre]
        v = b["casos"]["A2"]["nueva"]
        n1 = b["N1"]
        if v == "CONFORME":
            if all(x == "VACIA" for x in n1):
                final = "ACIERTO"
            else:
                final = "INDECIDIBLE (N1 no vacio o indeterminado)"
        elif v == "NO CONFORME (falso negativo)":
            final = "FALLO"
        else:
            final = "INDECIDIBLE (SIN DATO de posicion)"
        fragil = " [fragil: cambia con radio 3 km]" if (final == "ACIERTO" and b["A2_radio3"] != "CONFORME") else ""
        otros = sum(1 for k in orden if k != "A2" and b["casos"][k]["nueva"] == "CONFORME")
        total9 = otros + (final == "ACIERTO")
        aprueba = "APRUEBA 9/9" if total9 == 9 else "no aprueba"
        print("  %-24s A2: %-44s otros 8: %d/8   total %d/9   %s" % (nombre, final + fragil, otros, total9, aprueba))
        b["A2_final"] = final + fragil
        b["total_nueva_final"] = total9

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / "resultado_vara_corregida.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nescrito:", out / "resultado_vara_corregida.json")


if __name__ == "__main__":
    main()
