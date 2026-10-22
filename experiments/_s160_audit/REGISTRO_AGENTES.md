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
