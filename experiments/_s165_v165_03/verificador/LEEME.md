# Verificador limpio de V165-03 (S165, 2026-10-27)

Claude Fable 5.1, contexto limpio: recibió sólo las afirmaciones A1 a A8 y dónde mirar, sin el razonamiento de quien
escribió el PR. Escribió `CAMINOS.md` antes de leer el cambio (sha256 en `CAMINOS.sha256`; coincide con el archivo
copiado aquí). Midió el commit 3926f6a93 en sus propios árboles de D:, ya borrados. Es una copia de
`D:\vrp-trabajo\temporales\s165_v16503_verificador\` sin `salidas/docs_tag/`, que eran copias de CLAUDE.md,
MIROVA_DIVERGENCES.md y del guard G8 tal como estaban en el tag; se reconstruyen con
`git show pre-s165-v165-03-sin-dato:<ruta>`.

**Veredictos:** A1, A2, A4, A5, A6 y A7 CONFIRMADO; A3 y A8 CONFIRMADO EN PARTE. Informe completo en `INFORME.md`.

## Qué se hizo con cada hallazgo

| ID | gravedad | qué | respuesta |
|---|---|---|---|
| A3 (en parte) | | la razón «se repite igual en todos los brazos» no vale para el A/B que decide encender el flag (brazo con flag contra control sin él) | precisada en `pipeline/fetch.py`, en la prueba y en la FICHA: repetir el job no recupera el descarte, y contra un control sin el flag lo explica el evaluador (siguiente fila), no el modo estricto |
| V16503-01 | 2 | `scripts/evaluador_comun.py` no conocía el tipo: `causa_ausencia` daba «el run no registró nada» para una pasada descartada, indistinguible de una pérdida | causa nueva `CAUSA_SIN_DATO_CRATER`, después del hueco de NASA y antes de la búsqueda vacía; prueba roja primero (`test_el_evaluador_distingue_la_pasada_sin_dato_de_una_perdida`) y mutación `evaluador_no_conoce_el_tipo` en la batería |
| V16503-02 | 1 | la fila v1.17 de la FICHA tenía 3 celdas en vez de 4 | agregada la celda de trazabilidad interna |
| V16503-03 | 1 | `CLAUDE.md` (A100) citaba `process_modis.py:1172` para `FOCAL_CLUSTER_KEEP_PEAK`; ya estaba corrida antes del PR | remapeada por contenido a 1356 (`keep_peak=FOCAL_CLUSTER_KEEP_PEAK`), con la línea vieja dicha |
| V16503-04 | 0 | 14 citas de `docs/MIROVA_DIVERGENCES.md` a `process_modis.py` corridas 4 a 6 líneas, deriva heredada | no se toca aquí: es deriva anterior que este PR agranda poco; queda como seguimiento |
| V16503-05 | 0 | `scripts/backfill_nov_2025.py` usa `process_date` y nunca informa cobertura | fuera de alcance (no está en ningún workflow y es anterior al PR); seguimiento |

SIN DATO del verificador, que siguen abiertos: una incidencia con gránulo del día UTC siguiente al `--date`; cuáles 4
pruebas difieren entre Windows y el CI; la lectura real del HDF y la forma del MxD03 real (el arnés las reemplaza).
