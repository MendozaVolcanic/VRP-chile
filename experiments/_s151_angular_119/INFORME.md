# Tarea 1.19: la dependencia angular de la magnitud VIIRS 375 sí viene de la huella del píxel

Carpeta: `C:\Users\nmend\AppData\Local\Temp\claude\angular_119\`. Sólo lectura sobre el repo (pipeline en `427c0b013`,
`02_commit_pipeline.txt`). Predicciones escritas antes de correr: `PREREGISTRO.md`. Ángulos leídos en la página
renderizada (`pag/geo_35.png`, `pag/geo_48.png`, `pag/img_20.png`, `pag/geo_34.png`): agregación 3:1 hasta 31,589° de
barrido, 2:1 hasta 44,680°, 1:1 hasta 56,063° (ATBD de geolocalización 2014, p. 14 y 27; ATBD de imagen RevE, p. 21,
altitud 833 km). En cenit: **36,32° y 52,66°**. En `documentacion/` no hay un «VIIRS SDR User's Guide» (NESDIS 142);
los dos ATBD dicen lo mismo.

## El fenómeno

Un foco más chico que el píxel reparte su exceso de radiancia en el píxel que lo contiene. Al alejarse del nadir el
píxel crece, y en 36,32° y 52,66° se achica de golpe a lo ancho del barrido (3 → 2 y 2 → 1 muestras sumadas). MIROVA
remuestrea a celdas de área fija: una huella grande cae en más celdas, así que su **Npix** debe bajar en el límite,
su **VRP total** no (la energía se conserva) y su **VRP/Npix** debe subir. Nosotros fijamos el área a nadir sobre el
píxel nativo: nuestro VRP sigue a 140.625 m² / A_nativo, con diente de sierra.

## (i) OSF v2.5 global (V375 noche clase 1: 208.293 filas, 158 volcanes)

Modelo: efecto fijo volcán × mes, spline continuo del cenit, un escalón en cada límite. Nulo medido: el mismo
escalón en 89 posiciones placebo, con los escalones reales dentro del modelo (`01c_nulo_placebo.py`); IC por
bootstrap de volcanes (`01b_escalones_osf.py`, `01b_salida_V375_V750.txt`). Dayflag 0 es noche (100 % de las filas
entre 18 y 6 h solar local).

| escalón (ln) | 36,32° | 52,66° | placebo \|p95\| / máx | físico, fuente extensa |
|---|---|---|---|---|
| VRP/Npix | **+0,135** [+0,067; +0,198] | **+0,216** [+0,132; +0,300] | 0,072 / 0,079 | +0,405 / +0,693 |
| Npix | −0,048 [−0,117; +0,032] | **−0,213** [−0,324; −0,094] | 0,107 / 0,154 | −0,405 / −0,693 |
| VRP total | +0,087 | +0,003 | 0,156 / 0,169 | 0 |

Hay salto, en el lugar y con el signo que pide la geometría: VRP/Npix sube 14 % y 24 %, sobre el máximo de los 89
placebos, y el VRP total no salta. Es un tercio del límite de fuente extensa (la mayoría de las filas tiene 1 a 5
celdas). Se replica por satélite: SNPP +0,149 / +0,201, NOAA-20 +0,120 / +0,253. Por tamaño de muestra: volcanes con
2.000 filas o más (42) +0,144 / +0,245; resto (116) +0,118 / +0,156 (nulo 0,114). Los 10 chilenos solos no lo
resuelven (nulo 0,375): cada volcán se ve desde pocas órbitas y sus cenits caen a un solo lado. **Control MODIS**
(no agrega): +0,010 / +0,080 en Npix (IC [−0,030; +0,051] y [−0,035; +0,167]), −0,011 / +0,075 en VRP/Npix, dentro del placebo. V750 (+0,150 / +0,152,
placebo 0,168) no se resuelve.

## (ii) Sintético con nuestro detector (`02_sintetico.py`, `02b_resumen_sintetico.py`)

Fuente a 800 K con VRP 1 y 3 MW, toda en un píxel nativo, fondo 263/261 K ± 0,5 K, Láscar, `calculate_vrp` +
`store.append_record` de producción, 24 cenits × 4 semillas. Huella: modelo esférico con agregación, no VNP03 (no
hay gránulos completos en disco); en el borde da área ×4,57 contra ×4,38 de la Tabla 2.2-1 del ATBD (+4 %).
Resultado: 192 de 192 detectadas; pendiente de ln(VRP/verdadero) sobre −ln A_nativo **0,995 y 0,998**; escalones
0,370 / 0,642 contra 0,375 / 0,642 predichos; en 67° publicamos 0,29 del verdadero. Nuestro código hace exactamente
lo que dice la fórmula: el diente de sierra entero, sin pérdida.

## ¿Explica nuestra dependencia angular? Pares S139 (1.499 pasadas V375, OSF 2025)

`03d_razon_sobre_huella.py`: mediana de R por zona, y R multiplicado por A_nativo/A_nadir.

| | 0-20° | 20-36,3 | 36,3-44 | 44-52,7 | 52,7-70 | máx/mín |
|---|---|---|---|---|---|---|
| R, sin kernel local (Láscar, Isluga, Copahue) | 0,797 | 0,611 | 0,574 | 0,423 | 0,454 | 1,88 |
| R corregido por la huella con agregación | 0,842 | 0,869 | 0,803 | 0,852 | 0,795 | **1,09** |
| control: huella suave, sin agregación | 0,842 | 0,869 | 1,205 | 1,279 | 2,385 | 2,83 |

Sí, en los volcanes sin kernel local: la huella con agregación aplana R a 0,80-0,87 (máx/mín 1,09; en Láscar sola, 1,13), y el control sin
agregación falla como debe. Regresión con efecto fijo (`03_pares_vs_huella.py`): pendiente 0,69 [0,56; 0,82] con la
magnitud publicada, 0,85 [0,71; 1,01] con `pc.vrp_mw` (Láscar 0,92), nulo barajado 0,12; escalón en 52,66°
+0,31 [0,15; 0,48]. El de 36,32° no es medible en pares: Láscar tiene 25 pares a la izquierda y 0 a la derecha,
Isluga al revés (`03b_descomposicion_angular.py`); por eso S128 no lo vio. **Con todos los volcanes no aplana**
(0,87 → 1,10, máx/mín 1,26): en los de kernel local la corrección se pasa en el borde.

## Palanca

El área, pero con la ley correcta: la huella nativa con agregación (ATBD), no el espaciado geolocalizado que S133
probó y se pasó a 1,36 en el borde (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`), ni el remuestreo completo sin medir.
En los volcanes sin kernel local dejaría un déficit plano de ~0,85 que es selección y fondo (S139, S151), ya sin ángulo. A/B a
pre-registrar con criterio por zona, C3 (0 noches perdidas) y los volcanes con kernel local medidos aparte.

**Límites.** La primera versión (`01_rd_osf.py`, ventana de ±3° con efecto fijo dentro de la ventana) diluye el salto (Npix −0,10 en 52,66°) porque deja a casi todos los volcanes de un solo lado; queda como registro. Pares de 2025, antes de #535; hay que re-medir sobre 2026. Huella modelada, +4 % en el borde. Sin PSF:
el sintético es el caso de un solo píxel.
