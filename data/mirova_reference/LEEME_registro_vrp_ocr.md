# ⚠️ `registro_vrp_ocr.csv` de este directorio está CONGELADO — no lo uses

**Última fila: 2026-03-28 (236 líneas).** El canal OCR vivo es

```
data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv
```

que llega al **2026-08-24 (888 líneas)** y lo refresca `.github/workflows/audit-weekly.yml`
cada semana. Nadie actualiza la copia de este nivel.

## Por qué sigue acá

La consumen los experimentos históricos `experiments/126_*` a `131_*`, que deben quedar
pinneados a su snapshot para seguir siendo reproducibles — misma convención que los CSV
consolidados fechados (A17). Borrarla rompería esos experimentos.

## Qué salió mal por su culpa

`scripts/build_c2ab_windows.py` tomaba el consolidado del snapshot y el OCR de acá, o
sea dos cortes temporales distintos del mismo ground truth. Construía las ventanas del
A/B con cinco meses menos de canal OCR: **844 fechas ALERTA en vez de 903** sobre los
11 Tier A (+11 en Planchón-Peteroa, +10 en PCC, +9 en Villarrica). Corregido en S126.

El canal OCR es **complemento** del consolidado, no validación (A11): MIROVA publica
algunas cosas en `latest.php` y otras sólo como imagen por volcán. Lo que falta en un
canal **no** se recupera por el otro.

## Guard

`tests/test_ground_truth_mismo_snapshot_s126.py` verifica dos cosas: que los dos canales
salgan del mismo directorio, y que el CSV que un script consume sea uno que el workflow
efectivamente refresca. Si aparece otro consumidor apuntando acá, el test lo agarra.
