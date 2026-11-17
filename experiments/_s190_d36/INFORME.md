# D36: costo de las decisiones de la vía que no vienen de MIROVA (S190, 2026-11-17)

Worktree `D:\vrp-trabajo\worktrees\s190-d36`, rama `s190-d36` desde main `13af35186`. Todo número sale de un
script de esta carpeta con su salida al lado. Ventana de referencia: desde el 2026-03-01 (la tabla de MIROVA es
comparable desde marzo, A119) hasta el último record de main (2026-11-16 08:10 UTC en MODIS). Nada de producción
cambió.

## Resumen

| Punto | Qué se midió | Veredicto |
|---|---|---|
| 1. Umbrales de MODIS (K1 -0,7 y piso 0,02 del `.m` de VIIRS 750 en vez de -0,8 y 0,01 de la Tabla 1) | A/B sobre 330 pasadas reales con la grilla de la vía | **Pre-registrado: «medir más»** (la Tabla 1 cambia el valor publicado en 5,8 % de las pasadas con alerta; el corte para «dejar documentado» era 2 %). **Recomendación posterior: no adoptar la Tabla 1 y dejarlo documentado**: no recupera ninguna alerta, no cambia ninguna protegida, y en las 9 pasadas que cambian (todas Chillán) sube un valor que ya estaba sobre el de MIROVA |
| 2. Escalón de cenit de VIIRS 750 sobre 50° | Razón nuestra/MIROVA en la misma pasada sobre 50°, por magnitud | **No implementar (3 preguntas: NO) y medir más.** La razón es 0,998, pero la prueba no tiene poder: en el OSF el escalón casi sólo actúa sobre 100 MW, y no tenemos ningún par sobre 50° con 100 MW o más desde que corre la vía. Se mide en el primer evento oblicuo grande |
| 3. Corte de 5 km al centro, mínimo de 100 píxeles, recorte de 45 km | Mutaciones contra las pruebas de hoy; costo contra MIROVA | **Dejar documentado.** Costo contra MIROVA: 0 alertas perdidas atribuibles. Pruebas: quitar o subir el corte de 5 km y mover el recorte de 45 km se atrapan; bajar el corte, el mínimo de 100 píxeles y el radio de cobertura no los atrapa ninguna prueba (ver §3) |

## 1. Umbrales nocturnos de MODIS

**El fenómeno.** De noche, un píxel con lava o un domo caliente emite mucho más en el infrarrojo medio que en el
térmico, y el índice NTI sube. El detector alerta por dos caminos: un NTI absoluto alto (Test 1, umbral K1) o un
contraste contra sus vecinos mayor que un umbral que se calcula con la escena (media más n veces la desviación),
con un piso fijo. La vía usa en MODIS los números del código de VIIRS 750 (K1 -0,7; piso fuera de la cumbre 0,02),
mientras que la Tabla 1 de Coppola et al. 2016a para MODIS dice K1 -0,8 y piso 0,01 fuera de la cumbre (0,003 en la
cumbre, igual en los dos). Lo verifiqué en el PDF renderizado (`documentacion/sp426.5.pdf`, p. 7; la capa de texto
está rota, A95): noche ROI1 -0,8 / 0,003 / 5; ROI2 -0,8 / 0,01 / 10.

**Lo que dicen los records sin bajar nada (A2)** (`p1_exposicion.py`, salida `p1_exposicion_salida.txt`; records
nocturnos de la vía MODIS de los 11 Tier A desde el 2026-03-01):
- el piso de 0,02 decide el umbral fuera de la cumbre en 5.872 de 6.006 escenas con diagnóstico (pase 1): la Tabla 1
  bajaría ese umbral en casi todas;
- 0 de 6.006 escenas tienen alertas por el Test 1 absoluto (`n_abs` > 0): K1 no actúa hoy en MODIS;
- de 156 pasadas con alerta, 143 tienen todas sus celdas en la cumbre sensible (5 × 5 km), donde el piso de 0,02 no
  se aplica; 19 de 544 celdas alertadas están fuera de la cumbre.

Esto acota la exposición pero no dice cuántas celdas nuevas aparecerían: eso pide los gránulos.

**El A/B.** Pre-registro escrito antes de despachar (`PREREGISTRO_P1.md`); pasadas elegidas antes de mirar
(`p1_seleccion.py`, semilla 190, `p1_pasadas.json`): 338 pasadas nocturnas MODIS de los 11 Tier A, en cuatro
estratos (135 a ±60 min de una alerta MODIS de MIROVA, 156 con alerta nuestra, 165 negativas al azar, 15 por
volcán, y 12 que la vía descartó y la guardia K procesó). Brazos (`brazos.py`): A = la vía; B = los números de la
Tabla 1 con la lógica del `.m` (umbral = max(μ + C2σ, C1); la p. 7 del paper lo escribe «dNTI > C1 or dNTI >
μ + C2σ», que es lo mismo); B1 = sólo K1; B2 = sólo el piso. Corrió en Actions (run 44016042341, rama desechable ya borrada, sólo lectura; arnés
`p1_runner.py`) porque el token de Earthdata existe sólo como secreto. Lectura: `p1_analisis.py`, salida
`p1_analisis_salida.txt` y `.json`.

Controles:
- copia de `detectar_mirova` con los números de la vía = módulo de producción en 330 de 330 pasadas, y en 40 de 40
  escenas sintéticas (`probar_local.py`, verde en los tres jobs);
- el instrumento puede dar distinto de cero: en escenas sintéticas, B2 alerta una celda tibia fuera de la cumbre que
  A no alerta, y B1 una con NTI -0,75 que A no alerta;
- la vía en el runner = record guardado en producción en 318 de 318 pasadas con record;
- 8 de 338 pasadas no se procesaron por fallas del buscador CMR de la NASA (5 timeouts, 2 errores 502 y 1 «Internal
  Error»); 5 de ellas tenían alerta protegida de MIROVA, consolidada (23,73; 2,72; 2,22; 3,79 y 4,75 MW). Por eso los
  tres jobs del run terminan en «failure»: el arnés sale con 1 si falta alguna pasada (`p1_runner.py`, final de
  `main`), a propósito.

Resultados (330 pasadas procesadas):

| Métrica | A (vía) | B (Tabla 1) | B1 | B2 |
|---|---|---|---|---|
| M1 noches con alerta protegida de MIROVA (>= 1 MW) acertadas | 62 de 62 | 62 de 62 | 62 de 62 | 62 de 62 |
| M1 todas las alertas MODIS de MIROVA, por noche | 93 de 96 | 93 de 96 | 93 de 96 | 93 de 96 |
| M2 razón nuestra/MIROVA, misma pasada, consolidado (n 124): mediana | 1,013 | 1,027 | 1,013 | 1,027 |
| M2 mediana de \|log razón\| | 0,130 | 0,134 | 0,130 | 0,134 |
| M3 negativas con valor publicado (de 162) | 0 | 0 | 0 | 0 |
| M4 pasadas con valor publicado distinto de A (de 330) | | 9 | 2 | 8 |
| M4 suma de \|Δ publicado\| (sobre 936,2 MW publicados por A) | | 23,5 MW | 3,2 MW | 21,7 MW |

Las 9 pasadas que cambian son todas de Nevados de Chillán; en ninguna B publica desde cero ni deja de publicar;
siempre suma potencia (más celdas alrededor del domo). B cambia el número de celdas en 16 pasadas: 11 de Chillán y
5 de otros volcanes (Isluga 2, Láscar, Planchón-Peteroa, Llaima), donde el valor publicado no cambia porque lo que
crece es un cúmulo lejano que ya existía (Planchón de 1 a 6 celdas, Llaima de 1 a 5). B suma 1 sola alerta lejana
nueva, que no se publica, y es la misma pasada negativa que pasa a tener una celda alertada (Chillán 2026-05-31
07:35). Por volcán (M2, consolidado): Láscar 0,999 en los dos brazos (n 78); Chillán 1,034 con A y 1,051 con
B, \|log\| 0,108 contra 0,145 (n 46).

**Lectura con la regla pre-registrada.** Adoptar B pedía acertar al menos una protegida más: no acierta ninguna más.
«Dejar documentado» pedía que B cambiara menos del 2 % de las pasadas de los estratos `mirova` y `nuestra`: cambia 9
de 156 (5,8 %). «Mantener A» pedía que B perdiera una protegida o sobre-publicara: no pasa. Queda en «medir más».

**Desglose posterior (no estaba en el pre-registro; lo marco como tal).** Las 9 pasadas que cambian tienen todas
valor de MIROVA en la misma pasada, fuente consolidado (`cambios_con_mirova_misma_pasada` en el JSON). En las 9, B
queda más lejos de MIROVA que A. Ese 9 de 9 es casi mecánico y no es evidencia fuerte: B sólo puede sumar celdas, y A
ya estaba sobre MIROVA en 8 de las 9, así que cualquier suma aleja. La única pasada que informa es Chillán 2026-11-09
00:55 (MIROVA 6,37 MW, A 6,25, B 9,41), donde A estaba bajo MIROVA y B se pasa de largo. Ejemplo del caso típico:
Chillán 2026-10-30 08:55, cenit 63°, MIROVA 14,39 MW, A 20,55, B 28,60. Lo que sí se sostiene: la Tabla 1 no
recupera ninguna alerta, no cambia ninguna protegida y no mejora la magnitud en ninguno de los dos volcanes con pares (Láscar igual, Chillán
peor). El veredicto que
recomiendo es **no adoptar la Tabla 1 y dejarlo documentado**: la divergencia con el paper existe, pero acercarse al
paper no nos acerca a lo que MIROVA publica, que es la referencia del perfil `mirova_equivalent` (A115).

**Qué faltaría para cerrar del todo** (si Nicolás quiere el «medir más» literal): las 8 pasadas que fallaron por
la NASA (4 noches de Chillán, Láscar y Villarrica con alerta) y, para la sobre-publicación, una muestra de negativas
mayor (con 162, una tasa de 1 % no se distingue de 0). Ninguna de las dos puede cambiar el sentido de M2.

## 2. Escalón de cenit en VIIRS 750

**El fenómeno.** Cuando el satélite mira de lado (cenit alto), el píxel cubre más suelo y la atmósfera es más
gruesa. En el archivo OSF v2.5, MIROVA publica sobre 50° de cenit cerca de la mitad (mediana 0,51) del VRP que da su
propio código en el 24,1 % de las filas con cenit sobre 50° (8.239 de 34.250), y nunca bajo 50°
(`experiments/_s158_audit/f6/INFORME.md`). La vía corre el código sin ese escalón.

**Medición** (`punto2_escalon_cenit.py`, salida `punto2_escalon_cenit_salida.txt` y `.json`; con toda la ventana
de la vía desde el 2025-02-15, `punto2_escalon_cenit_desde_20250215_salida.txt`): alertas nocturnas de MIROVA,
fuente consolidado, contra nuestra pasada del mismo sensor a 10 min o menos (A109), valor publicado con la regla del
tablero. Como la vía corre el código, nuestro valor es el «VRP del código» que dispara el escalón; por eso los pares
se parten por nuestra magnitud.

| VIIRS 750, desde 2026-03-01 | Pares (con valor nuestro > 0) | Razón mediana (p25 a p75) | En 1,7 a 2,3 |
|---|---|---|---|
| cenit <= 50° | 309 (290) | 1,000 (0,984 a 1,012) | 3 |
| cenit > 50°, nuestro valor hasta 20 MW | (39) | 0,996 (0,967 a 1,000) | 0 |
| cenit > 50°, de 20 a 100 MW | (12) | 0,999 (0,992 a 1,005) | 0 |
| cenit > 50°, 100 MW o más | (0) | SIN DATO | |

Con toda la ventana de la vía (desde 2025-02-15) son 44 y 12 pares en los dos primeros tramos y otra vez 0 sobre
100 MW.

**Poder de la prueba** (lo encontró el verificador; `punto2_osf_por_tramo.py`, salida
`punto2_osf_por_tramo_salida.txt`, sobre `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, el OSF v2.5). En el
archivo de MIROVA, sobre 50°, el escalón actúa según la magnitud: en 2 de 12.048 filas hasta 20 MW, en 92 de 10.639
(0,9 %) entre 20 y 100 MW, en 4.095 de 7.452 (55 %) entre 100 y 500 MW y en 4.050 de 4.111 (98,5 %) sobre 500 MW.
Con nuestros 12 pares de 20 a 100 MW lo esperable, aunque MIROVA lo siguiera aplicando, es 0,1 par afectado: que no
veamos ninguno no dice nada. **Si el NRT de MIROVA mantiene el escalón es SIN DATO**: Chile no ha tenido desde
febrero de 2025 una pasada VIIRS 750 oblicua con 100 MW o más.

**Las 3 preguntas (`docs/MISSION.md`).** 1. ¿Está en los papers o en el código de MIROVA? No: no está en el `.m` ni
en los papers; sólo se ve en los datos del OSF v2.5. 2. ¿Cierra una divergencia documentada? No hay evidencia de
que hoy divergamos en este punto (SIN DATO para eventos grandes). 3. ¿Es alineación interna no metodológica? No. Las
tres son NO: **no implementar**. **Medir más**: el primer evento oblicuo grande (VIIRS 750, cenit > 50°, nuestro
valor de 100 MW o más) con valor de MIROVA en la misma pasada lo decide; si MIROVA publica cerca de la mitad, el
escalón sigue vivo en su NRT y nuestra magnitud quedaría al doble en esos casos. D36 lo mantiene como SOSPECHA.

## 3. Corte de 5 km al centro, mínimo de 100 píxeles y recorte de 45 km

**El fenómeno.** Si el volcán queda en el borde del gránulo, o fuera, la pasada no lo ve. La vía lo decide con tres
reglas propias (no están en el `.m` ni en el paper): descarta la pasada si el píxel más cercano al centro de la
grilla está a más de 5 km (VIIRS 375 y MODIS), si quedan menos de 100 píxeles a menos de 45 km, y sólo interpola
los píxeles a menos de 45 km.

**Costo contra MIROVA** (`p3_alertas_sin_pasada.py`, salida `p3_alertas_sin_pasada_salida.txt` y `.json`):
- de 2.197 alertas nocturnas de MIROVA (MODIS 134, VIIRS 375 1.649, VIIRS 750 414; 525 protegidas), 0 quedan sin
  una pasada nuestra de la vía del mismo sensor a ±60 min;
- con el criterio estricto de la misma pasada (10 min) quedan 15 (VIIRS 375 14, VIIRS 750 1; 3 protegidas), todas
  del 2026-03-10 al 2026-03-12 y a horas de Suomi NPP. En esas horas no hay ninguna pasada SNPP nuestra de ningún
  volcán a ±2 h, sólo NOAA-20 y NOAA-21. El verificador buscó en todos los perfiles de `data/` (`experimental`,
  `_s154_reproc_k_historico`, `historia_34`, `mirova_equivalent`): ninguno tiene un record SNPP del 03-10 al 03-12 y
  todos tienen el 03-09 y el 03-13. Y MIROVA tiene alertas consolidadas a horas que sólo calzan con SNPP (03-10 06:42
  Cordón Caulle y 06:36 Lastarria), así que el satélite sí adquirió: es un hueco en los gránulos SNPP que bajamos esas
  tres noches, común a todos los perfiles, y no el corte, que depende de la geometría de cada volcán. Si los gránulos
  SNPP de esas noches existen hoy en la NASA es SIN VERIFICAR (seguimiento aparte, fuera de D36);
- en el A/B de MODIS (§1), las 12 pasadas del estrato `borde` (la vía las descartó y la guardia K las procesó, desde
  el 2026-10-27) tienen el píxel más cercano al centro entre 6,9 y 19,9 km; corriendo la vía sin el corte de 5 km,
  ninguna da alerta. Una (Chillán 2026-10-29 02:00, otro gránulo del mismo paso del satélite) tiene a ±60 min una
  alerta de MIROVA de las 01:55 (16,61 MW), y nuestra pasada de las 01:55 la publica;
- en las 330 pasadas procesadas el mínimo de píxeles a 45 km fue 396: el mínimo de 100 no actuó en la muestra.

**¿Las pruebas lo vigilan?** (`p3_mutaciones.py`; fase 1 contra los 6 archivos que prueban la vía directamente,
salidas `p3_mutaciones_fase1a_salida.txt` y `p3_mutaciones_fase1b_salida.txt`; fase 2 con las sobrevivientes
contra los 16 archivos que importan la vía, `p3_mutaciones_fase2_salida.txt`). Controles: sin mutación «viva» y la
mutación de caída «caida», en las dos corridas de la fase 1.

| Mutación | Fase 1 (6 archivos) | Fase 2 (16 archivos) |
|---|---|---|
| MODIS sin corte de 5 km | atrapada | |
| MODIS corte a 10 km | atrapada | |
| MODIS corte a 2 km | viva | viva (457 casos) |
| VIIRS 375 sin corte de 5 km | atrapada (sólo por la prueba de constantes) | |
| VIIRS 375 corte a 10 km | atrapada (sólo por la prueba de constantes) | |
| corte de 5 km ignorado (`if False`) | atrapada | |
| mínimo de 100 a 1 | viva | viva (457 casos) |
| mínimo de 100 a 2000 | viva | viva (457 casos) |
| recorte de 45 a 30 km | atrapada | |
| recorte de 45 a 60 km | atrapada | |
| selección de 45 a 20 km (sólo el conteo de cobertura) | viva | viva (457 casos) |

Lo que ninguna prueba vigila: bajar el corte de 5 km (a 2 km descartaría pasadas que hoy se miden), el mínimo de
100 píxeles (ni a 1 ni a 2000) y el radio con que se cuenta la cobertura. Ninguno de los tres cuesta alertas hoy,
pero un cambio accidental pasaría la suite en verde. Seguimiento propuesto, fuera de este PR: una prueba con un
gránulo sintético en el borde (píxel más cercano a 3 km y a 7 km del centro, y con 99 y 101 píxeles en el recorte)
que fije el comportamiento.

El recorte de 45 a 30 km ya está vigilado (`test_remuestreo_es_el_del_probe_del_censo`); el verificador de S164
decía que no. En VIIRS 375 el corte lo vigila sólo una prueba que compara la constante con la del port, no una que
procese un gránulo.

## Qué cambia en el repo con este PR

- `docs/MIROVA_DIVERGENCES.md` D36: los puntos 1, 2, 3 y 6 de la tabla y el escalón de cenit llevan su cifra y su
  veredicto.
- `docs/FICHA_SDA_VRP_CHILE.md`: los literales (a), (b) y (e) de las diferencias con MIROVA dicen el costo medido;
  fila v1.36 del historial (numerada al mergear; el PR la abrió como v1.34). Sin cambio de lógica de detección.
- Nada en `pipeline/`, `data/` ni `frontend/`.

## Límites

- MODIS: sólo noche (la vía no tiene records diurnos en los 11 Tier A) y sólo los 11 Tier A.
- La referencia MODIS incluye OCR para M1; M2 usa sólo consolidado.
- El A/B usó el código de main `13af35186` del 2026-11-17; los records guardados los escribió el mismo código en 318
  de 318 casos comparables.
- Hallazgo de paso: MODIS se puede leer en Windows con el entorno conda `vrp`
  (`C:\Users\nmend\miniconda3\envs\vrp`) poniendo su `Library\bin` en el PATH; sin eso sale con código 127 sin
  mensaje. El CLAUDE.md dice que pyhdf no funciona en Windows. Igual hace falta Actions para bajar gránulos, porque
  el token de Earthdata vive sólo como secreto.

## Verificación

Un verificador con contexto limpio (subagente, esfuerzo alto, sin ver mi razonamiento) revisó unas 118 de unas 125
afirmaciones numéricas, reprodujo las salidas de los cuatro scripts livianos (idénticas), comparó `detectar_param`
con `detectar_mirova` de `13af35186` (iguales salvo los dos números) y miró la Tabla 1 renderizada. Encontró tres
errores, ya corregidos en este informe: el punto 2 no tenía poder (se agregó el análisis por magnitud y el veredicto
pasó a «medir más»), la columna «con escalón» bajo 50° aplicaba el factor donde nunca actúa, y el hueco SNPP de
marzo era de nuestros gránulos y no del satélite. También corregí sus sospechas: el «1 en 512» no era una prueba
válida, el resumen ponía como veredicto la recomendación posterior en vez del desenlace pre-registrado, y el brazo B
mantiene la lógica del `.m`. Fuera de su revisión quedaron la tabla de mutaciones (corría en ese momento) y la fecha
del último record MODIS.
