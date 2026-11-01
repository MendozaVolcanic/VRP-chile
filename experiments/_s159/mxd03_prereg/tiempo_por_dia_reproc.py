"""S159, pre-registro de MxD03: cuanto tarda un dia-volcan en un reproceso real, separado en busqueda+descarga y
proceso, y cuantos granulos de cada sensor proceso.

Fuente: el log de UN job de «Reproc por trozos» (`gh run view --job <id> --log`). run_pipeline imprime
`>>> <volcan> | <fecha>` al empezar cada dia, `[diag ...] DOWNLOAD_DONE` al terminar cada descarga y una linea
`<SENSOR> | VRP=...` por granulo procesado al final del dia.

Las dos preguntas del instrumento:
1. Si el log no trajera los marcadores, ¿se veria? Si: imprime cuantos dias y cuantas lineas de granulo encontro.
2. Si el corte entre descarga y proceso estuviera mal, ¿se veria distinto? Si: la suma descarga + proceso de cada
   dia tiene que dar el total del dia (se imprime el residuo maximo).

Uso: python tiempo_por_dia_reproc.py RUTA_log_job.txt
"""
import re
import statistics
import sys
from datetime import datetime

TS = re.compile(r"\t(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z ")


def ts(l):
    m = TS.search(l)
    return datetime.strptime(m.group(1)[:26], "%Y-%m-%dT%H:%M:%S.%f") if m else None


def main():
    lineas = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
    dias, actual = [], None
    for l in lineas:
        t = ts(l)
        if t is None:
            continue
        if ">>> " in l:
            if actual:
                actual["fin"] = t
                dias.append(actual)
            actual = {"ini": t, "ult_dl": None, "ult_linea": t, "sens": {}}
        elif actual:
            actual["ult_linea"] = t
            if "DOWNLOAD_DONE" in l:
                actual["ult_dl"] = t
            m = re.search(r"\s(MODIS_\w+|VIIRS_\w+)(?: \(\d+m\))? \| VRP", l)
            if m:
                s = m.group(1)
                b = "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
                actual["sens"][b] = actual["sens"].get(b, 0) + 1
    if actual:
        actual["fin"] = actual["ult_linea"]
        dias.append(actual)
    print(f"dias encontrados: {len(dias)}")
    tot, desc, proc, gran = [], [], [], {"MODIS": [], "V375": [], "V750": []}
    for d in dias:
        T = (d["fin"] - d["ini"]).total_seconds()
        D = ((d["ult_dl"] or d["ini"]) - d["ini"]).total_seconds()
        tot.append(T); desc.append(D); proc.append(T - D)
        for b in gran:
            gran[b].append(d["sens"].get(b, 0))
        print(f"  {d['ini']:%H:%M:%S} total {T/60:.2f} min, busqueda+descarga {D/60:.2f}, proceso {(T-D)/60:.2f}, "
              f"granulos {d['sens']}")
    if tot:
        print(f"mediana por dia: total {statistics.median(tot)/60:.2f} min, busqueda+descarga "
              f"{statistics.median(desc)/60:.2f}, proceso {statistics.median(proc)/60:.2f}")
        print("granulos por dia (mediana):", {b: statistics.median(v) for b, v in gran.items()})


if __name__ == "__main__":
    main()
