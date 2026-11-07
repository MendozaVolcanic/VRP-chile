# S175: mutaciones de la auditoría sobre la vigilancia de la guardia K de MODIS, antes y después

Decisiones 11 de `docs/AUDIT_S175.md` §8 (hallazgos 151, 152 y V1-01) y 3 de S174 (hallazgo 253), aprobadas por
Nicolás el 2026-11-07. Pregunta: las mutaciones M2, M6 y M2c de
`experiments/_s175_audit/f1/mutaciones_vigilancia.py` (rama `claude/relaxed-almeida-d17378`, `aa2b71441`) ¿quedan
atrapadas con el código nuevo, sobre datos reales, sin mover los controles?

## Montaje

- Datos: `data/mirova_equivalent/` y `data/guardia_k_modis/` de `origin/main` `a8dc6e63e` (2026-11-07 21:10 UTC).
- Referencia: `C:\Users\nmend\vrp-temporales\s175_audit\insumos\latest_consolidado_base.csv` (sha256 `dee768374b84d49b...`)
  y `snapshot_ocr_base.csv` (`577a336e76383a67...`), las de la auditoría (fuera del repo, `.gitignore` de `*.csv`).
- Instrumento: `mutaciones_vigilancia.py` de la auditoría (sha256 `dc318a58339a551a...`), pasado por `preparar.py`, que
  sólo cambia dos cosas de montaje: la carpeta de las copias (`MUT_DIR`) y, para el brazo «viejo», importar el
  `scripts/vigilancia_guardia_modis.py` de `origin/main` (sha256 `4d8b6ad074887f75...`) re-anclado al ROOT real. La
  lógica de las mutaciones no se toca. `hoy` = 2026-11-07.

## Resultado (`salida_viejo.json`, `salida_nuevo.json`)

| mutación | esperado si la vigilancia lo ve | viejo | nuevo |
|---|---|---|---|
| M0 sin mutar (control) | VERDE | VERDE | VERDE |
| M1 la vía calla, la guardia publica (control positivo) | REVERSION_CANDIDATA | REVERSION_CANDIDATA | REVERSION_CANDIDATA |
| M4 producción sin record | INVESTIGAR | INVESTIGAR | INVESTIGAR |
| **M6** el record de producción es caída a K y calla | INVESTIGAR o aviso, no reversión | **REVERSION_CANDIDATA** | **INVESTIGAR** + aviso de caída |
| **M2** la vía cae a K sólo en Chaitén | aviso | **VERDE** | **VIGILANCIA_CIEGA** (aviso de Chaitén y de caídas) |
| M2b la vía cae a K en los 11 | aviso | INVESTIGAR + aviso | INVESTIGAR + aviso |
| **M2c** la vía deja de escribir en Chaitén desde el 2026-11-04 | aviso | **VERDE** | **VIGILANCIA_CIEGA** (vía hasta el 2026-11-03) |
| M3 falta la guardia de Villarrica | VIGILANCIA_CIEGA | VIGILANCIA_CIEGA | VIGILANCIA_CIEGA |
| M5 la guardia trae la marca de la vía | VIGILANCIA_CIEGA | VIGILANCIA_CIEGA | VIGILANCIA_CIEGA |

Las tres mutaciones atrapadas; los controles no se mueven, y sobre los datos de hoy sin mutar la vigilancia sigue en
VERDE (no hay caídas a K en producción).

## Reproducir

```bash
python preparar.py <mutaciones_vigilancia.py de aa2b71441> mut_vig.py
MUT_DIR=<carpeta> [VGM_VIEJO=<carpeta con el vigilancia_guardia_modis.py viejo>] python mut_vig.py <raíz del repo> 2026-11-07 --cons <latest_consolidado_base.csv> --ocr <snapshot_ocr_base.csv>
```
