# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 2 (diagnóstico de posición): lista SUPLEMENTARIA de objetivos con las pasadas en que MIROVA
publicó una fuente lejana (etiqueta `far_ref` de banco_paridad: fila FALSO_POSITIVO y ninguna ALERTA).

POR QUÉ. Nicolás decidió (2026-10-27, programa §7) medir la regla de posición del record como tres brazos (radiante,
cercano y pico) contra lo que publica MIROVA, incluidas las pasadas en que MIROVA ubicó el calor lejos del cráter. La
población sellada de V750-B (`experiments/_s159/n/01_poblacion.py`, l. 106 en main) sólo toma `pos` y `neg_limpio`,
así que esas pasadas no están en los objetivos. Este script NO toca la lista sellada: corre la misma población con
la misma lógica, cambiando sólo el filtro de etiquetas para dejar pasar también `far_ref`, aplica los mismos cortes
del generador sellado (días excluidos, cese de Suomi NPP, sin gránulo afuera) y escribe aparte:

  objetivos_supl_v750b.json     las pasadas far_ref, con ids desde 100000 (nunca chocan con los sellados);
  sin_granulo_supl_v750b.json   las far_ref sin gránulo, atadas por sha256 a la lista suplementaria;
  objetivos_run_v750b.json      la lista sellada seguida de la suplementaria: es la que lee el run (OBJETIVOS);
  poblacion_supl.json           la población completa de esta corrida (para auditar).

CONTROL (si falla, sale 1 y no escribe ninguna lista): las pasadas `pos` y `neg_limpio` de esta corrida, con los
mismos cortes, tienen que ser exactamente las de la lista sellada que se pasa en --sellado (volcán, hora, gránulo,
etiqueta, protegida, alerta de la tabla y si decide). Se niega a escribir en la carpeta sellada o encima de salidas
de otra corrida (sale 2; no borra nada). Así se ve que el cambio de filtro no tocó la población sellada, y que las dos listas salieron de los mismos
records y de la misma referencia.

Uso (sobre el main del día del despacho, después de generar la lista sellada con objetivos_v750b.py):
  python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest <carpeta>
      --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
V750B = Path(r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750b')
RAIZ = Path(r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174')
FILTRO_SELLADO = 'if r["lab"] not in ("pos", "neg_limpio"):'
FILTRO_SUPL = 'if r["lab"] not in ("pos", "neg_limpio", "far_ref"):'
ID0 = 100000


def poblacion_con_far_ref(ruta):
    """Carga 01_poblacion.py cambiando SÓLO su filtro de etiquetas; falla si el filtro no aparece exactamente una vez."""
    src = Path(ruta).read_text(encoding="utf-8")
    n = src.count(FILTRO_SELLADO)
    if n != 1:
        raise SystemExit(f"01_poblacion.py: el filtro de etiquetas aparece {n} veces (tiene que ser 1): no se genera")
    m = type(sys)("pob_supl")
    m.__file__ = str(ruta)
    exec(compile(src.replace(FILTRO_SELLADO, FILTRO_SUPL), str(ruta), "exec"), m.__dict__)
    return m


SALIDAS = ("objetivos_supl_v750b.json", "sin_granulo_supl_v750b.json", "objetivos_run_v750b.json", "poblacion_supl.json",
           "poblacion_completa.json")
CAMPOS_CONTROL = ("volcan", "hora_utc", "granule", "lab", "protegida", "alerta_tabla", "decide")


def clave(o):
    """Lo que tiene que coincidir entre una pasada de esta corrida y la de la lista sellada (VAD2-08: no sólo la hora)."""
    return tuple(json.dumps(o.get(k), sort_keys=True, default=str) for k in CAMPOS_CONTROL)


def recortar(pob, excluidos, corte):
    """Los mismos cortes del generador sellado: días excluidos y cese de Suomi NPP."""
    return [p for p in pob if p["hora_utc"][:10] not in excluidos and p["hora_utc"] < corte]


def comparar(pob, sellado):
    """Control: pos y neg_limpio con gránulo de esta corrida = la lista sellada, campo por campo de CAMPOS_CONTROL."""
    pn = sorted(clave(p) for p in pob if p["lab"] in ("pos", "neg_limpio") and p.get("granule"))
    ss = sorted(clave(o) for o in sellado)
    return pn == ss, pn, ss


def seleccionar_far(pob):
    """(far_ref con gránulo, far_ref sin gránulo). dist_ref: la distancia de la primera fila FALSO_POSITIVO con distancia
    (nunca de una fila ALERTA o RUTINA; una pasada far_ref no tiene ALERTA por definición)."""
    far = [dict(p) for p in pob if p["lab"] == "far_ref"]
    sin_g = [(p["volcan"], p["hora_utc"], p["lab"], p.get("protegida")) for p in far if not p.get("granule")]
    far = [p for p in far if p.get("granule")]
    for p in far:
        fp = [f for f in p.get("mirova") or []]
        p["dist_ref"] = next((f["dist_km"] for f in fp if f.get("dist_km") is not None), None)
        p["en_sc"] = False
    return far, sin_g


def numerar(far):
    far.sort(key=lambda e: (e["granule"] or "", e["volcan"], e["hora_utc"]))
    for n, e in enumerate(far):
        e["id"] = ID0 + n
    return far


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    ap.add_argument("--hasta", required=True, help="último día de la ventana (YYYY-MM-DD), el mismo de la lista sellada")
    ap.add_argument("--sellado", required=True, help="objetivos_v750b.json generado el mismo día con objetivos_v750b.py")
    ap.add_argument("--dest", default=str(AQUI))
    a = ap.parse_args()
    dest = Path(a.dest)
    # VAD2-03 y VAD2-09: nunca en la carpeta sellada ni encima de una corrida anterior (no se borra nada)
    if dest.resolve() == V750B.resolve():
        print(f"--dest no puede ser la carpeta sellada ({V750B}): pisaría su poblacion_completa.json")
        return 2
    previos = [n for n in SALIDAS if (dest / n).exists()]
    if previos:
        print(f"en {dest} ya hay salidas de otra corrida {previos}: usa una carpeta nueva (no se escribe encima)")
        return 2
    dest.mkdir(parents=True, exist_ok=True)
    G = V750B / "objetivos_v750b.py"
    spec = importlib.util.spec_from_file_location("gen_sellado", G)
    GS = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GS)

    P = poblacion_con_far_ref(GS.N_DIR / "01_poblacion.py")
    P.VENTANA = ("2026-04-01", a.hasta)
    P.AQUI = dest                       # escribe poblacion_completa.json en dest; se renombra abajo
    sys.argv = ["01_poblacion.py", "--data", a.data, "--ref-dest", a.ref_dest]
    P.main()
    crudo = dest / "poblacion_completa.json"
    pob_txt = crudo.read_text(encoding="utf-8")
    pob = recortar(json.loads(pob_txt)["pasadas"], GS.EXCLUIDOS, GS.CORTE_SNPP)

    sellado = json.loads(Path(a.sellado).read_text(encoding="utf-8"))
    igual, pn, ss = comparar(pob, sellado)
    print(f"== control: pos y neg_limpio de esta corrida contra la lista sellada ({', '.join(CAMPOS_CONTROL)}): "
          f"{len(pn)} contra {len(ss)}, {'IGUALES' if igual else 'DISTINTAS'}")
    if not igual:
        faltan, sobran = sorted(set(ss) - set(pn))[:10], sorted(set(pn) - set(ss))[:10]
        print("   en la sellada y no acá:", faltan, "| acá y no en la sellada:", sobran)
        crudo.rename(dest / "poblacion_supl_CONTROL_FALLIDO.json")
        print("== no se escribe ninguna lista: las dos no salieron de los mismos datos (la población queda como "
              "poblacion_supl_CONTROL_FALLIDO.json para auditar)")
        return 1
    crudo.rename(dest / "poblacion_supl.json")

    far, sin_g = seleccionar_far(pob)
    SEL = GS._modulo("sel", GS.N_DIR / "02_seleccion.py")
    grillas = SEL.grillas()
    for p in far:
        p["grilla"] = grillas[SEL.TIF.get(p["volcan"], p["volcan"])]
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    sys.path.insert(0, str(RAIZ / "scripts"))
    import banco_paridad as B
    GS.completar(far, vy, B.inner_desde_html())
    numerar(far)
    texto = json.dumps(far, ensure_ascii=False, default=str)
    sha_supl = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    (dest / "objetivos_supl_v750b.json").write_text(texto, encoding="utf-8")
    (dest / "sin_granulo_supl_v750b.json").write_text(json.dumps(
        {"objetivos_sha256": sha_supl,
         "pasadas": [{"volcan": v, "hora_utc": h, "lab": lab, "protegida": pr} for v, h, lab, pr in sin_g]},
        ensure_ascii=False), encoding="utf-8")
    run = json.dumps(sellado + far, ensure_ascii=False, default=str)
    (dest / "objetivos_run_v750b.json").write_text(run, encoding="utf-8")
    sha_sell = hashlib.sha256(Path(a.sellado).read_bytes()).hexdigest()
    print(f"far_ref con gránulo: {len(far)} | sin gránulo (SIN DATO declarado): {len(sin_g)} {sin_g}")
    print(f"sha256 sellada {sha_sell}")
    print(f"sha256 suplementaria {sha_supl}")
    print(f"sha256 lista del run {hashlib.sha256(run.encode('utf-8')).hexdigest()} ({len(sellado)} + {len(far)} pasadas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
