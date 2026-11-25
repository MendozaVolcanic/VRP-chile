# -*- coding: utf-8 -*-
"""S201: une las tandas del barrido del piso (S196) en una carpeta por brazo, la entrada de `evaluar.py calibrar`
(--sin-zona, --control, --brazo piso=carpeta). No corre calibrar ni mira resultados de detección.

POR QUÉ. El barrido se despacha por tandas mensuales (pre-registro, decisión 3 de Nicolás) y cada tanda deja sus
salidas en la rama `s196-lab-piso/<run>`. El evaluador re-sellado recibe una carpeta por brazo, así que alguien tiene
que unir las tandas, y esa unión no estaba escrita. El verificador limpio del frente A de la ronda 5 de la auditoría
externa con Codex (D:\\codex-vrp\\_salida\\ronda5\\fa_r5_verificacion\\VEREDICTO.md) mostró que el evaluador puede
terminar en ELEGIDO con otro piso si un brazo trae filas duplicadas de otro código (R5FA-102), copias de una pasada
(R5FA-101) o noches que no están en todos los brazos (R5FA-105), y que la cadena oficial no produce esos casos salvo
que la unión de las tandas no los impida. Las tandas no son disjuntas: Cordón Caulle va en todas (da poder al control
donde la zona no actúa) y marzo se corrió en tres runs (t1, t2 y t2c) con volcanes inválidos en t2 (401 de NASA).
Por eso la unión sigue un manifiesto explícito (MANIFIESTO_TANDAS.json: qué run vale para cada volcán y mes) y se
detiene ante cualquier ambigüedad en vez de elegir en silencio.

QUÉ EXIGE (cada falla queda en `problemas`, la línea de comandos sale con 2):
  1. que cada volcán tenga cada mes, del primero al último del manifiesto, cubierto por algún run;
  2. que cada brazo y volcán de cada run exista en su rama;
  3. que cada record caiga en la ventana [ini, fin] de su run (fecha UTC de datetime_utc);
  4. que una clave (sensor, datetime_utc) repetida sea idéntica salvo processed_utc y first_processed_utc; si difiere
     en cualquier otro campo, incluido regimen.codigo_sha, es CONFLICTIVO;
  5. que todos los brazos tengan el mismo conjunto de claves que el control en cada volcán;
  6. con --fin-esperado, que el último fin del manifiesto sea ése (el fin sellado es 2026-11-23, R4FD-107).
Escribe <salida>/<brazo>/<volcán>.json y <salida>/informe_union.json (manifiesto, problemas, conteos, sha256).

Uso: python experiments/_s196_lab_piso/unir_tandas.py experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json SALIDA \\
         --fin-esperado 2026-11-23
Las ramas se bajan antes: git fetch origin "+refs/heads/s196-lab-piso/*:refs/remotes/origin/s196-lab-piso/*"
Pruebas: tests/test_lab_piso_union_tandas_s201.py.
"""
import argparse
import hashlib
import io
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BRAZOS = ["_s196_lab_sinzona", "_s196_lab_control", "_s196_lab_p300", "_s196_lab_p275", "_s196_lab_p250",
          "_s196_lab_p225", "_s196_lab_p200", "_s196_lab_p175", "_s196_lab_p150"]
CONTROL = "_s196_lab_control"
VOLATILES = {"processed_utc", "first_processed_utc"}


def leer_git(run, brazo, volcan):
    """El JSON de un brazo y volcán en la rama de salidas del run, o None si no está."""
    ruta = f"origin/s196-lab-piso/{run}:experiments/_s196_lab_piso/salidas/{run}/{brazo}/{volcan}.json"
    r = subprocess.run(["git", "-C", str(RAIZ), "show", ruta], capture_output=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode("utf-8"))


def huella(rec):
    return json.dumps({k: v for k, v in rec.items() if k not in VOLATILES}, sort_keys=True, ensure_ascii=False)


def meses(ini, fin):
    a, b = date.fromisoformat(ini), date.fromisoformat(fin)
    out, y, m = [], a.year, a.month
    while (y, m) <= (b.year, b.month):
        out.append("%04d-%02d" % (y, m))
        y, m = y + (m == 12), m % 12 + 1
    return out


def unir(manifiesto, salida, fin_esperado=None, leer=None):
    leer = leer or leer_git
    problemas, conteo = [], defaultdict(dict)
    volcanes = sorted({v for e in manifiesto for v in e["volcanes"]})
    ini_global = min(e["ini"] for e in manifiesto)
    fin_global = max(e["fin"] for e in manifiesto)
    if fin_esperado and fin_global != fin_esperado:
        problemas.append(f"fin del manifiesto {fin_global} distinto del esperado {fin_esperado}")
    for v in volcanes:                                                   # 1. cobertura de meses
        cubiertos = defaultdict(list)
        for e in manifiesto:
            if v in e["volcanes"]:
                for m in meses(e["ini"], e["fin"]):
                    cubiertos[m].append(e["etiqueta"])
        for m in meses(ini_global, fin_global):
            if not cubiertos.get(m):
                problemas.append(f"{v} {m}: ningún run del manifiesto lo cubre")
    claves = defaultdict(dict)
    salida = Path(salida)
    for b in BRAZOS:
        for v in volcanes:
            union, origen = {}, {}
            n_leidos = n_dup = 0
            for e in manifiesto:
                if v not in e["volcanes"]:
                    continue
                d = leer(e["run"], b, v)
                if d is None:                                            # 2. brazo presente
                    problemas.append(f"{b} {v}: falta en {e['etiqueta']} ({e['run']})")
                    continue
                for r in (d["records"] if isinstance(d, dict) else d):
                    n_leidos += 1
                    if not (e["ini"] <= r["datetime_utc"][:10] <= e["fin"]):   # 3. ventana
                        problemas.append(f"{b} {v}: record {r['datetime_utc']} fuera de la ventana de {e['etiqueta']}")
                        continue
                    k = (r.get("sensor"), r["datetime_utc"])
                    if k in union:                                       # 4. duplicados
                        if huella(union[k]) == huella(r):
                            n_dup += 1
                        else:
                            problemas.append(f"{b} {v}: duplicado CONFLICTIVO {k} entre {origen[k]} y {e['etiqueta']}")
                        continue
                    union[k] = r
                    origen[k] = e["etiqueta"]
            recs = [union[k] for k in sorted(union, key=lambda k: (k[1], k[0] or ""))]
            dest = salida / b / f"{v}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            texto = json.dumps({"volcano": v, "updated": "unir_tandas S201", "records": recs}, ensure_ascii=False)
            dest.write_text(texto, encoding="utf-8", newline="")
            conteo[b][v] = {"leidos": n_leidos, "unidos": len(recs), "duplicados_identicos": n_dup,
                            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest()}
            claves[v][b] = set(union)
    for v, porb in claves.items():                                       # 5. mismas claves que el control
        ref = porb.get(CONTROL, set())
        for b, ks in porb.items():
            if ks != ref:
                problemas.append(f"{v}: {b} tiene {len(ks - ref)} claves que el control no y le faltan {len(ref - ks)}")
    informe = {"manifiesto": manifiesto, "fin_esperado": fin_esperado, "problemas": problemas, "conteo": conteo}
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "informe_union.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8",
                                                newline="")
    return problemas, conteo


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifiesto")
    ap.add_argument("salida")
    ap.add_argument("--fin-esperado")
    a = ap.parse_args(argv)
    man = json.loads(Path(a.manifiesto).read_text(encoding="utf-8"))
    problemas, conteo = unir(man, a.salida, a.fin_esperado, leer=leer_git)
    tot = {b: sum(c["unidos"] for c in conteo[b].values()) for b in conteo}
    print("records unidos por brazo:", tot)
    print("duplicados idénticos quitados (control):",
          {v: c["duplicados_identicos"] for v, c in conteo.get(CONTROL, {}).items() if c["duplicados_identicos"]})
    print("problemas:", len(problemas))
    for p in problemas[:40]:
        print("  ", p)
    return 2 if problemas else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
