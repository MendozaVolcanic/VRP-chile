# S161: mapa satelital y persistencia de focos térmicos (Tupungatito, Cordón Caulle, Isluga)

Pedido de Nicolás (2026-10-22): ver sobre imagen satelital dónde está el calor que alerta MIROVA, dónde publicamos
nosotros y cuán persistente es cada foco mes a mes, separando noche y día, antes de decidir si se pre-registra un
cambio de radio. **Este trabajo sólo mide y muestra: no decide ni cambia ningún parámetro.** Base: auditoría espacial
S160 y su verificador (`experiments/_s160_espacial/verificador/INFORME.md`, rama `loop/activo`, commit `98e52517b`).

- Artifact: https://claude.ai/artifact/WmDZh2Wqb8EqTn4gbwDDZb (privado hasta que se comparta).
- Página local (abre en el navegador, con los mosaicos al lado):
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\gracious-merkle-6447d8\experiments\_s161_mapa_persistencia\artefacto\mapa_persistencia.html`
  (la carpeta `artefacto/` no se commitea: la regeneran `04_` y `05_`).

## El fenómeno, antes que el código

Un foco térmico real (cráter con fumarolas o un domo tibio) se ve como un píxel más caliente que su entorno en muchas
noches seguidas, siempre en el mismo lugar. De día el canal MIR (3,7 µm) suma luz solar reflejada: nubes, laderas
asoleadas y nieve también resaltan, así que una «fuente» que sólo aparece de día no es calor (A76; la del E de Cordón
Caulle en S160 eran 13 de 15 TIF diurnos de mayo, VE-08). Por eso noche y día se cuentan siempre por separado. Y un
punto tibio que aparece en muchas noches pero sobre todo cuando el cielo está despejado, también en pasadas en que
MIROVA no vio nada, apunta a terreno (valles más tibios que las cumbres nevadas, A69), no a un volcán.

## Instrumentos

| Script | Qué mide | Salida |
|---|---|---|
| `01_tif_persistencia.py` | En cada GeoTIFF VIIRS 375 de MIROVA (TIF menos su mediana de 9 × 9 px, en sigmas de la escena, como S139 y S160 02b): un foco está presente si hay 4 sigma o más a 1 km. Focos forzados de S160 más los descubiertos en el mapa de frecuencia. Nulo: 300 puntos al azar lejos de todo foco. Noche (sol a -6° o menos) y día (sol sobre el horizonte) aparte. | `01_tif_persistencia_salida.txt`, `01_tif_foco_por_tif.csv`, `01_tif_por_tif.csv`, `01_tif_persistencia.json`, `01_frecuencia_*.png` |
| `02_records_persistencia.py` | En nuestros records de producción (copia sólo lectura de `experiments/_s160_espacial/data/`, origin/main `db0dfe847`): pasadas con un píxel anómalo a 1 km o menos de cada foco, y cuántas veces el tablero publicó ahí (predicado de `frontend/index.html` con node, A97). Nulo igual. Etiquetas de MIROVA con `banco_paridad.etiquetar`, regla D-9 SN, ventana 2026-01-10 a 2026-10-22. | `02_records_persistencia_salida.txt`, `02_records_foco_mes.csv`, `02_capas_mapa.json` |
| `03_ve01_ve02_png.py` | VE-01 y VE-02 en los paneles «Latest Images» de MIROVA (no hay TIF después del 2026-09-22): georreferencia de la miniatura por correlación con TIF nocturnos despejados del mismo volcán, con nulo de otro volcán, y búsqueda del punto caliente. | `03_ve01_ve02_png_salida.txt`, `03_miniatura_*.png` |
| `04_construir_mapa.py` | Mosaicos Sentinel-2 cloudless 2016 (EOX, CC BY 4.0), datos del mapa y dos cifras de resumen. | `04_construir_mapa_salida.txt` |
| `05_armar_html.py` | Arma la página desde `artefacto_plantilla.html`. | `artefacto/mapa_persistencia.html` |

Controles: el predicado del tablero pasa su control de identidad (`02_…salida.txt` l. 1); la georreferencia de las
miniaturas se valida contra un nulo de otro volcán (`03_…salida.txt`); y el cráter de noche separa con fuerza las
imágenes con alerta de MIROVA de las RUTINA (abajo), que es la prueba de que el instrumento ve calor y no sólo textura.

## Resultados

Ventanas: TIF de MIROVA del 2026-05-09 al 2026-09-20 (201, 231 y 191 TIF nocturnos; 50, 54 y 35 diurnos;
`01_…salida.txt` l. 3, 26 y 55); records nocturnos del 2025-02-15 al 2026-10-22 (6.434, 7.185 y 5.576;
`02_…salida.txt`). El archivo de TIF no tiene más que eso: «todo el año» sólo vale para nuestros records.

**1. El cráter es el único foco que persiste, en los dos instrumentos y en los tres volcanes.**

| Volcán | TIF noche, cráter presente | con alerta de MIROVA | en RUTINA | azar | Fuente |
|---|---|---|---|---|---|
| Tupungatito | 45 de 201 (22 %) | 37 de 57 (65 %) | 3 de 123 (2 %) | 0,7 % | `01_…salida.txt` l. 81, 83, 97 |
| Cordón Caulle | 96 de 230 (42 %) | 73 de 84 (87 %) | 20 de 137 (15 %) | 1,8 % | l. 131, 133, 147 |
| Isluga | 74 de 191 (39 %) | 64 de 82 (78 %) | 3 de 86 (3 %) | 0,5 % | l. 181, 183, 193 |

Nuestros records ven el cráter en los 21 meses de los tres volcanes (fila `crater` de cada bloque «todos los
sensores» en `02_…salida.txt`). Mes a mes, la tasa del cráter en los TIF y en nuestros VIIRS 375 sube y baja junta en
Tupungatito (Spearman 0,97 en 5 meses) y Cordón Caulle (0,87); en Isluga da 0,30 porque la tasa casi no cambia (36 a
43 % en los TIF), así que no hay variación que seguir (`04_…salida.txt`, sección 2a). En Tupungatito los dos
instrumentos bajan en el invierno de 2026.

**2. Los otros focos recurrentes de noche no son calor volcánico visible para nuestro detector.** Los descubiertos en
la frecuencia de los TIF (por ejemplo n1 a n5 de Tupungatito, 10 a 18 km al W) aparecen en 11 a 36 % de los TIF
nocturnos, también en pasadas RUTINA (n1: 35 de 122), y en nuestros records 0 o 1 vez por mes
(`01_…salida.txt` l. 86 a 90 y 100 a 104; `02_…salida.txt`, bloque de Tupungatito). Que sean terreno tibio de los valles es
SOSPECHA: aparecen más en noches con alerta (n1: 29 de 57) que en RUTINA, lo que cuadra con noches despejadas, pero no
miré la nubosidad. El foco a 5,7 km al N de Isluga es el más cercano a señal (con alerta 24 de 82, RUTINA 10 de 85,
l. 194) y nuestro detector lo marca en 3 pasadas de 21 meses.

**3. La fuente del E de Cordón Caulle es diurna y de mayo.** De noche 8 de 230 TIF (3 %); de día 19 de 54 (35 %), y las
19 en mayo (`01_…salida.txt` l. 134 y 165). Confirma VE-08 del verificador S160.

**4. Lo que publicamos lejos del cráter en noches limpias de Cordón Caulle no es un foco que vuelva.** De 107 cúmulos
publicados en negativos limpios, 38 están a 2 km o menos del cráter y 69 más lejos (57 entre 10 y 20 km); de esos 69,
sólo 19 tienen otro publicado a 1 km o menos. En pasadas con alerta, 303 de 309 están a 2 km o menos del cráter. En
Tupungatito e Isluga los publicados lejos en noches limpias son 4 y 2 (`04_…salida.txt`, sección 2b). Esto es lo que
un cambio de radio tocaría; aquí sólo se describe.

**5. VE-01 (Tupungatito, 2026-09-29 04:54, protegida de 1,86 MW): CONFIRMADO.** El panel «Latest Images» de MIROVA
capturado a las 12:28 UTC muestra esa pasada con VRP 1,86 MW y marco verde. La miniatura se georreferencia bien (r 0,711
con un TIF nocturno del mismo volcán, desplazamiento de 1 px; nulo de otro volcán r 0,091). Su punto más brillante (z
21,3) está a 0,02 km de nuestro píxel (302 K, 1,11 MW), a 9,40 km al E del cráter; el cráter también se ve, débil (z
10,5, a 0,30 km). La fuente cae en el anillo de MIROVA (fila 24, columna 42, el borde E); el cráter de Tupungatito
también cae en el anillo (fila 27), no en la caja de cumbre. Nuestro radio interno de 7 km la deja fuera, por eso
el record es `far` y no se publica. **No es persistente**: aparece en nuestros records sólo el 2026-08-23 06:30 (277
K, 0,24 MW) y esa noche, y en 0 de 200 TIF nocturnos de mayo a septiembre. Qué es la fuente: SIN DATO. (Todo en
`03_…salida.txt`; el 0 de 200 en `01_…salida.txt` l. 85.) El panel de las 08:49 UTC (`data/png/Tupungatito/20260929_084950_VIIRS375_Latest10NTI.png`
del archivo) todavía no traía esa pasada y el de las 12:28 sí: MIROVA la procesó tarde (observado en las dos imágenes).
Las miniaturas usadas quedan en `03_miniatura_VE01_*`.

**6. VE-02 (Cordón Caulle, 2026-10-21 05:48): SIN DATO en la imagen de MIROVA, y una SOSPECHA nueva.** La escena está
nublada: la miniatura no se georreferencia (r 0,147 contra un nulo de 0,094) y el detector de puntos marca 84 máximos
en la de VIIRS 750 y 68 en la de VIIRS 375, así que no ubica nada (`03_…salida.txt`). El propio panel de MIROVA
muestra la pasada con «VRP = 0 MW» y aviso «Thermal anomaly: VERY LOW» (leído en la imagen de las 08:37), mientras la
tabla de MIROVA trae 0,36 MW a 6,45 km. Nuestros 11 píxeles de VIIRS 750 tienen 263 a 273 K sobre un fondo de 259 K,
entre 9,6 y 11,9 km del cráter. SOSPECHA: contraste en un claro entre nubes más que calor. Esto matiza el «calor real
lejos del cráter» del verificador S160 (VE-02), que sigue en pie en la posición pero no en la naturaleza.

## Límites

- Los TIF cubren sólo de mayo a septiembre de 2026 y los diurnos casi no existen de junio a agosto (1 a 4 por mes).
- Hay 23, 27 y 24 TIF `_lm` sin hora confiable que se excluyeron (`01_…salida.txt` l. 2, 25, 54).
- Los focos descubiertos dependen de los cortes declarados en `01_` (4 sigma, 1 km, frecuencia 3 veces la mediana y 5
  TIF o más). No se probaron otros cortes.
- El fondo satelital es de 2016 (Sentinel-2, 10 m): sirve para ubicar, no para ver cambios recientes.
- No se miró la nubosidad de cada TIF; las lecturas sobre terreno y nubes quedan como SOSPECHA.

## Cómo regenerarlo

```bash
python -I 01_tif_persistencia.py > 01_tif_persistencia_salida.txt
python -I 02_records_persistencia.py > 02_records_persistencia_salida.txt
python -I 03_ve01_ve02_png.py > 03_ve01_ve02_png_salida.txt
python -I 04_construir_mapa.py > 04_construir_mapa_salida.txt
python -I 05_armar_html.py
```

Los CSV por TIF y por mes (`01_tif_foco_por_tif.csv`, `01_tif_por_tif.csv`, `02_records_foco_mes.csv`) no se
commitean porque el `.gitignore` del repo excluye los CSV de `experiments/`; los regeneran `01_` y `02_`, y cada cifra
del README sale además de una salida `.txt` commiteada. Leen los TIF del disco (`mirova-tif-archive` y las bajadas de S139 a S147) y los datos de S160 sin modificarlos; las
PNG de MIROVA y las teselas se bajan una por una a la carpeta temporal, sin pull ni clone.
