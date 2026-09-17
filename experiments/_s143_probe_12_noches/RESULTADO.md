# Resultado del probe S143 de las 12 noches

Generado por `analizar.py` desde `resultado.json` (2026-09-17T19:19:49+00:00). Ningún número escrito a mano.

**Lectura pre-registrada:** ambas recuperan: comparar costo en negativos; la de menor costo al A/B, la otra como ablacion

## Control de instrumento

- 1_todas_ok: cumple
- 2a_control_recupera_11: cumple
- 2b_s135_d_recupera_max_1: cumple
- 3_envoltorio_coherente: cumple
- 4_control_publica_11_neg_artefacto: cumple

## Por variante

| variante | pasadas ok | noches recuperadas (con cota) | sin cota | neg_artefacto publicadas | neg_quieta publicadas | pasadas con filtro del Test 1 |
|---|---|---|---|---|---|---|
| control | 61 de 61 | 12 de 12 | 12 | 12 de 12 | 0 de 8 | 50 |
| s135_d | 61 de 61 | 0 de 12 | 0 | 0 de 12 | 0 de 8 | 53 |
| s135_d_sin_compuerta_ctx | 61 de 61 | 11 de 12 | 12 | 7 de 12 | 0 de 8 | 53 |
| literal | 61 de 61 | 10 de 12 | 12 | 6 de 12 | 1 de 8 | 47 |
| literal_sin_compuerta_ctx | 61 de 61 | 11 de 12 | 12 | 9 de 12 | 1 de 8 | 32 |
| literal_t1_sin_filtro | 61 de 61 | 12 de 12 | 12 | 12 de 12 | 1 de 8 | 0 |

## Noche por noche (con cota)

| noche | control | s135_d | s135_d_sin_compuerta_ctx | literal | literal_sin_compuerta_ctx | literal_t1_sin_filtro |
|---|---|---|---|---|---|---|
| Isluga|2026-07-01 | sí | no | sí | sí | sí | sí |
| Isluga|2026-07-16 | sí | no | sí | sí | sí | sí |
| Isluga|2026-08-19 | sí | no | sí | sí | sí | sí |
| Lastarria|2026-07-02 | sí | no | sí | sí | sí | sí |
| Lastarria|2026-08-28 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-06-22 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-06-26 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-07-24 | sí | no | no | no | no | sí |
| PlanchonPeteroa|2026-08-09 | sí | no | sí | sí | sí | sí |
| PlanchonPeteroa|2026-08-24 | sí | no | sí | no | sí | sí |
| Tupungatito|2026-07-07 | sí | no | sí | sí | sí | sí |
| Tupungatito|2026-08-01 | sí | no | sí | sí | sí | sí |
