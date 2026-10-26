# -*- coding: utf-8 -*-
"""MOD-D: cuenta, parte por parte, las pasadas de una tanda contra las que la población congelada espera (A108).

POR QUÉ. Un run 100 % verde no prueba cobertura pareja: en S143, 3 de 108 jobs verdes quedaron con pasadas de menos por
cortes de NASA. Antes de leer cualquier veredicto, cada parte tiene que traer exactamente los records de sus gránulos,
sin repetidos, con estado «ok», y un pie con 0 errores. Esto no decide nada: dice si la tanda se puede leer o hay que
repetir una parte.

Las dos preguntas del instrumento: (1) si faltara una pasada, ¿se vería? Sí: se compara (volcán, hora) contra la
población de cada parte. (2) Si la carpeta estuviera vacía o fuera de otra tanda, ¿se vería? Sí: se exige una cabecera
por parte con el commit esperado y la parte que corresponde.
Uso: python -I contar_tanda.py --art D:/vrp-trabajo/temporales/s162_modd/t1/run_40336655402 --partes 0-7
     [--poblacion experiments/_s162_mxd03/poblacion.json] [--commit 865174abeea01a1bad726ce25dd70cf0d00ae7eb]
"""
import argparse
import collections
import glob
import json
import sys
from pathlib import Path

COMMIT = "865174abeea01a1bad726ce25dd70cf0d00ae7eb"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--partes", required=True, help="rango, ej. 0-7")
    ap.add_argument("--poblacion", required=True)
    ap.add_argument("--commit", default=COMMIT)
    a = ap.parse_args()
    i0, i1 = (int(x) for x in a.partes.split("-"))
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    por_clave = {g["clave"]: g for g in pob["granulos"]}
    malas = []
    tot = collections.Counter()
    for parte in range(i0, i1 + 1):
        esperadas = {(f["vol"], f["dt"]) for c in pob["partes"][parte] for f in por_clave[c]["records"]}
        archivos = glob.glob(str(Path(a.art) / "**" / ("ab_parte%02d.jsonl" % parte)), recursive=True)
        if len(archivos) != 1:
            malas.append((parte, "archivos ab_parte: %d" % len(archivos)))
            continue
        filas = [json.loads(x) for x in open(archivos[0], encoding="utf-8")]
        cab = [r for r in filas if r.get("tipo") == "cabecera"]
        rec = [r for r in filas if r.get("tipo") == "record"]
        pie = [r for r in filas if r.get("tipo") == "pie"]
        vistos = collections.Counter((r.get("vol"), r.get("dt")) for r in rec)
        estados = collections.Counter(r.get("estado") for r in rec)
        port = collections.Counter(r.get("port_estado") for r in rec)
        faltan = esperadas - set(vistos)
        sobran = set(vistos) - esperadas
        dup = [k for k, n in vistos.items() if n > 1]
        retenidos = sum(1 for r in rec if r.get("retenido_para_sha"))
        rec_files = glob.glob(str(Path(archivos[0]).parent / ("recorridos_parte%02d.jsonl" % parte)))
        recorridos = [json.loads(x) for x in open(rec_files[0], encoding="utf-8")] if rec_files else []
        no_rep = sum(1 for r in recorridos if r.get("estado") != "deriva_de_version")
        ok_cab = len(cab) == 1 and cab[0].get("commit") == a.commit and cab[0].get("parte") == parte
        ok_pie = len(pie) == 1 and pie[0].get("errores") == 0
        bien = ok_cab and ok_pie and not faltan and not sobran and not dup and estados == {"ok": len(esperadas)}
        print("parte %2d: esperadas %3d | records %3d | ok %3d | faltan %d sobran %d repetidas %d | port %s | pie %s min | "
              "retenidos para sha %d, recorridos %d (no deriva %d) | %s" % (
                  parte, len(esperadas), len(rec), estados.get("ok", 0), len(faltan), len(sobran), len(dup),
                  dict(port), pie[0].get("minutos") if pie else None, retenidos, len(recorridos), no_rep,
                  "BIEN" if bien else "REVISAR"))
        if not bien:
            malas.append((parte, {"cabecera": ok_cab, "pie": ok_pie, "faltan": sorted(faltan)[:5], "sobran": len(sobran),
                                  "repetidas": len(dup), "estados": dict(estados)}))
        tot["esperadas"] += len(esperadas)
        tot["records"] += len(rec)
        tot["ok"] += estados.get("ok", 0)
    print("TOTAL:", dict(tot), "| partes a revisar:", malas if malas else "ninguna")
    sys.exit(1 if malas else 0)


if __name__ == "__main__":
    main()
