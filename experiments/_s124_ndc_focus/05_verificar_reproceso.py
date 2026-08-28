# -*- coding: utf-8 -*-
"""Se reproceso de VERDAD? — el test que destapo el bug del merge (S124).

Un reproceso puede cerrar en VERDE y no haber tocado nada: cada trozo sube el
archivo completo con los otros meses en su version vieja, y el merge dejaba
ganar al ultimo. Sintoma: meses enteros IDENTICOS byte a byte a la corrida
anterior. Este script lo detecta comparando el commit actual contra el previo.

Uso: python experiments/_s124_ndc_focus/05_verificar_reproceso.py [ruta_json]
"""
import collections, io, json, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REL = sys.argv[1] if len(sys.argv) > 1 else "data/experimental_ndc_focus/NevadosDeChillan.json"


def cargar_previo(rel):
    shas = subprocess.run(["git", "log", "-2", "--format=%H", "--", rel],
                          capture_output=True, text=True).stdout.split()
    if len(shas) < 2:
        return None
    txt = subprocess.run(["git", "show", f"{shas[1]}:{rel}"],
                         capture_output=True, text=True).stdout
    return json.loads(txt) if txt else None


def por_clave(d):
    return {(r["datetime_utc"], r.get("sensor")): json.dumps(r, sort_keys=True)
            for r in d["records"]}


if __name__ == "__main__":
    ahora = json.loads(Path(REL).read_text(encoding="utf-8"))
    antes = cargar_previo(REL)
    if antes is None:
        print("Sin version previa en git: nada que comparar (primera corrida).")
        sys.exit(0)

    a, b = por_clave(antes), por_clave(ahora)
    com = set(a) & set(b)
    print(f"records  antes: {len(a)}   ahora: {len(b)}   comunes: {len(com)}")

    tot = collections.Counter()
    ident = collections.Counter()
    for k in com:
        m = k[0][:7]
        tot[m] += 1
        if a[k] == b[k]:
            ident[m] += 1

    print("\nrecords IDENTICOS byte a byte, por mes (100% = ese mes NO se reproceso):")
    sospechoso = False
    for m in sorted(tot):
        pct = 100 * ident[m] / tot[m]
        flag = "  <== NO SE REPROCESO" if pct > 99 else ""
        if pct > 99:
            sospechoso = True
        print(f"   {m}: {ident[m]:4d}/{tot[m]:4d} = {pct:3.0f}%{flag}")

    print()
    if sospechoso:
        print("VEREDICTO: hay meses sin reprocesar. NO leer resultados de esos meses.")
        sys.exit(1)
    print("VEREDICTO: todos los meses cambiaron. El reproceso si toco la data.")
