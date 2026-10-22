# Registro de modelo, esfuerzo y consumo por agente (plan §7)

Hora del servidor al armar este registro: Thu, 22 Oct 2026 03:18:42 GMT. Esfuerzo: el de defecto del subagente (high), sin override.

| agente | modelo | lanzado (UTC aprox.) | terminó | duración | tokens | tool uses | hallazgos | confirmados por su verificador |
|---|---|---|---|---|---|---|---|---|
| guía §10 (no auditor) | Opus | 03:05 | 03:07 | 2 min 20 s | 192.402 | 24 | 18 de 19 puntos | revisado el diff por el orquestador |
| F2 | Fable | 03:14 | 03:40 | 26 min | 431.765 | 77 | ver f2/hallazgos.csv | |
| F3 | Fable | 03:16 | 03:39 | 24 min | 384.716 | 64 | 16 (9 de gravedad 3+) | |
| F4 | Fable | 03:18 | 03:47 | 29 min | 455.480 | 70 | 17 (281 a 297) | |
| F1a | Fable | 03:24 | 03:54 | 29 min | 503.001 | 83 | 6 (161 a 166) | |
| V2 | Opus | 03:45 | 04:01 | 16 min | 316.650 | 66 | 11 verificados + 4 propios | 203 CONFIRMADO g5; 201 EN PARTE g3; 211 REFUTADO; 213, 202, 205, 206, 207, 208 CONFIRMADOS; 209 y 204 EN PARTE. caminos.md sha256 787d157d coincide |
| V3 | Opus | 03:42 | 04:05 | 23 min | ver task | | 9 verificados + 4 propios | 241 EN PARTE g4 (no 5); 242 «sin push» REFUTADO por el tiempo (PR #892 a las 03:33); 243, 244, 246, 247, 248 CONFIRMADOS; 245, 252 EN PARTE |
| V4 | Opus | 04:02 | 04:2x | ver task | | | 12 verificados + 3 propios | 281 EN PARTE g4; 284 REFUTADO; 282, 283, 286, 287, 293 EN PARTE; 285, 288, 289, 290, 291 CONFIRMADOS |
| F0a | Fable | 04:07 | 04:20 | 13 min | ver task | | 10 pendientes S158 + 1 propio | 7 CONFIRMADOS, 3 EN PARTE, 0 REFUTADOS; F1-H6 sube a g4, F6-3 a g3; V0a-01 nada de S158 en main |
| V1a | Opus (el agente declara esfuerzo bajo, no high) | 03:48 | 04:25 | 37 min | ver task | | 3 hallazgos + 3 celdas | 161 primera mitad CONFIRMADA (placebo al azar pasa 16 de 30 en V1), segunda mitad CONFIRMADA (K supera el margen); g3, no 5; 162 EN PARTE g2; 163 CONFIRMADO g2; R6 CONFIRMADA, R11 EN PARTE, R17 REFUTADA |
| F1b | Fable | 03:42 | 04:30 | 48 min | 400.290 | 67 | 17 (180 a 196) + matriz de 28 instrumentos con 45 celdas FALLA | |
| F0b | Opus | 04:20 | 04:45 | 25 min | ver task | | 6 pendientes S158 + 3 propios | F4-H2 EN PARTE, F4-H3 REFUTADO EN PARTE, F4-H5, H7, H8, R2-17 CONFIRMADOS; V0b-01 K1 decide el tope D9 (Chillán protegida 11,08 a 5,0 MW con K1 -0,7) |
| V1b | Opus | 04:30 | 04:52 | 21 min | 384.714 | 137 | 5 hallazgos + 45 celdas; 4 propios | 180, 181, 182 EN PARTE y bajan de 4 a 2; 188, 189 EN PARTE; celdas 25 confirmadas o en parte, 11 refutadas o sin efecto, 9 SIN DATO; V1b-01 g3 |
| marcas A113 (no auditor) | Opus | 04:33 | 04:43 | 10 min | 279.494 | 91 | 27 marcas aplicadas, 12 sin aplicar | revisado el diff por el orquestador |
