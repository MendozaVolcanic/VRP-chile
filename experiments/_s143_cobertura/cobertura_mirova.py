# -*- coding: utf-8 -*-
"""S143: la cuenta de credibilidad, en dos columnas separadas.

POR QUÉ. Nicolás lo puso como el criterio que ordena el proyecto: «para que nos crean tenemos que
tener al menos todo lo que MIROVA publica», y lo que mejora la detección y MIROVA no tiene va al
perfil experimental, aparte. Ese par de números tiene que poder mirarse de un vistazo, por sensor y
por volcán, y siempre con su denominador y su ventana (A90):

  * **Lo que reproducimos**: de las pasadas y noches en que MIROVA publicó una alerta, en cuántas
    nuestro dashboard publica también (recall). Es la columna que da credibilidad.
  * **Lo que agregamos**: en las pasadas donde MIROVA miró y no vio nada (negativo limpio), en
    cuántas publicamos igual. Parte de eso es señal real sub-umbral (A54) y parte es artefacto
    (A69); esta cuenta NO los distingue, por eso se lee como «lo que hay que explicar», no como
    error ni como mérito.

No recalcula nada: lee `experiments/_s142_linea_base/linea_base_post535.json`, que lo produce
`linea_base_post535.py` con el predicado del dashboard ejecutado con node. Regla S91: ningún número
de la tabla se escribe a mano.

USO: python experiments/_s143_cobertura/cobertura_mirova.py [--tramo despues_571]
Escribe docs/audit_s143/COBERTURA_MIROVA.md
"""
import argparse
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FUENTE = ROOT / "experiments" / "_s142_linea_base" / "linea_base_post535.json"
DEST = ROOT / "docs" / "audit_s143" / "COBERTURA_MIROVA.md"
SENSORES = ["MODIS", "VIIRS375", "VIIRS750", "CUALQUIERA"]
N_MIN = 20  # bajo esto, la tasa no se interpreta (se marca)


def pct(x):
    return "s/d" if x is None else f"{100 * x:.1f} %"


def celda(d, clave="recall_pos"):
    n = d.get("n_pos") if clave == "recall_pos" else d.get("n_neg_limpio", d.get("n_neg"))
    v = d.get(clave)
    if not n:
        return "sin casos"
    marca = "" if n >= N_MIN else " (n<20)"
    return f"{pct(v)} de {n}{marca}"


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tramo", default="despues_571")
    a = ap.parse_args(argv)
    d = json.loads(FUENTE.read_text(encoding="utf-8"))
    t = d["tramos"][a.tramo]
    ini, fin = t["ventana_noches_utc"]
    meta = d["meta"]

    L = [f"# Cobertura de lo que MIROVA publica, y lo que publicamos de más",
         "",
         f"> Generado por `experiments/_s143_cobertura/cobertura_mirova.py` desde",
         f"> `experiments/_s142_linea_base/linea_base_post535.json` ({meta['generado_utc']}). Ningún",
         f"> número escrito a mano (S91). Ventana: **{ini} a {fin}**, {t['n_noches']} noches, régimen",
         f"> posterior al PR #571 (A104: una ventana que cruce el #535 mezcla dos regímenes y no se",
         f"> puede leer). Referencia de MIROVA: CONS `{meta['referencia']['registro_vrp_consolidado.csv']}`,",
         f"> OCR `{meta['referencia']['registro_vrp_ocr.csv']}`. Publicar = predicado del dashboard",
         f"> ejecutado con node.",
         "",
         "**Las dos cuentas van separadas a propósito.** La primera es la que da credibilidad: de lo",
         "que MIROVA publicó, cuánto publicamos también. La segunda es lo que publicamos donde MIROVA",
         "miró y no vio nada: ahí conviven señal real sub-umbral (A54) y artefacto topográfico (A69),",
         "y esta tabla no los separa. Lo que mejora la detección y MIROVA no tiene va al perfil",
         "`experimental`, nunca mezclado con la serie operacional.",
         "",
         "## 0. Lo que hoy NO reproducimos (la lista que hay que dejar en cero)",
         ""]
    faltas = []
    for vol, por_s in sorted(t["por_volcan"].items()):
        for s in ("MODIS", "VIIRS375", "VIIRS750"):
            v = (por_s.get(s) or {}).get("pasada") or {}
            n, r = v.get("n_pos") or 0, v.get("recall_pos")
            if n and r is not None and r < 1.0:
                faltas.append(f"- **{vol}, {s}**: reproducimos {pct(r)} de {n} pasadas con alerta"
                              f"{' (n<20, no se interpreta la tasa; son casos para mirar uno a uno)' if n < N_MIN else ''}.")
        nv = (por_s.get("CUALQUIERA") or {}).get("noche_volcan") or {}
        if (nv.get("n_pos") or 0) and (nv.get("recall_pos") or 1) < 1.0:
            faltas.append(f"- **{vol}, noche de volcán con cualquier sensor**: {pct(nv['recall_pos'])} "
                          f"de {nv['n_pos']} noches. Esta es la que importa para la alerta.")
    L += faltas or ["Ninguna: en esta ventana no hay volcán ni sensor con alertas de MIROVA que perdamos."]
    L += ["",
         "## 1. Por sensor",
         "",
         "| sensor | reproducimos, por pasada | reproducimos, por noche de volcán | publicamos de más, por pasada | alertas de MIROVA sin record nuestro |",
         "|---|---|---|---|---|"]
    for s in SENSORES:
        v = t["por_sensor"].get(s)
        if not v:
            continue
        L.append(f"| {s} | {celda(v['pasada'])} | {celda(v['noche_volcan'])} | "
                 f"{celda(v['pasada'], 'tasa_pub_neg')} | {v['pasada'].get('pos_sin_record', 0)} |")

    L += ["", "## 2. Por volcán (VIIRS 375, que es donde vive el frente abierto)", "",
          "| volcán | reproducimos, por pasada | reproducimos, por noche | publicamos de más, por pasada |",
          "|---|---|---|---|"]
    for vol, por_s in sorted(t["por_volcan"].items()):
        v = por_s.get("VIIRS375")
        if not v:
            continue
        L.append(f"| {vol} | {celda(v['pasada'])} | {celda(v['noche_volcan'])} | "
                 f"{celda(v['pasada'], 'tasa_pub_neg')} |")

    c = t["controles"]
    L += ["", "## 3. Controles del instrumento", "",
          f"- Identidad del predicado (node contra el dashboard): **{c['identidad_predicado']}**.",
          f"- Con un predicado que publica todo: recall 1,0 y publicación de más 1,0 por construcción.",
          f"- Con uno que no publica nada: 0,0 y 0,0. Las dos cotas se calculan en cada corrida, así que",
          "  una tasa pegada a un extremo se distingue de un instrumento roto.",
          "",
          "## 4. Cómo leer esto",
          "",
          "1. **Una tasa con n < 20 no se interpreta**: va marcada y sirve para saber que falta muestra,",
          "   no para concluir. VIIRS 750 en el régimen actual tiene pocas alertas.",
          "2. **La segunda columna no es precisión.** No hay forma de decir, sin mirar caso a caso, si una",
          "   publicación en negativo limpio es calor real que MIROVA no alcanza a ver o ruido del",
          "   gradiente topográfico. El A/B abierto (D22 y D25) ataca exactamente esa cuenta.",
          "3. **Las alertas de MIROVA sin record nuestro** son el número más grave si deja de ser cero:",
          "   significa que ni siquiera procesamos esa pasada."]
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"escrito {DEST.relative_to(ROOT).as_posix()}")
    for s in SENSORES:
        v = t["por_sensor"].get(s)
        if v:
            print(f"  {s:10s} recall pasada {celda(v['pasada']):18s} de más {celda(v['pasada'], 'tasa_pub_neg')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
