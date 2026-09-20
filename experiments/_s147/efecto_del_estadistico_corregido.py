"""S147 - cuanto cambiaria el disparo del Test 1 con el estadistico corregido, sin reprocesar.

DE DONDE SALE QUE SE PUEDE MEDIR SIN REPROCESAR. El campo persistido `test1_k_observed` es

    k_obs = suma_recortada / (sigma * raiz(N))

y el estadistico corregido es

    z = (suma_recortada - N * 0,398942 * sigma) / (sigma * raiz(N * 0,340845))

Dividiendo arriba y abajo por `sigma * raiz(N)`, sigma y la suma desaparecen y queda

    z = (k_obs - 0,398942 * raiz(N)) / raiz(0,340845)  =  1,7127 * (k_obs - 0,398942 * raiz(N))

o sea que z es una transformacion LINEAL de un campo que ya esta en los JSON. El criterio
`z > 3` equivale entonces a

    k_obs > 0,398942 * raiz(N) + 1,7514

que en VIIRS 375 (N = 201) es 7,41, en VIIRS 750 (N = 50) es 4,58 y en MODIS (N = 28) es 3,87,
contra el 3,0 fijo de hoy.

QUE ES ESTO Y QUE NO ES. Es una COTA calculada sobre lo persistido, no una re-ejecucion: el
veredicto lo da el A/B. Marcar SOSPECHA. Tres razones por las que puede diferir del reproceso:
- N es el nominal del disco por area de pixel, no el efectivo tras descartar pixeles invalidos
  (nube, borde de granulo). Con menos pixeles validos el umbral corregido baja.
- El disparo persistido `triggered_test1` combina el criterio absoluto con el relativo
  (`mir_relative`), y este calculo solo rehace el absoluto.
- Apagar un disparo no equivale a no publicar: el Test 1 compite por la fuente del cumulo, y
  puede haber otro camino que publique igual (por eso la unidad que decide es la pasada, y la
  mide el evaluador del A/B, no este script).

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el corregido no cambiara nada, esto lo mostraria? SI: la columna "sobreviven" daria 100 %.
2. Si el instrumento estuviera muerto? El control esta en que el mismo script reporta el conteo
   de hoy (`triggered_test1` persistido) como denominador: si leyera mal los JSON, ese
   denominador no coincidiria con el que reporta el resto del proyecto.

Uso:  python experiments/_s147/efecto_del_estadistico_corregido.py
"""
from __future__ import annotations
import glob
import json
import math
from collections import defaultdict

APIX = {"VIIRS375": 0.140625, "VIIRS750": 0.5625, "MODIS": 1.0}
ROI_KM = 3.0
K_HOY = 3.0
MEDIA_NULA = 1.0 / math.sqrt(2.0 * math.pi)          # 0,398942
DESV_NULA = math.sqrt(0.5 - 1.0 / (2.0 * math.pi))   # 0,583820
VENTANA_DESDE = "2026-08-29"


def bucket(sensor: str) -> str | None:
    s = sensor.upper()
    if s.startswith("MODIS") or "MOD" in s or "MYD" in s:
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if "VIIRS" in s:
        return "VIIRS375"
    return None


def umbral_corregido(n_pix: float) -> float:
    return MEDIA_NULA * math.sqrt(n_pix) + K_HOY * DESV_NULA


def main() -> None:
    disparos = defaultdict(int)
    sobreviven = defaultdict(int)
    por_volcan = defaultdict(lambda: [0, 0])

    for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        vol = f.replace("\\", "/").split("/")[-1].replace(".json", "")
        for r in recs:
            ts = str(r.get("datetime_utc") or r.get("timestamp") or "")
            if ts[:10] < VENTANA_DESDE:
                continue
            if not r.get("triggered_test1"):
                continue
            b = bucket(str(r.get("sensor", "")))
            k = r.get("test1_k_observed")
            if not b or not isinstance(k, (int, float)) or k != k:
                continue
            n_pix = math.pi * ROI_KM ** 2 / APIX[b]
            disparos[b] += 1
            por_volcan[vol][0] += 1
            if float(k) > umbral_corregido(n_pix):
                sobreviven[b] += 1
                por_volcan[vol][1] += 1

    print(f"ventana: desde {VENTANA_DESDE} (posterior al cambio de regimen de #535)")
    print("COTA sobre lo persistido, NO una re-ejecucion. Marcar SOSPECHA.")
    print()
    print(f"{'sensor':10} {'umbral hoy':>11} {'umbral corregido':>17} "
          f"{'disparos hoy':>13} {'sobreviven':>11} {'%':>7}")
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        n_pix = math.pi * ROI_KM ** 2 / APIX[b]
        d_hoy = disparos[b]
        if d_hoy == 0:
            print(f"{b:10} {K_HOY:11.2f} {umbral_corregido(n_pix):17.2f} {0:13d}")
            continue
        s = sobreviven[b]
        print(f"{b:10} {K_HOY:11.2f} {umbral_corregido(n_pix):17.2f} {d_hoy:13d} "
              f"{s:11d} {100.0 * s / d_hoy:6.1f}%")

    print()
    print(f"{'volcan':22} {'disparos':>9} {'sobreviven':>11} {'%':>7}")
    for vol, (tot, sob) in sorted(por_volcan.items(), key=lambda kv: -kv[1][0]):
        if tot == 0:
            continue
        print(f"{vol:22} {tot:9d} {sob:11d} {100.0 * sob / tot:6.1f}%")


if __name__ == "__main__":
    main()
