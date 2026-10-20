"""S157: une los trozos de un A/B corrido con todos los brazos en el mismo job.

POR QUÉ. Para que N brazos quepan en el paso de 170 min (A15), el A/B parte la ventana en trozos
(scripts/reproc_brazos.py::dias_por_trozo) y cada job corre todos los brazos de un volcán y un trozo. Cada artefacto
se llama `s146ab-<volcan>-<idx>-<ini>_<fin>` y trae data/<brazo>/<volcan>.json, logs/<brazo>_<volcan>.log y
cobertura/. Bajados con `merge-multiple`, dos trozos del mismo brazo y volcán se pisarían en silencio; por eso se bajan
separados y este script los une, cada trozo aportando sólo los records de SU ventana (scripts/merge_chunk_stores.py,
la misma unión de reproc-chunked).

SALIDA, con la forma de antes para los evaluadores: salidas/<brazo>/<volcan>.json (un solo trozo se copia tal cual),
salidas/logs/<brazo>_<volcan>.log (trozos en orden) y salidas/cobertura_brazos.json.

Uso: python scripts/unir_trozos_ab.py recolectado salidas
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.merge_chunk_stores import merge_stores  # noqa: E402

PATRON = re.compile(r"^s146ab-(?P<vol>.+)-(?P<idx>\d+)-(?P<ini>\d{4}-\d{2}-\d{2})_(?P<fin>\d{4}-\d{2}-\d{2})$")


def unir(recolectado, salidas) -> dict:
    recolectado, salidas = Path(recolectado), Path(salidas)
    salidas.mkdir(parents=True, exist_ok=True)
    trozos = []
    for d in sorted(recolectado.iterdir()):
        m = PATRON.match(d.name)
        if m and d.is_dir():
            trozos.append((m["vol"], int(m["idx"]), m["ini"], m["fin"], d))
    trozos.sort(key=lambda t: (t[0], t[1]))
    jsons = defaultdict(list)
    logs = defaultdict(list)
    fallas = []
    for vol, idx, ini, fin, d in trozos:
        for j in sorted((d / "data").glob(f"*/{vol}.json")):
            jsons[(j.parent.name, vol)].append((j, f"{ini}:{fin}"))
        for lg in sorted((d / "logs").glob("*.log")):
            logs[lg.name].append(lg)
        for c in sorted((d / "cobertura").glob("*.json")):
            for f in json.loads(c.read_text(encoding="utf-8")).get("fallas", []):
                fallas.append(dict(f, volcan_trozo=vol, trozo=idx))
    for (brazo, vol), lista in sorted(jsons.items()):
        destino = salidas / brazo / f"{vol}.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        if len(lista) == 1:
            shutil.copyfile(lista[0][0], destino)
            continue
        ventanas = [tuple(v.split(":")) for _, v in lista]
        unido, dup = merge_stores([p for p, _ in lista], ventanas)
        if dup:
            print(f"AVISO {brazo} {vol}: {dup} records repetidos entre trozos", file=sys.stderr)
        destino.write_text(json.dumps(unido, indent=2), encoding="utf-8")
        print(f"{brazo} {vol}: {len(lista)} trozos, {len(unido['records'])} records")
    (salidas / "logs").mkdir(exist_ok=True)
    for nombre, lista in logs.items():
        with open(salidas / "logs" / nombre, "w", encoding="utf-8") as fh:
            for lg in lista:
                fh.write(lg.read_text(encoding="utf-8", errors="replace"))
    (salidas / "cobertura_brazos.json").write_text(
        json.dumps({"fallas": fallas, "n": len(fallas)}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"trozos": len(trozos), "archivos": len(jsons), "fallas": len(fallas)}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(unir(sys.argv[1], sys.argv[2]))
