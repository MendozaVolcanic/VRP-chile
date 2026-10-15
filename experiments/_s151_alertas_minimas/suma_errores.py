# -*- coding: utf-8 -*-
"""Estudio D, parte 3: cuanto cambia la suma de errores de los resultados ya medidos si las alertas minimas se
cuentan como lo que MIROVA dice de ellas.

POR QUE. El criterio de victoria (docs/MISSION.md, "Criterio de victoria de la replica", lectura A) suma, bajo
1 MW, alertas perdidas y publicaciones en negativos limpios con el mismo peso. Una pasada que el scraper llama
ALERTA y el banner de MIROVA llama NONE (frontera_salida.txt) entra hoy como alerta: si el brazo no la publica
cuenta un error, y si la publica cuenta un acierto. Si MIROVA no vio nada, los dos signos estan al reves.

Tres escenarios, sobre las MISMAS pasadas y publicaciones de cada tabla (no se re-corre ningun brazo):
  S0  la etiqueta original del evaluador (control: tiene que reproducir los totales ya publicados);
  SE  estrato aparte: la pasada minima sale de la suma (ni alerta ni negativo); la noche no cambia;
  SN  MIROVA no vio nada: las filas de alerta de la pasada minima pasan a RUTINA con VRP 0 y se re-etiqueta con
      el etiquetador del evaluador (banco_paridad.etiquetar), asi que la pasada puede volverse negativo limpio y
      las otras pasadas de esa noche tambien, si la minima era la unica alerta.
"Minima" = pasada (volcan, sensor, minuto) cuyo VRP de alerta (consolidado antes que OCR, como el evaluador) es
<= umbral. Umbral 0,05 MW y solo VIIRS 375 (frontera medida, frontera_salida.txt); VIIRS 750 con 0,15 MW va
aparte como sensibilidad, porque esa frontera descansa en UNA imagen.

Fuentes (todas en el repo salvo la referencia congelada de los meses, que esta en .gitignore):
  pasadas_meses_B_F.csv  meses de S150, control B (_s146_ab_sin_test1), brazo F (max), abril a agosto, VIIRS 375 y
                         750 (extraer_tablas.py); referencia congelada de cada mes, sha256 contra
                         experiments/_s149_prereg_invierno/_congelado/<mes>/MANIFIESTO.json.
  pasadas_ndc.csv        Chillan, run 38560317428, nueve brazos; referencia experiments/_s150_ndc/_congelado_ndc.
  D22                    la lista de perdidas de experiments/_s151_d22_techo/salida.txt.

Uso: python suma_errores.py --congelado-meses DIR > suma_salida.txt
     (DIR: carpeta con <mes>/registro_vrp_*.csv, por ejemplo la del worktree principal)
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from comun import RAIZ, TIPOS_ALERTA, cargar_referencia_unificada, pasadas_de_alerta  # noqa: E402

sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
bp = ev.bp

AQUI = Path(__file__).resolve().parent
MESES = ["abril", "mayo", "junio", "julio", "agosto"]
CONG_MESES_MANIF = RAIZ / "experiments" / "_s149_prereg_invierno" / "_congelado"
CONG_NDC = RAIZ / "experiments" / "_s150_ndc" / "_congelado_ndc"
D22 = RAIZ / "experiments" / "_s151_d22_techo" / "salida.txt"
BRAZOS_NDC = ["C0", "T0", "E", "B", "F", "J", "K", "KE", "KET"]


def sha(p: Path) -> str:
    # Con core.autocrlf=true el checkout de Windows trae CRLF; el manifiesto se calculo sobre LF (el contenido
    # commiteado). Se normaliza para comparar el contenido, no el fin de linea.
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verificar_congelado(dir_csv: Path, manifiesto: Path):
    man = json.loads(manifiesto.read_text(encoding="utf-8"))
    for nombre, info in man["archivos"].items():
        s = sha(dir_csv / nombre)
        if s != info["sha256"]:
            raise SystemExit(f"{dir_csv / nombre}: sha256 {s} no coincide con el manifiesto {info['sha256']}")
    return man["ventana"]


def cargar_ref(dir_csv: Path, historico: bool):
    capas = {} if historico else {"historico_path": None}
    return cargar_referencia_unificada(dir_csv / "registro_vrp_consolidado.csv", dir_csv / "registro_vrp_ocr.csv", **capas)


def leer_pasadas(path: Path, brazos, filtro=None):
    """{grupo: {clave: {"lab", "vrp_ref", "pub": {brazo: 0|1}}}}; un brazo en blanco no publica ni se cuenta."""
    out = defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if filtro and not filtro(r):
                continue
            pub = {b: int(r["pub_" + b]) for b in brazos if r.get("pub_" + b, "") != ""}
            out[r.get("mes", "ndc")][r["clave"]] = {"lab": r["lab"], "vrp_ref": float(r["vrp_ref"]) if r["vrp_ref"] else None,
                                                    "pub": pub, "ventana": r["ventana"].split("|")}
    return out


def minimas(filas, umbrales) -> set:
    P = pasadas_de_alerta(filas)
    return {k for k, v in P.items() if k[1] in umbrales and v["vrp"] <= umbrales[k[1]] + 1e-9}


def escenario_sn(filas, mins):
    out = []
    for f in filas:
        k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
        if k in mins and f["tipo"] in TIPOS_ALERTA:
            f = copy.copy(f)
            f["tipo"], f["vrp_mw"] = "RUTINA", 0.0
        out.append(f)
    return out


def etiquetar(filas, claves, ventana):
    """Etiquetas del evaluador para pasadas dadas por su clave 'vol|sensor|AAAA-MM-DD HH:MM'."""
    coords = bp._coords_por_volcan()
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, tuple(ventana))
    recs = []
    for c in claves:
        vol, b, t = c.split("|")
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "clave": c})
    bp.etiquetar(recs, por_vb, ns, nv)
    ev.anotar_vrp_mirova(recs, por_vb)
    return {r["clave"]: (r["lab"], r.get("vrp_ref")) for r in recs}


def indice_minimas(mins):
    # Sin cache. La primera version guardaba este indice por id(mins); Python reusa ese id entre meses y julio y
    # agosto salian con el indice de otro mes (SE excluia 0 pasadas mientras SN cambiaba 15). Lo detecto la
    # comparacion entre SE y SN; el control 2 de evaluar() lo vigila ahora.
    d = defaultdict(list)
    for m in mins:
        d[(m[0], m[1])].append(datetime.strptime(m[2][:16], "%Y-%m-%d %H:%M"))
    return d


def minima_pareada(clave, idx):
    """La pasada nuestra es minima si una pasada minima de la referencia esta a +-120 s (pareo del evaluador)."""
    vol, b, t = clave.split("|")
    dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
    return any(abs((dm - dt).total_seconds()) <= 120 for dm in idx.get((vol, b), []))


def contar(pas, brazo, etq, sensores, idx=None):
    """Suma de errores del criterio bajo 1 MW: alertas Muy Bajo sin publicar + publicaciones en negativos limpios.
    Con `idx`, escenario SE: las alertas minimas salen de la cuenta."""
    c = Counter()
    for k, v in pas.items():
        if brazo not in v["pub"] or k.split("|")[1] not in sensores:
            continue
        lab, vrp = etq[k]
        pub = v["pub"][brazo]
        if idx is not None and lab == "pos" and minima_pareada(k, idx):
            c["excluidas"] += 1
            continue
        if lab == "pos":
            if vrp is not None and vrp >= 1.0:
                c["prot"] += 1
                c["prot_perdidas"] += 1 - pub
            else:
                c["pos"] += 1
                c["perdidas"] += 1 - pub
        elif lab == "neg_limpio":
            c["neg"] += 1
            c["fp"] += pub
    c["suma"] = c["perdidas"] + c["fp"]
    return c


def linea(nombre, c):
    return (f"{nombre:4s} alertas Muy Bajo perdidas {c['perdidas']:4d} de {c['pos']:4d} | negativos limpios publicados "
            f"{c['fp']:4d} de {c['neg']:4d} | SUMA {c['suma']:4d} | protegidas perdidas {c['prot_perdidas']} de {c['prot']}"
            + (f" | excluidas {c['excluidas']}" if c["excluidas"] else ""))


def evaluar(pas, filas, ventana, brazos, sensores, umbrales, imprimir=True):
    claves = sorted(pas)
    e0 = etiquetar(filas, claves, ventana)
    # Control 1: el etiquetador re-corrido sobre la referencia congelada reproduce la etiqueta guardada.
    malas = sum(1 for k in claves if (pas[k]["lab"], pas[k]["vrp_ref"]) != e0[k])
    mins = minimas(filas, umbrales)
    idx = indice_minimas(mins)
    sn = etiquetar(escenario_sn(filas, mins), claves, ventana)
    cambio = Counter((e0[k][0], sn[k][0]) for k in claves if e0[k][0] != sn[k][0] and k.split("|")[1] in sensores)
    res, fallos_se = {}, []
    for b in brazos:
        r = (contar(pas, b, e0, sensores), contar(pas, b, e0, sensores, idx), contar(pas, b, sn, sensores))
        res[b] = r
        # Control 2: lo que SE excluye por pareo es lo que la etiqueta original marca como alerta con VRP <= umbral.
        directo = sum(1 for k, v in pas.items() if b in v["pub"] and k.split("|")[1] in sensores and e0[k][0] == "pos"
                      and e0[k][1] is not None and e0[k][1] <= umbrales.get(k.split("|")[1], -1) + 1e-9)
        if directo != r[1]["excluidas"]:
            fallos_se.append((b, r[1]["excluidas"], directo))
    if imprimir:
        print(f"   control 1, re-etiquetado S0 igual a la tabla: {len(claves) - malas} de {len(claves)} pasadas")
        print(f"   control 2, SE excluye lo mismo que marca la etiqueta original: {'OK' if not fallos_se else 'FALLA ' + str(fallos_se)}")
        print(f"   etiquetas que cambian de S0 a SN: {dict(cambio)}")
        for esc, i in (("S0 (etiqueta original)", 0), ("SE (estrato aparte)", 1), ("SN (MIROVA no vio nada)", 2)):
            print(f"   {esc}")
            for b, r in res.items():
                print("     " + linea(b, r[i]))
    return res, malas, fallos_se


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--congelado-meses", required=True, help="carpeta con <mes>/registro_vrp_*.csv (en .gitignore)")
    a = ap.parse_args()

    print("== 1. MESES de S150 (control B sin Test 1, brazo F = max), abril a agosto")
    for titulo, umbrales, sensor in (("VIIRS 375, umbral 0,05", {"VIIRS375": 0.05}, "VIIRS375"),
                                     ("VIIRS 750, SENSIBILIDAD con umbral 0,15", {"VIIRS750": 0.15}, "VIIRS750")):
        print(f"\n## {titulo}")
        grupos = leer_pasadas(AQUI / "pasadas_meses_B_F.csv", ["B", "F"], lambda r, s=sensor: f"|{s}|" in r["clave"])
        tot = defaultdict(Counter)
        for mes in MESES:
            pas = grupos[mes]
            ventana = verificar_congelado(Path(a.congelado_meses) / mes, CONG_MESES_MANIF / mes / "MANIFIESTO.json")
            if next(iter(pas.values()))["ventana"] != list(ventana):
                raise SystemExit(f"{mes}: ventana de la tabla distinta de la del manifiesto {ventana}")
            print(f"\n-- {mes} {ventana}")
            res, _, _ = evaluar(pas, cargar_ref(Path(a.congelado_meses) / mes, historico=False), ventana,
                                ["B", "F"], (sensor,), umbrales)
            for b, r in res.items():
                for i in range(3):
                    tot[(b, i)].update(r[i])
        print(f"\n## TOTAL abril a agosto, {titulo}")
        for i, esc in enumerate(("S0", "SE", "SN")):
            for b in ("B", "F"):
                c = tot[(b, i)]
                c["suma"] = c["perdidas"] + c["fp"]
                print(f"   {esc} " + linea(b, c))

    print("\n== 2. CHILLAN (run 38560317428), los tres sensores, umbral 0,05 en VIIRS 375")
    ventana = verificar_congelado(CONG_NDC, CONG_NDC / "MANIFIESTO.json")
    pas = leer_pasadas(AQUI / "pasadas_ndc.csv", BRAZOS_NDC)["ndc"]
    # Las tablas de Chillan se armaron con el cargador por defecto del dia (#778, la capa historica de la union, se
    # mergeo esa misma manana): se prueba con y sin ella y se usa la que reproduce las etiquetas.
    mejor = None
    for historico in (True, False):
        _, malas, _ = evaluar(pas, cargar_ref(CONG_NDC, historico), ventana, BRAZOS_NDC,
                              ("MODIS", "VIIRS375", "VIIRS750"), {"VIIRS375": 0.05}, imprimir=False)
        print(f"   con la capa historica {'SI' if historico else 'NO'}: re-etiquetado distinto en {malas} de {len(pas)}")
        if mejor is None or malas < mejor[0]:
            mejor = (malas, historico)
    evaluar(pas, cargar_ref(CONG_NDC, mejor[1]), ventana, BRAZOS_NDC, ("MODIS", "VIIRS375", "VIIRS750"), {"VIIRS375": 0.05})

    print("\n== 3. D22 (experiments/_s151_d22_techo/salida.txt): perdidas confiables de max por el camino D22")
    vrps = [float(m.group(1)) for m in re.finditer(r"VRP MIROVA\s+([0-9.]+) MW", D22.read_text(encoding="utf-8"))]
    print(f"   perdidas listadas {len(vrps)}; con VRP <= 0,05: {sum(v <= 0.05 + 1e-9 for v in vrps)} "
          f"(<= 0,04: {sum(v <= 0.04 + 1e-9 for v in vrps)}; 0,05 exacto: {sum(abs(v - 0.05) < 1e-9 for v in vrps)}); "
          f"techo de ganancia del A/B de D22 si esas no cuentan como alerta: {sum(v > 0.05 + 1e-9 for v in vrps)} "
          f"(con 0,05 dudoso: entre {sum(v > 0.05 + 1e-9 for v in vrps)} y {sum(v > 0.04 + 1e-9 for v in vrps)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
