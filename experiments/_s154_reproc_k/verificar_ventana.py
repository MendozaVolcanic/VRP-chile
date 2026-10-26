# -*- coding: utf-8 -*-
"""S154: ¿la ventana quedo de verdad escrita con K, y nada fuera de ella cambio?

POR QUE. Un reproceso puede cerrar en verde sin haber tocado nada (S124: el merge dejaba ganar la version vieja;
S125: sin --overwrite una ventana ya consolidada no se reemplaza). Este script compara la serie operacional de un
commit contra el tag tomado justo antes del reproceso y cuenta, por volcan:
  - en la ventana: pasadas procesadas despues del merge de K (`processed_utc` >= corte) y pasadas que siguen con
    la version anterior; claves que estaban en el tag y ya no estan (perdidas);
  - antes de la ventana: records que no son identicos a los del tag (deberia dar 0: el reproceso no los toca, y el
    NRT solo escribe hacia adelante).
El criterio «procesado despues del corte» no depende del sha del codigo ni del nombre del perfil.

Uso:
  python experiments/_s154_reproc_k/verificar_ventana.py --desde 2026-09-18 --hasta 2026-10-18 \
      --corte 2026-10-18T09:57:30Z --tag pre-s154-reproc-k-datos --ref origin/main [--salida informe.json]
"""
import argparse
import io
import json
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TIER_A = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten", "Tupungatito", "Copahue",
          "PlanchonPeteroa", "PuyehueCordonCaulle", "NevadosDeChillan"]


def cargar(ref, vol, subdir):
    txt = subprocess.run(["git", "show", f"{ref}:data/{subdir}/{vol}.json"], capture_output=True,
                         encoding="utf-8", check=True).stdout
    return {(r["datetime_utc"], r.get("sensor")): r for r in json.loads(txt)["records"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--corte", required=True, help="hora UTC desde la que un record cuenta como escrito con K")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--subdir", default="mirova_equivalent")
    ap.add_argument("--salida")
    a = ap.parse_args()

    filas, total = [], {"en_ventana": 0, "con_k": 0, "sin_k": 0, "perdidas": 0, "cambiados_antes": 0}
    for vol in TIER_A:
        antes, ahora = cargar(a.tag, vol, a.subdir), cargar(a.ref, vol, a.subdir)
        en_v = lambda k: a.desde <= k[0][:10] <= a.hasta
        v_ahora = [k for k in ahora if en_v(k)]
        con_k = [k for k in v_ahora if (ahora[k].get("processed_utc") or "") >= a.corte]
        perdidas = [k for k in antes if en_v(k) and k not in ahora]
        cambiados = [k for k in antes if k[0][:10] < a.desde and ahora.get(k) != antes[k]]
        f = {"volcan": vol, "en_ventana": len(v_ahora), "con_k": len(con_k), "sin_k": len(v_ahora) - len(con_k),
             "perdidas": len(perdidas), "cambiados_antes": len(cambiados),
             "sin_k_ejemplos": sorted(k for k in v_ahora if k not in set(con_k))[:5]}
        filas.append(f)
        for c in total:
            total[c] += f[c]
        print(f"{vol:20s} ventana {f['en_ventana']:5d} | con K {f['con_k']:5d} | sin K {f['sin_k']:4d} | "
              f"perdidas {f['perdidas']:3d} | cambiados antes de la ventana {f['cambiados_antes']:3d}")
    print(f"{'TOTAL':20s} ventana {total['en_ventana']:5d} | con K {total['con_k']:5d} | sin K {total['sin_k']:4d} | "
          f"perdidas {total['perdidas']:3d} | cambiados antes de la ventana {total['cambiados_antes']:3d}")
    if a.salida:
        with open(a.salida, "w", encoding="utf-8") as fh:
            json.dump({"args": vars(a), "total": total, "por_volcan": filas}, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
