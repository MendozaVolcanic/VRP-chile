# -*- coding: utf-8 -*-
"""S173 F2 (d): tiempo por fecha de Láscar con la vía (sombra, tres vías) y con K (NRT), desde los logs reales de GitHub.

Pregunta 1 (si lo que mido estuviera roto, ¿se vería?): si la vía costara mucho más que K, el tramo de procesamiento
  (último DOWNLOAD_DONE de la fecha hasta «Cleaned up») de la sombra sería mucho mayor que el del NRT en la misma fecha.
  Lo que NO ve: no separa MODIS de VIIRS (la salida de cada sensor se imprime en bloque al final de la fecha), así que
  es una COTA SUPERIOR del costo de la vía de MODIS (incluye las vías de V750 y V375). Tampoco ve la escritura del
  JSON: la de producción es mucho más grande que la de la sombra (confusor que juega a favor de la vía).
Pregunta 2 (instrumento muerto): si el parser no encontrara fechas o marcas, imprime 0 fechas y SIN DATO, no un cero.
Control positivo: el tramo de descarga (suma de DOWNLOAD_DONE elapsed) tiene que ser > 0 en cada fecha con gránulos.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parent
TS = re.compile(r"\t(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z ")


def ts(line):
    m = TS.search(line)
    return datetime.fromisoformat(m.group(1)[:26]) if m else None


def bloques(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out, cur = {}, None
    for ln in lines:
        m = re.search(r">>> \S+ \| (\d{4}-\d\d-\d\d)", ln)
        if m:
            cur = m.group(1)
            out[cur] = [ln]
        elif cur:
            out[cur].append(ln)
    res = {}
    for fecha, ls in out.items():
        t0 = ts(ls[0])
        dl = [(ts(x), float(re.search(r"elapsed=([\d.]+)s", x).group(1))) for x in ls if "DOWNLOAD_DONE" in x]
        clean = [ts(x) for x in ls if "Cleaned up" in x]
        sensores = [x.split("\t")[-1].split(" | ")[0].strip()[29:] for x in ls if " | VRP" in x]
        gran = [x for x in ls if "kept" in x and "granules" in x]
        kept = sum(int(re.search(r"kept (\d+) of", x).group(1)) for x in gran)
        modis_kept = sum(int(re.search(r"kept (\d+) of", x).group(1)) for x in gran if "MODIS" in x)
        if not dl or not clean:
            res[fecha] = None
            continue
        res[fecha] = {"inicio_a_limpieza_s": (clean[-1] - t0).total_seconds(),
                      "descarga_s": sum(e for _, e in dl),
                      "proceso_s": (clean[-1] - max(t for t, _ in dl)).total_seconds(),
                      "granulos_kept": kept, "modis_kept": modis_kept, "n_lineas_resultado": len(sensores)}
    return res


def main():
    s = bloques(F / "log_sombra11_lascar_41034796854.txt")
    k = bloques(F / "log_nrt_lascar_41038778013.txt")
    print("Láscar, sombra (perfil sombra_codigo_mirova, tres vías; run 41034796854, job 123992887697, 2026-10-30 09:37 UTC)")
    print("contra NRT (mirova_equivalent, K; run 41038778013, job 124006081054, 2026-10-30 10:10 UTC)")
    print(f"fechas con bloque: sombra {len(s)} {sorted(s)}, NRT {len(k)} {sorted(k)}")
    comunes = sorted(set(s) & set(k))
    if not comunes:
        print("SIN DATO: no hay fechas comunes")
        return
    print(f"{'fecha':12}{'brazo':8}{'total_s':>9}{'descarga_s':>11}{'proceso_s':>10}{'kept':>6}{'modis':>6}")
    tot = {"s": [0, 0], "k": [0, 0]}
    for f in comunes:
        for nom, d in (("sombra", s[f]), ("NRT K", k[f])):
            if d is None:
                print(f"{f:12}{nom:8} SIN DATO (sin DOWNLOAD_DONE o sin Cleaned up)")
                continue
            print(f"{f:12}{nom:8}{d['inicio_a_limpieza_s']:9.1f}{d['descarga_s']:11.1f}{d['proceso_s']:10.1f}"
                  f"{d['granulos_kept']:6d}{d['modis_kept']:6d}")
            key = "s" if nom == "sombra" else "k"
            tot[key][0] += d["proceso_s"]
            tot[key][1] += d["granulos_kept"]
    print(f"suma proceso_s en {len(comunes)} fechas: sombra {tot['s'][0]:.1f} s ({tot['s'][1]} gránulos), "
          f"NRT K {tot['k'][0]:.1f} s ({tot['k'][1]} gránulos)")
    print("Todas las fechas del NRT (8 días):")
    for f in sorted(k):
        d = k[f]
        print(f"  {f} " + ("SIN DATO" if d is None else
                           f"total {d['inicio_a_limpieza_s']:.1f} s, descarga {d['descarga_s']:.1f} s, proceso {d['proceso_s']:.1f} s, "
                           f"kept {d['granulos_kept']} (MODIS {d['modis_kept']})"))


if __name__ == "__main__":
    main()
