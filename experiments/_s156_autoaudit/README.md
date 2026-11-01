# S156: auto-audit por detector y alertas protegidas (evidencia del PR #862)

Arreglos 2 y 3 de `docs/AUDIT_S155.md` §5. Plan en `docs/superpowers/plans/2026-10-19-auto-audit-por-detector.md`.

## Corrida con la referencia fresca

`latest_2026-10-19_ref_fresca.json` es la salida de `scripts/auto_audit_weekly.main()` del commit del PR, corrida el
2026-10-19 con `correr_audit.py` (desvía `CONS`, `OCR` y `OUTDIR`; no escribe en `data/`) sobre los CSV de Mirova-v1
bajados ese día:

| archivo | sha256 |
|---|---|
| `registro_vrp_consolidado.csv` | `ba7d50bd108b96f5168b4b2115f4446b03fc6d530c1414f257f4686a22c35b80` |
| `registro_vrp_ocr.csv` | `ed1756231f6ce54040606d7cf19bd990af4f1df5c61bd84fdd8296ae6842185e` |

No regenera la unión histórica (el cron sí lo hace), así que el lunes los números pueden moverse un poco.
Veredicto: `FUERA_DE_BANDA` con 10 flags, todos del detector K (ver `flags` en el JSON).

## Verificador con contexto limpio

`verificador/INFORME.md`, con sus scripts y salidas. Confirmó A1 a A4 y A6 (números por detector, las 90
protegidas nocturnas y las 5 sin publicar, con un instrumento propio a ±15 min). A5 quedó parcial: D-9 se calculaba
sobre filas ya deduplicadas. A7 quedó refutada en parte: las pruebas atrapaban 4 de 12 mutaciones. Arreglado después
del informe, en el mismo PR:

- D-9 se calcula sobre la referencia unificada (`cargar_filas_referencia`), con fallback al cargador.
- Prueba de punta a punta de `main()` (`tests/test_auto_audit_main_s156.py`); `mutar.py` corre 12 mutaciones y las
  12 caen por fallo de prueba, ninguna por caída.
- Un aviso de detector (frontera ilegible o atrás de los datos, banco sin `sha`) degrada el veredicto.
- Las protegidas que descansan sólo en el OCR de Suomi NPP antes del hito de A119 se marcan como referencia
  sospechosa en el flag (las dos de Tupungatito del 28 y 29 de septiembre).
- El issue DEGRADADO lista también los flags.

Lo que queda abierto del informe: el estado de una protegida no mira el detector del record que la parea (hoy sin
efecto; el campo `detector_records` lo deja a la vista), y la compatibilidad con Python 3.11 se revisó sólo de forma
estática.
