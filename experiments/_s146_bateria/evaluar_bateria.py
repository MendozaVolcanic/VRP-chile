"""S146 - evaluador de la bateria del Apendice A: vara corregida (criterio sellado de A2) mas el nulo
por pixel alertado (criterio de esta carpeta).

CRITERIOS, los dos escritos antes que este script y ninguno definido aca:
  docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md              veredicto por cumulo primario (sellado)
  experiments/_s146_bateria/CRITERIO_NULO_POR_PIXEL.md       nulo por pixel: R1 a R4, Cpx-a a Cpx-d
El predicado sellado NO se reimplementa: se importa de experiments/_s146_a2/evaluar_vara_corregida.py
(funciones `veredicto`, `estado_caja`, `hav`, `punto_desde`, `rumbo` y las constantes), para que haya
una sola copia (A102). Ese archivo no se modifica ni se ejecuta su main().

SOLO LECTURA sobre las salidas del probe. Escribe unicamente en el directorio `--informe`.

Uso:  python experiments/_s146_bateria/evaluar_bateria.py [--out DIR] [--informe DIR]
Salida 0 = el instrumento esta sano (el veredicto se LEE, no es un codigo de salida);
salida 1 = el instrumento fallo un control (R4, Cpx-a o Cpx-b) y los nulos no valen.

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si lo que mide estuviera roto (la vara regala aciertos), fallaria? Si: cuenta pixeles alertados
    con magnitud en cajas donde no hay nada que detectar (N1px, N2px) y en la cumbre de los casos
    negativos (NEGpx). prueba_local.py planta un pixel en una caja rotada y comprueba que el acierto
    pasa a INDECIDIBLE, y que sin ese pixel no pasa.
(2) Si el instrumento estuviera muerto (captura vacia, evaluador que no mira posiciones), se veria
    distinto? Si: R4 y Cpx-b dan salida 1 cuando un brazo acierta A2 por cumulo primario y no hay
    ningun pixel con magnitud en la caja de la fisura; Cpx-a recuenta cumulos contra pixeles.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402
import brazos as B  # noqa: E402

# Klyuchevskoy dentro de la caja; ver CRITERIO_NULO_POR_PIXEL.md seccion 3.
EXCLUIDAS = {("A1", 270.0)}          # (caso, giro respecto del rumbo de la fisura)
CORTE_MARGINAL, CORTE_REGALA = 1, 4  # seccion 4, R2
NEGATIVOS = ("A4", "A7", "A9")


def cargar_sellado():
    ruta = RAIZ / "experiments" / "_s146_a2" / "evaluar_vara_corregida.py"
    spec = importlib.util.spec_from_file_location("vara_corregida_s146", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)     # OJO: al importarse reenvuelve sys.stdout en UTF-8; aca no se repite
    return mod


def sha_lf(ruta):
    """sha256 con finales de linea normalizados a LF. En Windows con core.autocrlf=true el checkout
    deja CRLF y el hash crudo no coincide con el sellado aunque el contenido sea el mismo (medido en
    S146 sobre el pre-registro de A2)."""
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def hash_anotado(ruta):
    return Path(ruta).read_text(encoding="utf-8").split()[0].strip()


def pixeles_de(pasada):
    """Pixeles alertados de la pasada, sin repetir el mismo (fila, col) si lo listaron dos llamadas."""
    vistos = {}
    for px in pasada.get("pixeles_alertados") or []:
        k = (px["fila"], px["col"])
        if k not in vistos or (px.get("vrp_mw") or 0) > (vistos[k].get("vrp_mw") or 0):
            vistos[k] = px
    return list(vistos.values())


def contar_caja(ev, pasadas, centro, radio):
    """(n con magnitud, MW, n alertados en total) dentro de la caja, sumando las pasadas."""
    n_mag = n_tot = 0
    mw = 0.0
    for p in pasadas:
        for px in pixeles_de(p):
            if ev.hav(px["lat"], px["lon"], *centro) <= radio:
                n_tot += 1
                if (px.get("vrp_mw") or 0) > 0:
                    n_mag += 1
                    mw += px["vrp_mw"]
    return n_mag, round(mw, 3), n_tot


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--informe", default=str(HERE / "evaluacion"))
    a = ap.parse_args(argv)
    ev = cargar_sellado()
    out_dir = Path(a.out)
    R = ev.RADIO_KM
    errores = []

    print("=" * 100)
    h1, h1a = sha_lf(RAIZ / "docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md"), hash_anotado(
        RAIZ / "experiments/_s146_a2/HASH_PRE_REGISTRO.txt")
    h2, h2a = sha_lf(HERE / "CRITERIO_NULO_POR_PIXEL.md"), hash_anotado(HERE / "HASH_CRITERIO_NULO.txt")
    print(f"criterio sellado de A2      sha256(LF) {h1}  {'COINCIDE' if h1 == h1a else 'NO COINCIDE: PRE-REGISTRO INVALIDADO'}")
    print(f"criterio del nulo por pixel sha256(LF) {h2}  {'COINCIDE' if h2 == h2a else 'NO COINCIDE: PRE-REGISTRO INVALIDADO'}")

    casos = {c["caso"]: c for c in yaml.safe_load(
        (RAIZ / "experiments/_s136/apendice_a.yaml").read_text(encoding="utf-8"))["casos"]}
    orden = sorted(casos)
    datos, etiquetas = {}, {}
    for b in B.como_dicts():
        f = out_dir / b["nombre"] / "resultado_apendice.json"
        if f.exists():
            datos[b["nombre"]] = {c["caso"]: c for c in json.loads(f.read_text(encoding="utf-8"))}
            etiquetas[b["nombre"]] = b["etiqueta"]
    if not datos:
        print(f"ERROR: no hay ninguna salida de brazo en {out_dir}")
        return 1
    print(f"brazos con salida: {len(datos)}  ({', '.join(etiquetas.values())})")
    presentes = sorted({k for d in datos.values() for k in d})
    if presentes != orden:
        print(f"AVISO: corrida parcial, casos presentes {presentes}. Los totales de 9 no aplican.")

    cumbre_a2 = (casos["A2"]["lat"], casos["A2"]["lon"])
    D_FIS, R_FIS = ev.hav(*cumbre_a2, *ev.FISURA["A2"]), ev.rumbo(*cumbre_a2, *ev.FISURA["A2"])
    print(f"fisura GVP a {D_FIS:.2f} km rumbo {R_FIS:.1f} de la cumbre ; radio de caja {R} km")
    informe = {"hash_criterio_a2": h1, "hash_criterio_a2_coincide": h1 == h1a,
               "hash_criterio_nulo": h2, "hash_criterio_nulo_coincide": h2 == h2a,
               "fisura": {"dist_km": round(D_FIS, 3), "rumbo": round(R_FIS, 2)}, "brazos": {}}

    # ------------------------------------------------------------ Cpx-d identidad con lo commiteado
    print("\n" + "=" * 100 + "\nCpx-d IDENTIDAD: vara vieja sobre las salidas NUEVAS vs veredicto commiteado en S136/S137")
    ig = tot = 0
    for b in B.como_dicts():
        if b["nombre"] not in datos or not b["commiteado"]:
            continue
        viejo = {c["caso"]: c for c in json.loads(
            (RAIZ / b["commiteado"] / "resultado_apendice.json").read_text(encoding="utf-8"))}
        for k in datos[b["nombre"]]:
            v, _ = ev.veredicto(casos[k], datos[b["nombre"]][k]["pasadas"], None, R)
            tot += 1
            if v == viejo[k]["resultado"]:
                ig += 1
            else:
                print(f"  DERIVA  {b['etiqueta']}  {k}: hoy={v!r}  commiteado={viejo[k]['resultado']!r}")
    print(f"  reproduce {ig} de {tot}" + ("" if ig == tot else
          "   -> el pipeline o los granulos cambiaron desde el 13-09-2026; comparar con cuidado"))
    informe["Cpx_d"] = {"iguales": ig, "total": tot}

    # ------------------------------------------------------------ Cpx-a integridad de la captura
    print("\n" + "=" * 100 + "\nCpx-a INTEGRIDAD DE LA CAPTURA: cumulos vs pixeles listados, y primario vs record")
    n_pas = n_malas = 0
    for nom, d in datos.items():
        for k, c in d.items():
            for p in c["pasadas"]:
                n_pas += 1
                prob = list(p.get("captura_discrepancias") or [])
                if "pixeles_alertados" not in p or "cumulos" not in p:
                    prob.append("la pasada no trae cumulos/pixeles_alertados (salida de formato viejo)")
                else:
                    for origen in {c2["origen"] for c2 in p["cumulos"]}:
                        s = sum(c2["n_pixels"] for c2 in p["cumulos"] if c2["origen"] == origen)
                        n = sum(1 for px in p["pixeles_alertados"] if px["origen"] == origen)
                        if s != n:
                            prob.append(f"{origen}: {s} pixeles en cumulos vs {n} listados")
                    prim = [c2 for c2 in p["cumulos"] if c2["es_primario_publicado"]]
                    if p.get("pc_lat") is not None and len(prim) != 1:
                        prob.append(f"el record trae primario y la captura marca {len(prim)}")
                if prob:
                    n_malas += 1
                    print(f"  NO CUADRA  {etiquetas[nom]}  {k}  {p['granule']}: {prob}")
    print(f"  pasadas revisadas {n_pas} ; con problemas {n_malas}")
    if n_malas:
        errores.append(f"Cpx-a: {n_malas} pasadas donde la captura no cuadra")
    informe["Cpx_a"] = {"pasadas": n_pas, "con_problemas": n_malas}

    # ------------------------------------------------------------ veredicto sellado + nulos por pixel
    giros = [90.0, 180.0, 270.0]
    for nom, d in datos.items():
        et = etiquetas[nom]
        b = informe["brazos"][et] = {"carpeta": nom, "casos": {}}
        for k in d:
            vv, _ = ev.veredicto(casos[k], d[k]["pasadas"], None, R)
            vn, dn = ev.veredicto(casos[k], d[k]["pasadas"], ev.FISURA.get(k), R)
            b["casos"][k] = {"vieja": vv, "nueva": vn, "detalle_nueva": dn}
        if "A2" in d:
            ps, _m = ev.filtro_validez(casos["A2"], d["A2"]["pasadas"])
            ps = ps or []   # A2 sin pasadas: la cobertura ya lo marca; aca no debe reventar
            n1 = []
            for g in giros:
                centro = ev.punto_desde(*cumbre_a2, D_FIS, (R_FIS + g) % 360)
                est = [ev.estado_caja(p, cumbre_a2, centro, R) for p in ps]
                n1.append("CON CUMULO" if "DENTRO" in est else ("INDET" if "INDET" in est else "VACIA"))
            b["N1_por_cumulo_primario"] = n1
            b["A2_radio3"], _ = ev.veredicto(casos["A2"], d["A2"]["pasadas"], ev.FISURA["A2"], ev.RADIO_SENS_KM)

    print("\n" + "=" * 100 + "\nTABLA BRAZO x CASO por CUMULO PRIMARIO (criterio sellado; vieja -> nueva, solo A2 puede cambiar)")
    print("%-26s" % "brazo" + "".join("%-13s" % k for k in orden))
    for et, b in informe["brazos"].items():
        print("%-26s" % et + "".join("%-13s" % (
            f"{ev.corto(b['casos'][k]['vieja'])}->{ev.corto(b['casos'][k]['nueva'])}" if k in b["casos"] else "s/d")
            for k in orden))

    print("\n" + "=" * 100 + "\nDETALLE A2: TODOS los cumulos por pasada (posicion, pixeles, MW crudos; * = primario publicado)")
    for nom, d in datos.items():
        if "A2" not in d:
            continue
        print(f"  {etiquetas[nom]}")
        for p in d["A2"]["pasadas"]:
            for c2 in p.get("cumulos") or []:
                sep = ev.hav(c2["lat"], c2["lon"], *ev.FISURA["A2"])
                print("    %s %s %-10s n_px=%-3d crudo=%9.3f MW  publicado=%s  d_cumbre=%6.2f  rumbo=%5.1f  sep_fisura=%5.2f"
                      % (p["inicio"][11:16], "*" if c2["es_primario_publicado"] else " ", c2["origen"],
                         c2["n_pixels"], c2["vrp_mw_crudo"] or 0.0, c2["vrp_mw_publicado"],
                         c2["dist_cumbre_km"], ev.rumbo(*cumbre_a2, c2["lat"], c2["lon"]), sep))

    print("\n" + "=" * 100 + f"\nNULO POR PIXEL ALERTADO (decisorio: pixeles con vrp_mw > 0 ; entre parentesis: alertados en total)")
    print(f"cajas de {R} km a {D_FIS:.2f} km de cada cumbre ; 'fis' = rumbo de la fisura, +90/+180/+270 = giradas")
    for nom, d in datos.items():
        et = etiquetas[nom]
        b = informe["brazos"][et]
        cajas, ocupadas, evaluadas, aparte = [], 0, 0, []
        sustrato = 0
        for k in d:
            cumbre = (casos[k]["lat"], casos[k]["lon"])
            for p in d[k]["pasadas"]:
                sustrato += sum(1 for px in pixeles_de(p) if (px.get("vrp_mw") or 0) > 0
                                and abs(px["dist_cumbre_km"] - D_FIS) <= R)
            for g in [0.0] + giros:
                centro = ev.punto_desde(*cumbre, D_FIS, (R_FIS + g) % 360)
                n_mag, mw, n_tot = contar_caja(ev, d[k]["pasadas"], centro, R)
                tipo = ("FISURA" if (k == "A2" and g == 0.0) else
                        "EXCLUIDA" if (k, g) in EXCLUIDAS else "N1px" if k == "A2" else "N2px")
                fila = {"caso": k, "giro": g, "rumbo": round((R_FIS + g) % 360, 1), "tipo": tipo,
                        "n_con_magnitud": n_mag, "mw": mw, "n_alertados": n_tot,
                        "estado": "OCUPADA" if n_mag else "VACIA"}
                cajas.append(fila)
                if tipo in ("N1px", "N2px"):
                    evaluadas += 1
                    ocupadas += bool(n_mag)
                elif tipo == "EXCLUIDA":
                    aparte.append(fila)
        neg = []
        for k in NEGATIVOS:
            if k in d:
                n_mag, mw, n_tot = contar_caja(ev, d[k]["pasadas"], (casos[k]["lat"], casos[k]["lon"]), R)
                neg.append({"caso": k, "n_con_magnitud": n_mag, "mw": mw, "n_alertados": n_tot,
                            "estado": "OCUPADA" if n_mag else "VACIA",
                            "veredicto_por_cumulo": b["casos"][k]["nueva"]})
        b.update({"cajas": cajas, "nulas_evaluadas": evaluadas, "nulas_ocupadas": ocupadas,
                  "excluidas": aparte, "NEGpx": neg, "sustrato_anillo": sustrato})
        print(f"\n  {et}")
        for k in d:
            fs = [c for c in cajas if c["caso"] == k]
            print("    %-3s " % k + "  ".join(
                "%s%s:%d(%d)%s" % ("fis" if c["giro"] == 0 else "+%d" % c["giro"],
                                   "[excl]" if c["tipo"] == "EXCLUIDA" else "[FISURA]" if c["tipo"] == "FISURA" else "",
                                   c["n_con_magnitud"], c["n_alertados"],
                                   (" %.2fMW" % c["mw"]) if c["n_con_magnitud"] else "") for c in fs))
        print(f"    cajas nulas ocupadas: {ocupadas} de {evaluadas}   sustrato (pixeles con magnitud en el anillo "
              f"{D_FIS - R:.2f}-{D_FIS + R:.2f} km, 9 casos): {sustrato}")
        print("    NEGpx (caja de cumbre en negativos): " + "  ".join(
            f"{n['caso']}:{n['n_con_magnitud']}({n['n_alertados']}) {n['estado']}" for n in neg))

    # ------------------------------------------------------------ reglas R1 a R4 y Cpx-b
    print("\n" + "=" * 100 + "\nVEREDICTO POR BRAZO")
    print("  A2 sellado = seccion 4 del criterio de A2 (cumulo primario + N1 por cumulo)")
    print("  A2 final   = lo anterior mas R1 (N1px por pixel) ; regalo = R2 ; reservas = R3")
    for et, b in informe["brazos"].items():
        if "A2" not in b["casos"]:
            print(f"  {et:26s} sin A2 en esta corrida")
            continue
        v = b["casos"]["A2"]["nueva"]
        if v == "CONFORME":
            sell = "ACIERTO" if all(x == "VACIA" for x in b["N1_por_cumulo_primario"]) else "INDECIDIBLE (N1 por cumulo)"
        elif v == "NO CONFORME (falso negativo)":
            sell = "FALLO"
        else:
            sell = "INDECIDIBLE (" + v + ")"
        n1px = [c for c in b["cajas"] if c["tipo"] == "N1px"]
        fis = [c for c in b["cajas"] if c["tipo"] == "FISURA"][0]
        final = sell
        if sell == "ACIERTO" and any(c["estado"] == "OCUPADA" for c in n1px):
            final = "INDECIDIBLE (R1: caja rotada ocupada por pixeles)"
        if v == "CONFORME" and fis["n_con_magnitud"] == 0:
            errores.append(f"Cpx-b/R4: {et} acierta A2 por cumulo primario y la caja de la fisura no tiene "
                           f"ningun pixel con magnitud: captura muerta")
        oc = b["nulas_ocupadas"]
        regalo = ("REGALA ACIERTOS" if oc >= CORTE_REGALA else
                  "regalo marginal" if oc >= CORTE_MARGINAL else "no regala")
        reservas = [n["caso"] for n in b["NEGpx"]
                    if n["estado"] == "OCUPADA" and n["veredicto_por_cumulo"] == "CONFORME"]
        otros = sum(1 for k, c in b["casos"].items() if k != "A2" and c["nueva"] == "CONFORME")
        total = otros + (final == "ACIERTO")
        completo = len(b["casos"]) == 9
        lectura = f"{total}/9" if completo else f"{total} de {len(b['casos'])} casos corridos"
        if reservas:
            lectura += f" con {len(reservas)} reserva(s) {reservas}"
        if completo and total == 9:
            lectura += ("  SIN VALOR DISCRIMINANTE (R2)" if regalo == "REGALA ACIERTOS" else "  APRUEBA 9/9")
        fragil = "  [fragil con radio 3 km]" if final == "ACIERTO" and b.get("A2_radio3") != "CONFORME" else ""
        print(f"  {et:26s} A2 sellado: {sell:30s} A2 final: {final}{fragil}")
        print(f"  {'':26s} fisura: {fis['n_con_magnitud']} px {fis['mw']} MW ; nulas ocupadas {oc}/{b['nulas_evaluadas']} -> {regalo} ; total {lectura}")
        b.update({"A2_sellado": sell, "A2_final": final + fragil, "regalo": regalo,
                  "reservas_negativos": reservas, "total_final": total, "lectura": lectura})

    informe["errores_de_instrumento"] = errores
    inf = Path(a.informe)
    inf.mkdir(parents=True, exist_ok=True)
    (inf / "resultado_bateria_s146.json").write_text(
        json.dumps(informe, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nescrito: {inf / 'resultado_bateria_s146.json'}")
    if errores:
        print("\nERROR DE INSTRUMENTO, los nulos NO valen:")
        for e in errores:
            print("  -", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
