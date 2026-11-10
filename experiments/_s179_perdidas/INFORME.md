# S179: qué alertas de MIROVA perdemos, y por qué no vemos las fumarolas de Guallatiri y Callaqui

Fecha: 2026-11-10 (servidor ~18:15 UTC). Base: datos de producción de `origin/main` en `b68779c65` (`base_main.txt`),
worktree de sólo lectura `D:\vrp-trabajo\worktrees\s179-main`. Referencia: snapshot del repo (tabla y OCR), regla D-9
SN. Medición exploratoria del coordinador, **sin verificador**: no decide nada por sí sola.

## 1. Alertas nocturnas de MIROVA que producción no publica (2026-04-09 a 11-09)

Instrumento: `perdidas_por_pasada.py`, que importa `scripts/banco_paridad.py` (mismo pareo a ±120 s, mismo predicado
del tablero con node). Salidas: `salida_0409_1109.txt`, `perdidas_0409_1109.json`; recall agregado en
`banco_paridad_0409_1109_salida.txt`.

- 145 de 1.703 pasadas con alerta de MIROVA sin publicar (8,5 %). Por magnitud de MIROVA: 97 bajo 0,3 MW, 38 entre 0,3
  y 1 MW, 10 de 1 MW o más.
- Por sensor: VIIRS 750 70 de 312 (recall por pasada 77,6 %, el peor; Isluga 20 de 36, Planchón 8 de 9, Tupungatito 8
  de 10, Cordón Caulle 14 de 54); VIIRS 375 62 de 1.302 (95,2 %); MODIS 13 de 89 (85,4 %).
- Las 10 de 1 MW o más: 5 de VIIRS 375 son filas sólo OCR, sin distancia en la tabla, donde nuestro foco estaba lejos
  (8 a 22 km): ambiguas, las clasifica V375-A; 4 de MODIS en Chillán (12, 15, 25 y 30 de octubre, MIROVA 1,0 a 3,8 MW a
  2,2 a 2,8 km) con K, que no vio nada (0 píxeles en 3 de 4); 1 de VIIRS 750 en Cordón Caulle (10-oct, 1,19 MW). En las
  10, esa misma noche publicamos otra pasada del mismo volcán: el operador vio algo.
- 15 noches de volcán con alerta de MIROVA y nada publicado por nosotros.
- Desde que MODIS corre la vía (2026-11-02 a 11-09): 6 de 100 sin publicar, todas bajo 0,3 MW, ninguna de MODIS.
- Misma semana, mismas 600 pasadas, producción contra la sombra de la vía (inline, no guardado como script): VIIRS 750
  publica 21 de 25 alertas con K y 24 de 25 con la vía; VIIRS 375, 53 y 52 de 55; en negativos limpios la vía publica
  menos (VIIRS 750 3 contra 0 de 155; VIIRS 375 3 contra 1 de 86). n chico: exploratorio.

Lectura: las pérdidas son sobre todo alertas débiles de VIIRS 750 con el detector K, el que la vía reemplaza (B2, #983).
La retrospectiva que dio «ninguna protegida perdida» decidió con F26 (febrero y marzo de 2026, `PREREGISTRO_RETRO_PAQUETE.md`
§3.2), una ventana sin la erupción de Chillán; octubre (DM) entró sólo como control de montaje.

## 2. Alertas diurnas de MIROVA (el NRT no procesa de día, D-10, #813)

`margen_34_y_diurnas.py`, salida `salida_margen_34_y_diurnas.txt`. En la misma ventana MIROVA tiene 162 filas de
alerta diurnas (contra 2.037 nocturnas), 138 de 1 MW o más; por volcán, Chillán 63, Lastarria 30, Láscar 28. Son filas
(una pasada puede tener CONS y OCR). Ninguna métrica nocturna las cuenta. Parte puede ser artefacto solar (A76); la de
Chillán coincide con su erupción.

## 3. Guallatiri y Callaqui

- MIROVA no los vigila: no están en `http://www.mirovaweb.it/NRT/volcanoes.php` (consultado 2026-11-10). Tampoco están
  en nuestra referencia (el scraper baja 11 volcanes). Corren sólo en la sombra de los 34, que no se publica.
- Sombra de los 34 con la vía (2026-11-03 a 11-09): Guallatiri tiene una celda de cumbre que se repite (fila 69, col 66
  de la grilla de VIIRS 375, 5 de 16 pasadas) con margen 0,24 a 0,68 del umbral de MIROVA en VIIRS 375 (mediana 0,43
  en NOAA-20): hay una señal tibia persistente, por debajo del umbral. Callaqui no tiene una celda que se repita y su
  margen mediano es 0,10 a 0,17: no hay señal distinguible del ruido esa semana.
- El umbral que las calla es el de MIROVA (`max(μ + 5σ, 0,003)` en dNTI y dETI de la caja sensible,
  `pipeline/mirova_v750_codigo.py`), no uno nuestro. Un clon fiel no las ve porque MIROVA tampoco. Verlas es trabajo de
  `experimental` (más allá de MIROVA), validado contra OVDAS y SWIR (A115), no contra MIROVA.
