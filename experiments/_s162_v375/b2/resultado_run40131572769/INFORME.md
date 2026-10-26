# V375-B2 (S162): resultado del lote, run 40131572769

2026-10-24. Pre-registro sellado `../PREREGISTRO_B2.md` (tag `s162-v375-b2-listo`, D-48, con «Sello» y «Adenda 1» sin
cambio de regla). Disparo `a9331d51c` (tag `s162-v375-b2-disparo-lote`), árbol de `ca034d66e` (`pipeline/` idéntico a
533398f8f). Artefactos: `C:\vrp-trabajo\temporales\s162_v375\run_40131572769\`. Lectura: `evaluar_salida.txt` y
`evaluar.json` (commit `8f2499fdc`). Verificador con contexto limpio (Sonnet): `verificador/INFORME.md`, **CONFIRMADO**.

## En una pantalla

1. **V375-B queda resuelto: el código de MIROVA portado a VIIRS 375 calla en las noches sin actividad por lo menos tanto
   como producción.** VEREDICTO B, con la regla sellada: **SILENCIO ACOTADO BAJO K**.
2. En las 1.165 noches limpias nuevas en que MIROVA miró y no vio nada y producción tampoco publica, el port publica **6**
   (0,52 % [0,24; 1,12]). Las 6 son de un solo píxel y de 0,01 a 0,04 MW (Copahue 2, Tupungatito, Nevados de Chillán,
   Isluga, Llaima). Contando todas las noches limpias, la cota superior queda en **2,48 %** contra la vara de producción,
   3,85 %. La lectura estricta (z 2,241) también queda bajo la vara (2,65 %).
3. **El instrumento está limpio.** Recálculo sin red igual al runner en 19.277 de 19.277 pares; K re-corrido igual a lo
   publicado en 2.032 de 2.032. **Control de vida: las 20 pasadas re-medidas dan exactamente lo de S162** (16 con
   píxeles), así que el port estaba vivo en este run. Cobertura: 1.220 de 1.220 con resultado; 35 no observadas (2,9 %),
   con el volcán fuera de la franja del gránulo, el mismo que usó producción.
4. **Qué quiere decir y qué no.** Quiere decir que el port publica menos que producción en las noches sin nada. No quiere
   decir que no encienda nada nuevo: apaga la mayoría de los puntos que producción publica en esas noches (el 72,5 % de
   neg_pub), y enciende pocos donde producción calla, unas 17 noches estimadas de 3.323 (0,2 a 1,1 %), todos de un
   píxel y casi todos bajo 0,05 MW.
5. La unión con S159 y S162 da lo mismo (1,70 % [1,43; 2,20]), pero no es una confirmación independiente: contiene el 73 %
   del lote que decide. La medición que decide es la de B2 sola, y basta por sí misma.

## Lo que el verificador agregó

| reparo | gravedad | cómo queda |
|---|---|---|
| La unión no confirma de forma independiente (73 % del lote que decide) | 2 | declarado en el punto 5 |
| La cuenta mide «menos publicaciones que K», no «ninguna publicación nueva» | 2 | declarado en el punto 4 |
| neg_pub que decide es la muestra de 113 de 133 de S162; la sección 3 de la salida rotula «censo» al pool de 133 | 1 | sesgo conservador; el rótulo de la sección 3 se corrige si se reusa el evaluador |
| Las 10 publicaciones en neg_resto (S162 y B2) son de 1 píxel y de 0,01 a 0,052 MW; 9 de 10 bajo 0,05 MW | 1 | informado |
| Heterogeneidad por volcán que el intervalo agrupado no modela (Lastarria 2 de 12 en S162 y 0 de 40 en B2) | 1 | SOSPECHA |
| La clave de la caché de brazos no incluye la versión de `brazos.py` | 2 | sin hallazgo en la muestra: un recálculo fresco de 50 pasadas da 0 diferencias |
| El control de vida cubre 6 de los 11 volcanes | 2 | SOSPECHA, ya declarada en la adenda 1 (H4) |

## Para PD1 y V375-E

- **V375-B: RESUELTO** a favor del silencio (con V375-B2). El paquete de VIIRS 375 no enciende de más en las noches sin
  actividad.
- **V375-C**: caja C13 en el cráter (`../../resultado_run40116289866/INFORME.md`).
- **V375-D**: no se abre.
- **V375-E** sigue esperando la decisión de PD1, la vía de proceso en `pipeline/` (PD3) y los PR #903 y #905. El riesgo
  que queda para su veto de adopción son las 6 protegidas sólo OCR de Suomi NPP que pierden todos los brazos.
