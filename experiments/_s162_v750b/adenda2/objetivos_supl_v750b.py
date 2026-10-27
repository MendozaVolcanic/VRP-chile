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

CONTROL (si falla, sale 1 y no escribe la lista del run): las pasadas `pos` y `neg_limpio` de esta corrida, con los
mismos cortes, tienen que ser exactamente las de la lista sellada que se pasa en --sellado (mismo volcán, hora y
gránulo). Así se ve que el cambio de filtro no tocó la población sellada, y que las dos listas salieron de los mismos
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
V750B = AQUI.parent
RAIZ = V750B.parents[1]
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


def clave(o):
    return (o["volcan"], o["hora_utc"], o.get("granule"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    ap.add_argument("--hasta", required=True, help="último día de la ventana (YYYY-MM-DD), el mismo de la lista sellada")
    ap.add_argument("--sellado", required=True, help="objetivos_v750b.json generado el mismo día con objetivos_v750b.py")
    ap.add_argument("--dest", default=str(AQUI))
    a = ap.parse_args()
    dest = Path(a.dest)
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
    (dest / "poblacion_supl.json").write_text(pob_txt, encoding="utf-8")
    crudo.unlink()
    pob = json.loads(pob_txt)["pasadas"]
    pob = [p for p in pob if p["hora_utc"][:10] not in GS.EXCLUIDOS and p["hora_utc"] < GS.CORTE_SNPP]

    # control: pos y neg_limpio con gránulo = la lista sellada
    sellado = json.loads(Path(a.sellado).read_text(encoding="utf-8"))
    pn = sorted(clave(p) for p in pob if p["lab"] in ("pos", "neg_limpio") and p.get("granule"))
    ss = sorted(clave(o) for o in sellado)
    igual = pn == ss
    print(f"== control: pos y neg_limpio de esta corrida contra la lista sellada: {len(pn)} contra {len(ss)}, "
          f"{'IGUALES' if igual else 'DISTINTAS'}")
    if not igual:
        faltan, sobran = sorted(set(ss) - set(pn))[:10], sorted(set(pn) - set(ss))[:10]
        print("   en la sellada y no acá:", faltan, "| acá y no en la sellada:", sobran)
        print("== no se escribe la lista suplementaria: las dos listas no salieron de los mismos datos")
        return 1

    far = [p for p in pob if p["lab"] == "far_ref"]
    sin_g = [(p["volcan"], p["hora_utc"], p["lab"], p.get("protegida")) for p in far if not p.get("granule")]
    far = [p for p in far if p.get("granule")]
    SEL = GS._modulo("sel", GS.N_DIR / "02_seleccion.py")
    grillas = SEL.grillas()
    for p in far:
        p["grilla"] = grillas[SEL.TIF.get(p["volcan"], p["volcan"])]
        fp = [f for f in p.get("mirova") or [] if str(f.get("tipo", "")).startswith("FALSO_POSITIVO")]
        p["dist_ref"] = next((f["dist_km"] for f in fp if f.get("dist_km") is not None), None)
        p["en_sc"] = False
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    sys.path.insert(0, str(RAIZ / "scripts"))
    import banco_paridad as B
    GS.completar(far, vy, B.inner_desde_html())
    far.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for n, e in enumerate(far):
        e["id"] = ID0 + n
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
    print(f"far_ref con gránulo: {len(far)} | sin gránulo (SIN DATO declarado): {len(sin_g)} {sin_g[:20]}")
    print(f"sha256 sellada {sha_sell}")
    print(f"sha256 suplementaria {sha_supl}")
    print(f"sha256 lista del run {hashlib.sha256(run.encode('utf-8')).hexdigest()} ({len(sellado)} + {len(far)} pasadas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
