"""S147 - el valor de reposo del Test 1 integrado, medido sobre los records persistidos.

QUE MIDE, Y POR QUE. La derivacion de D30 dice que con ruido puro el criterio absoluto del
Test 1 se sienta en `0,399 por raiz(N)`, donde N es el numero de pixeles del disco de 3 km.
Si eso es cierto, el `test1_k_observed` que el pipeline persiste tiene que sentarse cerca de
ese valor en la poblacion general, y el cociente contra el valor de reposo tiene que ser
PARECIDO ENTRE SENSORES aunque sus discos difieran por un factor 7. Esa constancia es la
firma del defecto: significa que el estadistico esta gobernado por el tamano del disco y no
por el calor del volcan.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el fenomeno no existiera, esto lo mostraria? SI: si el estadistico estuviera centrado,
   la mediana rondaria 0 en los tres sensores y el cociente seria ~0, no ~0,85.
2. Si el instrumento estuviera muerto, se veria distinto? El control esta en la propia
   comparacion entre sensores: un lector que solo devolviera basura no produciria tres
   cocientes casi iguales sobre tres poblaciones distintas con tres N distintos.

LIMITES DECLARADOS (A90, A104):
- La poblacion es TODOS los records de la ventana, no los negativos limpios. Por eso el
  numero NO es comparable con el 1,056 de `docs/audit_s146/`, que uso negativos limpios de
  VIIRS 375. Son denominadores distintos, no una discrepancia.
- La ventana empieza el 2026-08-29, entera posterior al cambio de regimen del 2026-08-28
  23:00 UTC (PR #535). Ninguna ventana de este proyecto debe cruzar esa fecha sin decirlo.
- N se deriva del area nadir fija por sensor (A66/A67), no se lee del record: el pipeline no
  persiste `n_roi`. Es el N nominal del disco, no el efectivo tras descartar invalidos.

Uso:  python experiments/_s147/reposo_test1_en_records_reales.py
"""
from __future__ import annotations
import glob
import json
import math
import statistics as st
from collections import defaultdict

# Area de pixel nadir fija por sensor, km2 (A66/A67: MIROVA remuestrea a area constante)
APIX = {"VIIRS375": 0.140625, "VIIRS750": 0.5625, "MODIS": 1.0}
ROI_KM = 3.0
K_UMBRAL = 3.0
VENTANA_DESDE = "2026-08-29"
MEDIA_NULA_POR_PIXEL = 1.0 / math.sqrt(2.0 * math.pi)  # 0,398942


def bucket(sensor: str) -> str | None:
    """Convencion del proyecto (A48): VIIRS_<plataforma> sin sufijo es banda I 375 m."""
    s = sensor.upper()
    if s.startswith("MODIS") or "MOD" in s or "MYD" in s:
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if "VIIRS" in s:
        return "VIIRS375"
    return None


def main() -> None:
    vals: dict[str, list[float]] = defaultdict(list)
    n_tot: dict[str, int] = defaultdict(int)
    sobre_umbral: dict[str, int] = defaultdict(int)

    for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        for r in recs:
            ts = str(r.get("datetime_utc") or r.get("timestamp") or "")
            if ts[:10] < VENTANA_DESDE:
                continue
            b = bucket(str(r.get("sensor", "")))
            if not b:
                continue
            n_tot[b] += 1
            k = r.get("test1_k_observed")
            if isinstance(k, (int, float)) and k == k and k > 0:
                vals[b].append(float(k))
                if k > K_UMBRAL:
                    sobre_umbral[b] += 1

    print(f"ventana: desde {VENTANA_DESDE} (entera posterior al cambio de regimen de #535)")
    print(f"poblacion: TODOS los records, no negativos limpios")
    cab = (f"{'sensor':10} {'N disco':>8} {'reposo':>8} {'mediana':>8} {'razon':>6} "
           f"{'>3 sigma':>9} {'n con k':>8} {'n total':>8}")
    print(cab)
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        n_pix = math.pi * ROI_KM ** 2 / APIX[b]
        reposo = MEDIA_NULA_POR_PIXEL * math.sqrt(n_pix)
        v = vals[b]
        if not v:
            print(f"{b:10} {n_pix:8.0f} {reposo:8.2f} {'sin datos':>8}")
            continue
        med = st.median(v)
        frac = 100.0 * sobre_umbral[b] / len(v)
        print(f"{b:10} {n_pix:8.0f} {reposo:8.2f} {med:8.2f} {med / reposo:6.3f} "
              f"{frac:8.1f}% {len(v):8d} {n_tot[b]:8d}")

    print()
    print("LECTURA: si el cociente 'razon' es parecido en los tres sensores, el estadistico")
    print("esta gobernado por el tamano del disco (N) y no por el calor. El umbral del codigo")
    print("es 3,0 fijo para los tres, asi que el sensor con el disco mas grande llega al")
    print("umbral por construccion y el mas chico no.")


if __name__ == "__main__":
    main()
