# S190: A/B de fase de la grilla en VIIRS 750 y una hipótesis más para Chillán V375

2026-11-17. Sigue al probe L1B de S185 (PR #1018). Pre-registro: [`PREREGISTRO.md`](PREREGISTRO.md), sellado en el commit
`269165227` (tag `s190-prereg-fase`) antes del despacho. Nada tocó `pipeline/`, `data/` ni `frontend/`.

## 0. Veredictos

| Pregunta | Veredicto | Una línea |
|---|---|---|
| ¿Correr la grilla media celda al N/S acerca la vía a MIROVA en VIIRS 750? | **NO CUMPLE** | Recupera 8 de las 12 calladas fuera de Tupungatito, pero apaga 12 alertas que MIROVA también ve y enciende 26 rutinas: daña más de lo que arregla. |
| ¿Explica la fase de la grilla las 6 calladas de Tupungatito? | **REFUTADO como explicación** | Las 6 se dan vuelta con B, pero cualquier corrimiento da vuelta pasadas cerca del umbral en las dos direcciones; la grilla de producción es la de los cuatro brazos que más coincide con MIROVA. |
| Chillán V375: ¿la cola baja del este viene del gránulo estándar de I-band (y no del NRT que pudo ver MIROVA)? | **REFUTADO en la 11-14 (n = 1); SIN DATO en las otras dos** | El NRT y el estándar dan el mismo VRP, 19,875 MW. La causa sigue SIN ATRIBUIR. |

## 1. Por qué este A/B

MIROVA interpola cada pasada a una grilla UTM fija de celdas de 750 m centrada en el volcán. Un píxel caliente que cae
entero en una celda la enciende; el mismo calor repartido entre dos celdas por la interpolación puede quedar bajo el
umbral en ambas. S185 vio que con la grilla corrida media celda al norte (o al sur, que es la misma fase) las 6 pasadas de
Tupungatito que MIROVA alerta y la vía calla pasaban a alertar, sin perder los 4 controles. Pero esas 10 pasadas estaban
todas cerca del umbral (margen 0,73 a 1,20) y se usaron para elegir la fase. Este A/B la prueba sobre pasadas nuevas y
mide también el daño (A116).

## 2. Qué se corrió

- **Pasadas**: 193 que puntúan, de los 11 Tier A (2026-03-01 a 2026-11-14, nocturnas, pareadas con la tabla de MIROVA), por
  estratos: las 12 calladas fuera de Tupungatito (Puyehue 8, Isluga 3, Copahue 1), las 19 «solo vía», rutinas y «ambos» por
  margen; más las 10 de S185 como réplica (no puntúan). 178 gránulos (~20 GB bajados y borrados en los runners).
- **Brazos**: A producción; B +0,5 celda al norte (la hipótesis); C +0,5 este y +0,5 norte (descriptiva); Z +0,5 este (control
  de perturbación). Misma vía, mismo remuestreo lineal; solo cambia la esquina de la grilla.
- **Runs**: 44016316141 (6 partes; la parte 0 perdió 9 gránulos porque un solo timeout de búsqueda en CMR encendió el
  cortacircuito S116 del pipeline y saltó el resto, lo mismo en su reintento) y 44024005897 (reintento de esos 9, desvío
  operativo en `reintento.py`, commit `7cdce99ed`: misma medición, manifiesto sellado, cortacircuito reseteado por gránulo).
  Ensamblado: partes 1 a 5 y lo que salió de la parte 0 en el intento 1, más el reintento; 203 de 203 pasadas, sin
  duplicados (`resultados/`).
- **Lector**: `leer_ab.py` sellado, sin cambios; salida en `resultados/veredicto.json`.

## 3. Resultado

**Validez**: el brazo A reproduce lo publicado (mismos píxeles, misma celda decisiva, margen a 1e-3) en 193 de 193 (V1);
la réplica da 6 de 6 calladas de S185 alertadas por B (V2); B cambia la decisión en 52 pasadas (V3).

Por brazo, pesos de la población (G ganancia, D daño, Net = G - D):

| Brazo | G | D | Net | Calladas recuperadas (de 12) | Pasadas que cambian |
|---|---|---|---|---|---|
| A producción | 0 | 0 | 0 | 0 | 0 |
| B N/S | 14,0 | 103,8 | -89,8 | 8 | 52 |
| C diagonal | 15,0 | 144,8 | -129,8 | 8 | 55 |
| Z E/O | 13,0 | 135,8 | -122,8 | 6 | 50 |

Criterios de B: C1 (ninguna alerta ≥ 1 MW perdida) cumple; C2 (ninguna rutina de margen < 0,6 alertada) cumple; **C3 (Net ≥ 3 y
G ≥ 2 D) no cumple**; C4 (≥ 6 de 12 calladas) cumple; C5 (Net_B - Net_Z ≥ 3) cumple. Veredicto: **NO CUMPLE**.

Lo mismo sin pesos, contando pasadas, para que se vea que no es un artefacto de la ponderación:

| Brazo | Calladas que alerta | Solo vía que apaga | «Ambos» que apaga | Rutinas que alerta | Saldo |
|---|---|---|---|---|---|
| B | 8 | 6 | 12 | 26 | 14 contra 38 |
| C | 8 | 7 | 15 | 25 | 15 contra 40 |
| Z | 6 | 7 | 20 | 17 | 13 contra 37 |

Las rutinas que B enciende están casi todas en el estrato de margen ≥ 0,9 (19 de 44), y las «ambos» que apaga en el de
margen < 1,2 (10 de 20): **B no se acerca a MIROVA, mueve hacia los dos lados las pasadas que están cerca del umbral**
(apaga 18 alertas de A y enciende 34). El cociente del margen máximo del 7 x 7 del cráter, B sobre A (no es la misma celda:
la decisiva coincide en 77 de 193), va de 0,24 a 8,1 con mediana 0,91, igual que Z sobre A (0,91). Por volcán solo Puyehue
gana en neto (6 ganancias, 4 daños; Z casi igual) y Copahue (1 y 0); Láscar, Isluga y Tupungatito empeoran. Por satélite B
pierde en los tres (NOAA-20 9 contra 14, NOAA-21 3 contra 21, Suomi NPP 2 contra 3). La réplica de S185 se entiende ahora:
10 pasadas elegidas con margen cerca de 1 se dan vuelta con cualquier corrimiento.

Un matiz que encontró el verificador (descriptivo, post hoc): entre las pasadas que A no alerta, cualquier corrimiento
enciende más las que MIROVA alerta que las rutinas (B 8 de 12 contra 26 de 124, Fisher p 0,002; Z 6 de 12 contra 17 de 124,
p 0,006). Las calladas tienen señal real bajo el umbral en el cráter (en ellas el cociente B/A sube a 1,17, 11 de 12 sobre
1); lo que no tienen es una fase que la saque sin encender rutinas. No es propio de B.

**Lectura física.** La fase de producción es la que más coincide con MIROVA de las cuatro, como se espera si nuestra grilla
ya es la de MIROVA (la regla GEO se verificó a 1 m contra sus GeoTIFF, S159). Las 6 calladas de Tupungatito quedan sin
explicar por la fase: son pasadas a 7 a 27 % bajo el umbral, y la diferencia con MIROVA está en otra parte (el remuestreo
de MIROVA no publicado o el producto que vio, que ya no se puede bajar: el NRT de LANCE dura ~7 días, S185 §1).

## 4. Chillán V375: una hipótesis más (`chi/`)

**Hipótesis**: la cola baja del lado este viene del gránulo estándar de I-band, distinto del NRT que pudo usar MIROVA. S185
la había descartado porque el V750 de la misma pasada reproduce a MIROVA, pero I-band (VJ202IMG) y M-band (VJ202MOD) son
productos distintos y el V750 no prueba nada del I-band.

**Sonda sin descarga** (`chi/1_nrt_vs_std_git.py`): el record que la vía escribió con el gránulo NRT quedó en la historia git
de `data/mirova_equivalent/NevadosDeChillan.json` antes de que el pipeline lo pasara a estándar.

- 2026-11-14 05:00 NOAA-21 (baja, razón 0,676): NRT `VJ202IMG_NRT.A2026318.0500.021.2026318065559.nc`, con la vía encendida,
  19,875 MW y 13 píxeles (record de las 07:27 UTC, antes de que existiera el estándar); estándar
  `VJ202IMG.A2026318.0500.021.2026318102827.nc`, 19,875 MW dos veces: en el record que el pipeline recalculó a las 11:27 UTC y
  en el recálculo del probe S185 desde el L1B. **Igual: REFUTADO** para esta pasada.
- 10-29 y 10-10: sus records de la época NRT son del detector anterior (sin la vía) o nacieron estándar. **SIN DATO**.

**Chillán queda SIN ATRIBUIR.** Descartado hasta hoy: selección de cúmulo, fondo del anillo como causa principal, saturación
como causa única, borde de grilla, NRT contra estándar en V750 (S185 V375-F); huecos de bow-tie, grosor del píxel (no
concluyente), paralaje de terreno (descriptivo) (S185 L1B); NRT contra estándar en I-band en la 11-14 (este informe). Queda
como SOSPECHA débil el remuestreo (n = 3). Lo que cerraría: el remuestreo de MIROVA para V375 (no publicado) o más bajas del
este capturando su NRT dentro de los 7 días de LANCE.

## 5. Recomendación para Nicolás

- **No cambiar la grilla.** La fase de producción es la mejor de las cuatro; correrla empeora la coincidencia con MIROVA.
  Nada que decidir en `grillas_mirova.yaml`.
- **Tupungatito V750**: cerrar la vía de la fase. Lo que queda abierto es el remuestreo de MIROVA y el producto NRT; para lo
  segundo, la única vía es capturar el NRT de la próxima alerta de MIROVA que la vía calle, dentro de 7 días.
- **Chillán V375**: SIN ATRIBUIR, con la lista de arriba. No gastar más descargas sin una hipótesis nueva.
- **Operativo**: el cortacircuito de búsqueda de CMR se enciende con un solo ReadTimeout y salta todo lo que queda de la
  corrida; en un probe largo eso pierde decenas de pasadas. En el NRT está pensado así (S116); en probes conviene resetearlo
  por gránulo como hace `reintento.py`.

## 6. Reservas

- La reserva §8 del pre-registro («la tabla no separa 375 de 750») era infundada: el CSV trae «VIIRS» (17.511 filas, el
  750) y «VIIRS375» (16.825) por separado, y el pareo usó «VIIRS». Ningún record tiene más de una fila a menos de 120 s.
- 2 pasadas «ambos» (Láscar 11-05 y Chillán 11-06) se midieron con un gránulo reprocesado distinto del publicado; reproducen
  igual.
- V2 no exige que la réplica reproduzca lo publicado; sin efecto, las 10 reproducen.
- Los pesos de los estratos grandes son toscos; por eso se muestra también el conteo sin pesos, que da lo mismo.
- La sonda de Chillán es n = 1.

## 7. Verificación independiente

Verificador con contexto limpio (Opus, effort high), scripts propios en `D:\vrp-trabajo\temporales\s190_l1b_ab_verif\`
que no importan `leer_ab.py` ni `ab_fase.py`. Cobertura: leyó el pre-registro entero y todo el código del experimento, los
logs de la parte 0 en los dos intentos y el reintento, `store.py` y la historia git del record de Chillán; reconstruyó el
manifiesto desde los datos del commit `13af35186`.
- CONFIRMADO: 203 de 203 pasadas sin duplicados; las 23 pasadas medidas en los dos intentos de la parte 0 dan los 4 brazos
  idénticos (el ensamblado equivale al intento 2); las métricas, pesos y criterios de B, C y Z, y el veredicto NO CUMPLE;
  el manifiesto (población, semilla, réplica, 178 gránulos); 14 contra 38 sin pesos; el valor 19,875 MW de Chillán.
- CORREGIDO aquí: el cociente B/A es del margen máximo del 7 x 7, no de la misma celda; la reserva de 375 contra 750; el
  matiz de las calladas; el desglose por satélite (§7 del pre-registro, que `leer_ab.py` no calculaba).
- CORREGIDO en la nota de Chillán: el paso de NRT a estándar en `store.py` recalcula el record desde el gránulo estándar (no
  copia el valor), así que el record estándar de git es una medición independiente del NRT, y el recálculo de S185 es una
  segunda confirmación. El valor NRT nació a las 07:27 UTC, antes de que existiera el estándar (10:28 UTC).
