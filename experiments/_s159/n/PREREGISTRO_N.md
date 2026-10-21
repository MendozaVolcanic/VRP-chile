# Pre-registro del frente N (S159, ola 2): escala del fondo y la suma del código de MIROVA en VIIRS 750

> Escrito y commiteado **antes** de despachar el workflow (`probe-s159-n.yml`) y antes de ver ningún resultado de
> los brazos. Lo que cambie después de este commit va en una adenda fechada, nunca reescribiendo esto.
> Esto es MEDICIÓN: no decide adopción. Alimenta el pre-registro de adopción de la ola 3 (R2.3 de
> `tasks/LOOP_OBJETIVOS.md`).

## 1. Hipótesis y refutación (plan S159 §3, fila N)

- **Hipótesis.** Con el fondo y la suma del código de MIROVA, las alertas protegidas de VIIRS 750 se publican y los
  negativos limpios siguen callados en la proporción que exige `docs/MISSION.md` (criterio de victoria).
- **Refutación.** El brazo enciende negativos limpios por encima de lo que gana en alertas, o pierde una alerta
  protegida que producción publica.

## 2. Población (scripts `01_poblacion.py` y `02_seleccion.py`, salidas al lado)

- Pasadas VIIRS 750 nocturnas de los 11 Tier A, 2026-04-01 a 2026-10-21 (A119: VIIRS por pasada desde abril).
  Records de `data/mirova_equivalent` de `origin/main` 533398f8f; referencia remota de Mirova-v1 (consolidado
  `7ea275df`, OCR `4ddd5481`).
- Etiquetas: `scripts/banco_paridad.py::etiquetar` (pareo a ±120 s), con la regla D-9 en modo SN (en VIIRS 750 no
  toca ninguna fila: `clase_mirova.SENSORES_MINIMA` es sólo VIIRS 375). Protegida = lectura A
  (`clase_mirova.alerta_protegida`, alerta del scraper con VRP de 1 MW o más). Es la definición de `clase_mirova`
  con la regla SN; PR #889 documenta que hay otras tres.
- Pareo a 8 min (R2.3): medido, la referencia de cada pasada etiquetada está a 2 s o menos; abrir a 480 s agrega
  143 negativos limpios y 1 positivo que salen de **otro gránulo** (filas a 2 a 8 min, el gránulo vecino del mismo
  satélite). Se usa ±120 s y se informa la diferencia; no cambia ninguna pasada ya etiquetada.
- A119: en pasadas antes del 2026-06-13 la alerta que decide es la de la tabla; las alertas sólo OCR de ese tramo se
  informan aparte (campo `decide`). Excluidos de las muestras el 2026-10-18 y el 19 (CMR no los sirve, COB y R2-13);
  el 17 y el 20 entran y lo que no baje queda SIN DATO por pasada.
- Población (sin 10-18 y 10-19): 270 alertas de MIROVA (`pos`), 92 protegidas publicadas por producción, 5.476
  negativos limpios. Muestra de 398 pasadas (tope 400, aprobado por Nicolás), en cinco clases:

| clase | qué es | cómo entra | n |
|---|---|---|---|
| pos_nopub | alerta que producción no publica (lo que un brazo puede ganar) | censo | 68 |
| pos_prot | protegida que producción publica (lo que un brazo puede perder) | censo | 92 |
| pos_resto | alerta bajo 1 MW que producción publica | muestra al azar, semilla 159, peso 110/36 | 36 (+2 de R2, peso 0) |
| neg_pub | negativo limpio que producción publica (lo que un brazo puede apagar) | censo | 54 |
| neg_resto | negativo limpio que producción no publica (lo que un brazo puede encender) | muestra estratificada por volcán y cenit (≤40°, >40°), igual por estrato, peso N/n del estrato | 142 (+1 de R2, peso 0) |
| r2_fuera | Tupungatito 2026-03-01 05:36 (caso R2, fuera de ventana) | forzada | 1 |
| diurna | Chillán 2026-10-01 18:42 y 10-10 18:18 (protegidas diurnas, rb/06 de R2) | forzada, sólo oráculo | 2 |

Las pasadas forzadas de R2 con peso 0 cuentan para los controles y la tabla por pasada, no para los estimadores.

## 3. Brazos (sobre el mismo gránulo y la misma pasada; detalle en `probe_n.py`)

- **K**: `pipeline.process_viirs_mod.calculate_vrp` de hoy, y el record pasado por `pipeline.store.append_record`
  en una carpeta temporal. **K2**: K otra vez (nulo).
- **C**: K sin la compuerta `bt > t_bg + 3 K` del primer pase (D22).
- **F**: K con el fondo y la suma de `MIROVA_VIIRS750_VRP.m` (halo k × k, `fillmissing2` lineal del port R2, sin
  recorte, suma del cúmulo sin `single_pixel_mode`), en la geometría del gránulo.
- **FC**: F y C.
- **O**: el oráculo R2 (código completo) en la grilla de 750 m con la esquina de GEO; variantes de interpolador,
  la grilla vieja de R2 y el anillo con umbrales de cumbre. Referencia, no brazo.
- Construcción: reemplazo en memoria del módulo (patrón A75); `pipeline/` no se edita.

## 4. Qué se cuenta («gana» y «enciende de más»), por estrato, contra la referencia de MIROVA

«Publica» = el predicado del tablero (`isSummitDetection && isValidDetection && !isThermalArtifact &&
mirovaEqVrpDisplay > 0`) ejecutado con node desde `frontend/index.html` (`banco_paridad.correr_node`) sobre el record
que escribe `store.append_record` para ese brazo. Sólo pasadas con estado ok en K y en el brazo.

Para cada brazo X contra K, sobre la población (estimador ponderado por los pesos de §2) y sobre la muestra cruda:

1. **Protegidas perdidas**: protegidas que deciden que K publica y X no. Censo, conteo exacto.
2. **Protegidas ganadas**: protegidas que K no publica y X sí.
3. **Alertas bajo 1 MW ganadas y perdidas** (deciden, no protegidas).
4. **Negativos limpios encendidos** (X publica, K no) **y apagados** (K publica, X no).
5. **Suma de errores** `E = alertas bajo 1 MW perdidas + negativos limpios publicados` (MISSION, regla 2: bajo
   1 MW una alerta perdida y una publicación de más pesan igual). `ΔE = E_X − E_K`.

**Veredicto por brazo** (las reglas son las de `docs/MISSION.md`; ningún número de gusto):

- **PIERDE PROTEGIDA** si (1) > 0. Refuta la hipótesis para ese brazo (regla 1), diga lo que diga lo demás.
- Si no: **GANA** si `ΔE < 0` en la estimación y en los dos extremos de la banda de §5; **ENCIENDE DE MÁS** (refuta)
  si los negativos encendidos netos superan a las alertas ganadas netas (`ΔE > 0`) en la estimación y en los dos
  extremos; **EMPATE** si `ΔE = 0`; **AMBIGUO** si el signo cambia dentro de la banda.
- Incertidumbre de muestreo: intervalo de 95 % por bootstrap estratificado (2.000 réplicas, semilla 159) de `ΔE`
  ponderado. Si el intervalo contiene 0, el veredicto se informa con la marca **«no resuelto por este lote»**. El
  95 % es una convención estadística para declarar el ruido de la muestra, no un umbral de tolerancia.
- Estratos que se informan siempre: volcán, cenit (≤40° y >40°), protegida o no, tramo A119 (antes y después del
  2026-06-13, y alertas sólo OCR aparte), clase de §2.

## 5. Banda de un píxel (O1)

En F y FC el fondo depende de la triangulación de `fillmissing2`. Se corre con 20 perturbaciones (`jitter` 1e-6) y se
guarda la banda del cúmulo. Una pasada es **ambigua** si el signo de la magnitud del cúmulo cambia dentro de la banda;
`ΔE` se calcula con las ambiguas a favor y en contra. O1 midió que entre modelos de `fillmissing2` la razón llega a
1,82 en un píxel; la banda de 20 perturbaciones de un solo port es más angosta que eso y se declara como **cota
inferior** de la incertidumbre del fondo. Todo VRP de un píxel se informa con su banda.

## 6. Magnitud

Razón `pc.vrp_mw del brazo / VRP de MIROVA` en las alertas que el brazo publica: mediana y cuartiles por estrato, con la
banda en F y FC. Se informa al lado un **placebo** `K × 1,2` (D-28): la razón se mueve con el placebo por construcción,
así que es descriptiva y no entra al veredicto.

## 7. Controles que se miran ANTES del veredicto (si fallan, el veredicto no se lee)

1. **Cobertura (A108)**: pasadas con estado ok por brazo y por clase; las que faltan, listadas como SIN DATO.
2. **Nulo**: K2 idéntico a K en todos los campos del record, en todas las pasadas ok.
3. **K reproduce producción**: publica igual que el record de `data/` en todas las pasadas ok, y `pc.vrp_mw` a 0,001
   MW. Toda diferencia se lista y se explica antes de leer el veredicto.
4. **Los reemplazos actúan**: en toda pasada donde K tiene píxeles alertados, F registra llamadas al fondo y recortes
   evitados > 0; en toda pasada, C registra la compuerta reemplazada. **Control positivo de F**: Láscar 2026-10-08
   05:42, donde K publica 0,0 MW, F tiene que dar una magnitud distinta de 0,0.
5. **Control positivo del oráculo**: con la grilla vieja de R2 y el interpolador lineal, Láscar 2026-10-08 05:42 da 1
   píxel y 0,33 MW (banda 0,19 a 0,33), Chillán 2026-10-10 05:54 da 5 píxeles y 12,37 MW, Villarrica 2026-09-19 05:48
   da 2 píxeles y 0,47 MW (`docs/AUDIT_S158_R2.md` §3). Si no salen, el oráculo o la cadena están rotos.
6. **Contador de la grilla de GEO**: se informa qué cambia entre la grilla de GEO y la de R2 en Láscar 2026-09-26 y
   Chaitén 2026-10-06 (las dos alertas débiles), sin veredicto.

## 8. Lo que este pre-registro no hace

No adopta nada, no toca `pipeline/`, `data/` ni `frontend/`. VIIRS 375 y MODIS no entran a este lote (los 271
cúmulos en 0 MW de VIIRS 375, VA-2, quedan como estrato pendiente). Ampliar el tope de 400 es decisión de Nicolás.
