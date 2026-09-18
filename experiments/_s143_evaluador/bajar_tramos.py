# -*- coding: utf-8 -*-
"""S143: baja los artefactos de los runs del A/B y comprueba la cobertura ANTES de fusionar.

POR QUÉ. El tramo 1 terminó 54 de 54 en verde y aun así dos jobs quedaron con menos pasadas que el
control (Lastarria 13 menos, Nevados de Chillán 15 menos, brazo `lit_con_compuerta`): el log mostraba
`SEARCH_CMR_TIMEOUT` con el cortacircuitos encendido, o sea un corte de NASA (A64). Un brazo con menos
pasadas **no perdió noches: no las miró**, y en S135 ese mismo modo de falla fabricó cuatro pérdidas
falsas. Un job verde no prueba que el brazo procesó lo mismo (S141): hay que contarlo.

QUÉ HACE. Baja cada run a su propia carpeta, deja que un run posterior **reemplace** la carpeta de un
job repetido, y reporta la diferencia simétrica de pasadas `(datetime_utc, sensor)` de cada brazo
contra el control, por volcán. Con `--estricto` termina en 1 si algo quedó desparejo.

USO:
    python experiments/_s143_evaluador/bajar_tramos.py --dir <destino> \\
        --run 35266704955 --run 35340956881   # tramo 1 y su repeticion
Después, `fusionar.py --tramo <destino>/... --prefijo s143ab-t1- --prefijo s143ab-t2- ...`
"""
import argparse
import collections
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def bajar(run_id, destino, repo=None):
    """`gh run download` a una carpeta temporal y mueve cada artefacto a `destino`, pisando."""
    tmp = destino / f"_run{run_id}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    cmd = ["gh", "run", "download", str(run_id), "--dir", str(tmp)]
    if repo:
        cmd += ["--repo", repo]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    movidos = []
    for carpeta in sorted(p for p in tmp.iterdir() if p.is_dir()):
        final = destino / carpeta.name
        if final.exists():
            shutil.rmtree(final)  # un run posterior pisa al anterior: así se repite un job corto
            movidos.append(f"{carpeta.name} (reemplaza)")
        else:
            movidos.append(carpeta.name)
        shutil.move(str(carpeta), str(final))
    shutil.rmtree(tmp)
    return movidos


def pasadas_por_artefacto(destino):
    """{(brazo, volcán): set de (datetime_utc, sensor)} leyendo `<prefijo><brazo>-<volcán>/<vol>.json`."""
    out = {}
    for carpeta in sorted(p for p in Path(destino).iterdir() if p.is_dir()):
        jsons = list(carpeta.glob("*.json"))
        if len(jsons) != 1:
            continue
        vol = jsons[0].stem
        brazo = carpeta.name[: -(len(vol) + 1)]  # quita "-<volcán>"
        for sep in ("s143ab-t1-", "s143ab-t2-", "s143ab-"):
            if brazo.startswith(sep):
                brazo = brazo[len(sep):]
                break
        recs = json.loads(jsons[0].read_text(encoding="utf-8"))["records"]
        out[(brazo, vol)] = {(r["datetime_utc"], r["sensor"]) for r in recs}
    return out


def cobertura(pasadas, control):
    """Diferencia simétrica de cada brazo contra el control, por volcán."""
    vols = sorted({v for _, v in pasadas})
    informe = {}
    for vol in vols:
        base = pasadas.get((control, vol))
        if base is None:
            informe[vol] = {"error": f"falta el control {control}"}
            continue
        dif = {}
        for (b, v), s in pasadas.items():
            if v != vol or b == control:
                continue
            d = base ^ s
            if d:
                dif[b] = {"diferencia_simetrica": len(d), "control": len(base), "brazo": len(s)}
        informe[vol] = {"n_control": len(base), "desparejos": dif}
    return informe


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--run", action="append", required=True, help="id de run, repetible y EN ORDEN")
    ap.add_argument("--repo", default=os.environ.get("GH_REPO"))
    ap.add_argument("--control", default=None, help="brazo control; por defecto el de parametros.json")
    ap.add_argument("--estricto", action="store_true")
    a = ap.parse_args(argv)
    control = a.control or json.loads((HERE / "parametros.json").read_text(encoding="utf-8"))["control"]
    a.dir.mkdir(parents=True, exist_ok=True)
    for run in a.run:
        movidos = bajar(run, a.dir, a.repo)
        print(f"run {run}: {len(movidos)} artefactos"
              + (f"; reemplazan {sum('reemplaza' in m for m in movidos)}" if any("reemplaza" in m for m in movidos) else ""))
    pas = pasadas_por_artefacto(a.dir)
    inf = cobertura(pas, control)
    total = collections.Counter()
    for vol, d in inf.items():
        if d.get("error"):
            print(f"  {vol:22s} {d['error']}")
            total["error"] += 1
            continue
        if d["desparejos"]:
            print(f"  {vol:22s} control {d['n_control']:4d}  DESPAREJOS {d['desparejos']}")
            total["desparejos"] += 1
        else:
            print(f"  {vol:22s} control {d['n_control']:4d}  todos iguales")
    (a.dir / "cobertura.json").write_text(json.dumps({"control": control, "por_volcan": inf}, indent=1,
                                                     ensure_ascii=False), encoding="utf-8")
    print(f"{total['desparejos']} volcanes desparejos, {total['error']} con error. "
          f"Detalle en {(a.dir / 'cobertura.json')}")
    if a.estricto and (total["desparejos"] or total["error"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
