# Censo del oráculo de MIROVA en los negativos limpios de VIIRS 750 (S159, analizado por la sesión nocturna S160)

- Hora del servidor al analizar: 2026-10-22 ~04:25 UTC. Run del censo **39713438252** (rama auxiliar
  `s159-oraculo-disparo`, 32 jobs: 28 verdes, 4 en rojo por pasadas sin procesar declaradas, 20 en total) y run del
  rescate del 12-oct **39715348772** (20 pasadas, las 20 ok). Artefactos en `D:\vrp-trabajo\temporales\s159_oraculo\`.
- Pre-registro: `PREREGISTRO.md` (commiteado antes del disparo, con la adenda §8 antes del run aparte). Analizador:
  `02_analizar.py`, sin cambios de lógica después del disparo (`1259ccc66` sólo agrega una línea de salida y recorta una
  lista, hecho por el agente antes de que terminara el run). Salidas: `02_analizar_salida.txt` (principal, sin el
  rescate) y `02_analizar_salida_con_rescate.txt` (con el estrato del 12-oct reemplazando a sus SIN DATO), más las
  tablas `tabla_por_pasada*.csv`, `negativos_publicados*.csv` y `resumen*.json`.
- Quién: el agente de S159 diseñó, pre-registró y despachó; murió antes de que terminara el run. El análisis lo corrió
  la sesión nocturna (Opus 5.5) con el analizador pre-registrado, sin tocarlo. **Sin verificador todavía.**
- Ventana de todos los números: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 ni el 19 de octubre; pareo a
  120 s; regla D-9 SN; lectura A de protegidas; predicado «publica» del tablero ejecutado con node (A97).

## En una pantalla

1. **Los cuatro controles pasan, antes de mirar el resultado**: K = producción en 5.620 de 5.620 pasadas ok (publica y
   `pc.vrp_mw` a 0,001 MW); oráculo = frente N en 1.006 de 1.006 comparaciones; las 1.006 perturbaciones del nulo
   cambian la publicación; el oráculo detecta las alertas de MIROVA con razón 1,000 (O-def, 193 de 253) y 0,999 (O-sens,
   241 de 253).
2. **El efecto del oráculo en negativos ya no tiene la cota abierta del frente N** («hasta ~139 más»): sobre los 5.353
   negativos limpios ok, **O-def publica 5 y O-sens 15**, contra **54 de K**.
3. **O-def: PIERDE PROTEGIDAS** (6, todas de Cordón Caulle, 1,00 a 1,43 MW), aunque ΔE sea −60 (rango −62 a −43).
4. **O-sens: GANA EN EL CENSO**: 0 protegidas perdidas y 1 ganada; ΔE **−90** (rango −92 a −73). Con el estrato
   rescatado del 12-oct: 0 SIN DATO, ΔE −92, mismo veredicto.
5. Las etiquetas son descriptivas (pre-registro §4): **no deciden ninguna adopción**, eso es la ola 3 con su propio
   pre-registro y sello de Nicolás.

## Resultado por caja (principal, sin el rescate)

| | negativos publicados (de 5.353 ok) | encendidos / apagados | protegidas perdidas / ganadas | bajo 1 MW sin publicar (K / O) | ΔE (rango por SIN DATO) | etiqueta |
|---|---|---|---|---|---|---|
| K | 54 (1,01 %) | | | 65 | | |
| O-def | 5 (0,09 %) | 1 / 50 | 6 / 0 | 65 / 54 | −60 (−62 a −43) | PIERDE PROTEGIDAS |
| O-sens | 15 (0,28 %) | 7 / 46 | 0 / 1 | 65 / 14 | −90 (−92 a −73) | GANA EN EL CENSO |

- Sensibilidad declarada (distancia desde `volcanoes.yaml` en vez del centro del TIF): O-def ΔE −59, O-sens 16
  negativos y ΔE −88; mismas etiquetas.
- Por volcán, los 15 negativos de O-sens: Tupungatito 5, Isluga 3, Láscar 3, Cordón Caulle 3, Llaima 1. Los 54 de K:
  Cordón Caulle 25, Isluga 10, Láscar 9, Tupungatito 4, Chaitén 3, y 1 en Llaima, Chillán y Villarrica. O-sens publica
  en Tupungatito 5 negativos donde K publica 4 (el único volcán donde el oráculo publica más), con píxeles a 4,8 a
  6,7 km del centro y temperaturas de 226 a 263 K.
- Por cenit: O-sens 11 de 1.891 con cenit ≤ 40° y 4 de 3.568 sobre 40°; K 41 y 13.
- Bajo 1 MW: O-sens pierde 8 que K publica (Cordón Caulle 4, Isluga 2, Láscar 1, Tupungatito 1) y gana 59.
- Las 14 alertas sólo OCR anteriores al 13-jun (no deciden, A119): K publica 14, O-def 13, O-sens 14.
- Pasadas fuera del gránulo (el píxel más cercano al centro a más de 5 km): 106, todas negativos limpios; no son SIN
  DATO y ninguna caja publica en ellas.

## Estrato rescatado del 12-oct (adenda §8)

Las 20 pasadas de los cuatro gránulos reprocesados por NASA (VJ202MOD 05:12 y 05:18, VNP02MOD 05:48 y 05:54) corren
todas: 17 negativos limpios y 3 alertas (la protegida de Chillán 05:18, Isluga 05:48 y Chillán 05:54). Ninguna caja
publica en esos negativos; O-sens detecta la protegida de Chillán. El pre-registro decía que el control 1 no aplica
ahí (producción procesó el archivo original); igual da 0 diferencias en las 5.640 pasadas ok, o sea que K sobre el
archivo nuevo publica lo mismo que producción sobre el viejo en esas 20.

## Qué NO dice

- No es un A/B de adopción ni toca producción. Es un censo de sólo lectura de un oráculo validado contra Octave.
- Sólo VIIRS 750. No dice nada de VIIRS 375 ni de MODIS (ver `experiments/_s159/portes/`).
- La etiqueta positiva que decide después del 13-jun incluye alertas del OCR. El analizador no da la lectura con la
  tabla de `latest.php` sola, que Nicolás considera la más creíble; queda como seguimiento (se puede sacar de
  `tabla_por_pasada*.csv` si trae el canal de cada alerta, SIN VERIFICAR que lo traiga).
- Las 6 protegidas que pierde O-def son las mismas de Cordón Caulle que ya había visto el frente N: la caja por
  defecto las deja fuera y la sensible no. Que sea porque el campo difuso del lacolito (A68) cae fuera de la cumbre de
  7 × 7 es SOSPECHA: este análisis no lo midió.
