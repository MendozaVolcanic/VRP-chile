# Pre-registro S190: A/B de fase de la grilla en VIIRS 750 (L1B estándar, solo lectura)

Sellado antes de correr: este archivo, `armar_manifiesto.py`, `manifiesto_s190.json`, `ab_fase.py` y `leer_ab.py` quedan en
un commit con tag `s190-prereg-fase` empujado ANTES del despacho del workflow. Nada de lo de abajo se cambia después de
ver resultados; si algo resulta mal especificado, se anota como desvío en el informe con su efecto, sin reescribir la regla.

## 1. Pregunta y por qué

MIROVA interpola cada gránulo a una grilla UTM fija por volcán; la vía «código MIROVA» usa la misma regla
(`pipeline/grillas_mirova.yaml`, centros en X0 - 25000 : 750 : X0 + 25000). En Tupungatito V750 hay 6 pasadas que MIROVA
alerta y la vía calla, con la celda del cráter al 0,73 a 0,93 de su umbral. El probe S185 (PR #1018, run 43724596931)
mostró que la decisión es sensible a cómo cae el retículo de la grilla sobre el píxel caliente: con la grilla corrida
media celda al norte (o al sur, que es la misma fase), las 6 alertan y los 4 controles siguen. Físicamente es plausible:
un píxel nativo de 750 m que calienta una sola celda la alerta, y el mismo calor repartido entre dos celdas por la
interpolación lineal queda bajo el umbral en ambas. Pero S185 eligió esa fase mirando esas mismas 10 pasadas, todas con
margen cerca de 1, donde cualquier perturbación da vuelta la decisión. La pregunta de este A/B es si la fase N/S se
acerca a MIROVA en pasadas que no se usaron para elegirla, y cuánto daña (A116).

## 2. Pasadas (manifiesto_s190.json, armado por `armar_manifiesto.py`, semilla 190)

Universo: records V750 nocturnos de la vía en los 11 Tier A, 2026-03-01 a 2026-11-14, con celda decisiva, pareados con
la tabla de MIROVA (`registro_vrp_consolidado.csv`, Sensor VIIRS, |Δt| ≤ 120 s, como S185) con fila ALERTA_TERMICA o
RUTINA. Categorías según lo PUBLICADO por la vía (brazo A):
- `calla`: MIROVA alerta, la vía no. `solo_via`: MIROVA rutina, la vía alerta.
- `ambos`: los dos alertan. `rutina`: ninguno.

Estratos y muestra (la población excluye las 10 pasadas de Tupungatito de S185, que se corren aparte como réplica y no
puntúan): `calla` todas (12: Puyehue 8, Isluga 3, Copahue 1), `solo_via` todas (19), rutinas por el margen publicado de la
celda decisiva (≥ 0,9 todas, 44; 0,8 a 0,9: 30 de 86; 0,6 a 0,8: 30 de 305; 0,3 a 0,6: 12 de 1.811; < 0,3: 8 de 4.596,
negativos limpios), ambos (margen < 1,2: 20 de 58; 1,2 a 1,5: 10 de 69; ≥ 1,5: 8 de 210). Total 193 que puntúan y 10 de
réplica, 178 gránulos distintos.

## 3. Brazos

Mismo gránulo, misma vía (`pipeline.mirova_v750_codigo.calcular_vrp_granulo`, remuestreo lineal de producción), solo
cambia la esquina de la grilla (la celda del cráter y la caja se recalculan solas):
- **A, producción**: grilla de `grillas_mirova.yaml`.
- **B, fase N/S** (la hipótesis): esquina corrida +0,5 celda al norte (375 m).
- **C, fase diagonal** (descriptiva): +0,5 celda al este y +0,5 al norte (la confusión esquina contra centro de un
  raster). No decide nada.
- **Z, fase E/O** (control de perturbación): +0,5 celda al este. Si B gana solo porque cualquier corrimiento da vuelta
  pasadas cerca del umbral, Z debería ganar parecido.

Decisión por pasada y brazo: alerta si el record del brazo tiene `n_anomalous_pixels > 0` (lo que la vía publica).

## 4. Métricas

Por brazo X sobre las pasadas que puntúan y son válidas:
- Ganancia: `calla` que X alerta; `solo_via` que X apaga. Daño: `ambos` que X apaga; `rutina` que X alerta.
- Peso de cada pasada: población del estrato / pasadas válidas del estrato. G_X y D_X son las sumas pesadas; Net_X = G_X - D_X.
- Por construcción el brazo A da G = D = 0 si reproduce lo publicado: es el control que se cancela solo (A110).

## 5. Validez (si falla, el veredicto es SIN DATO)

- V1. El brazo A reproduce el record publicado (mismo `n_anomalous_pixels`, misma celda decisiva y margen a 1e-3) en ≥ 90 %
  de las pasadas que puntúan, y las válidas son ≥ 80 % en `calla` y en `solo_via`. Las que no reproducen se excluyen de
  todos los brazos y se listan.
- V2. Réplica: en las 10 de S185, B alerta al menos 5 de las 6 calladas (S185 midió 6 de 6). Si no, el instrumento no
  reproduce el probe anterior.
- V3 (A116, el instrumento puede dar distinto de cero). B cambia la decisión en al menos 1 pasada válida que puntúa. Si
  ninguna cambia, el veredicto es NO CUMPLE por falta de efecto (no hay nada que adoptar).

## 6. Regla de adopción del brazo B (CUMPLE solo si se cumplen las 5)

- C1. B no apaga ninguna `ambos` con VRP de MIROVA ≥ 1 MW (alerta protegida, criterio de victoria de `docs/MISSION.md`).
- C2. B no alerta ninguna `rutina` con margen publicado < 0,6 (una sola, con su peso, son 10 a 575 falsos positivos).
- C3. Net_B ≥ 3 y G_B ≥ 2 · D_B.
- C4. B alerta al menos 6 de las 12 `calla` fuera de Tupungatito (cuenta sin peso).
- C5. Net_B - Net_Z ≥ 3.

NO CUMPLE: válido y falla al menos una. El brazo C se informa con las mismas métricas; si cumpliera C1 a C5 con Net_C
mayor que Net_B, queda como SOSPECHA para un pre-registro nuevo, no se adopta.

Aunque B cumpla, esto no cambia producción: la grilla sale del GeoTIFF de MIROVA (A5, A63) y moverla toca
`grillas_mirova.yaml` (A45). CUMPLE significa «hay razón para revisar la georreferencia de la grilla con Nicolás»; la
decisión es suya.

## 7. Se informa además (descriptivo)

Cociente de margen B/A por pasada (rango y mediana), conteos sin peso por estrato y por brazo, desglose por volcán y por
satélite, y la réplica de las 10 de S185 en los cuatro brazos.

## 8. Reservas conocidas antes de correr

- La tabla de MIROVA dice «VIIRS» sin separar 375 de 750; el pareo por hora puede tomar una fila que MIROVA sacó del I-band.
- Algunas pasadas de la población pueden ser reprocesos con otro gránulo que el publicado; V1 las saca si no reproducen.
- El margen de la celda decisiva mira el 7 x 7 del cráter; en Puyehue MIROVA alerta a 7 u 8 km, fuera de ese cuadro. Por eso
  la decisión es `n_anomalous_pixels > 0` y el margen solo sirve para estratificar.
- Los pesos de los estratos grandes (0,3 a 0,6: 151 por pasada) hacen que una sola rutina alertada ahí hunda el saldo: es a
  propósito (C2).
