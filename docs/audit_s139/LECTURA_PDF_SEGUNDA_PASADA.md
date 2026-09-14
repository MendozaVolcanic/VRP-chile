# Segunda pasada de lectura de papers del grupo MIROVA (Fase 0, tarea 10), S141

Sesión S141, 2026-09-14. Salida que pide el plan
`docs/superpowers/plans/2026-09-14-fase0-instrumento-paridad.md` (tarea 10). **Sin cambios de código
del pipeline.** Los informes completos, con cada cita textual, viven en `docs/audit_s141/lectura/`:

| informe | qué cubre |
|---|---|
| `LECTOR_A.md` | Coppola 2020 (Front. Earth Sci. 7:362), Campus 2022 (Sensors 22, 1713), Aveni 2023 FY-3D MERSI-II (Remote Sens. 15, 2528) |
| `LECTOR_B.md` | Fernandina 2025 entero (Remote Sens. 17, 1191), Coppola 2023 entero (Front. Earth Sci. 11:1240107), `rs11131528.pdf` (resultó ser MOUNTS, no MIROVA), planillas Coppola 2019 |
| `LECTOR_C.md` | Massimetti 2020 (resultó ser Sentinel-2 contra MIROVA MODIS, no validación VIIRS), Aveni 2024 TIRVolcH (RSE 315), Aveni 2025 GRL, Aveni 2025 Remote Sens. 17, 2543 |
| `LECTOR_D.md` | 11 casos de estudio (Coppola 2013, 2016 Vanuatu, 2021 Klyuchevskoy; Laiolo 2017, 2026; Campus 2024; Morelli, Campion, Galetto, Piton 2010) |
| `VERIFICADOR_LECTORES.md` | verificación con contexto limpio de todo hallazgo de gravedad 3 o más: **19 fusionados (4 confirmados, 12 con matiz, 2 mixtos, 1 refutado) y 7 propios** |
| `LOCALIZADOR_MANUSCRITO.md` | las 73 afirmaciones de literatura del manuscrito `docs/paper/`, con paper, página y párrafo (pedido de Nicolás, S141) |

**Método.** Toda cita se leyó en la página del PDF renderizada a imagen (PyMuPDF, 150 a 200 dpi),
nunca en la capa de texto ni en los `.txt` (A95). Los PNG quedaron fuera del repo (derechos de
autor, repo público). Cada hallazgo lleva localizador comprobable a mano: PDF, página, sección y
párrafo, o figura, tabla o ecuación.

## Lo que cambia, ya verificado

| ID | tema | veredicto | localizador principal | dónde quedó |
|---|---|---|---|---|
| V-07, P-02 | **Fondo del VRP**: media de los vecinos del píxel alertado, **por píxel**, y el fondo total es la suma. Nunca mediana ni anillo | confirmado con matiz, gravedad 4 | Campus 2024 (Bull. Volcanol. 86:25) p. 3, bajo ec. 1 y ec. 2; Coppola 2023 p. 3 ec. 1 y p. 6 Tabla 1; cinco textos más | D25 del catálogo: segunda divergencia dentro de D25 (un único `t_bg` para todo el cúmulo) |
| V-05 | **Bow tie**: los duplicados se identifican y eliminan en el gránulo original, antes de remuestrear | confirmado con matiz, gravedad 4 | Coppola 2013 (JVGR 249) p. 46 Apéndice 2; Coppola 2023 p. 3 §2.1; Aveni 2023 p. 8 §3.2 | D28 |
| V-08 | **Ángulo cenital**: el grupo descarta pasadas oblicuas en sus análisis (40° o 50°), el NRT no filtra, y el remuestreo corrige el cenit sólo «partially» | confirmado con matiz, gravedad 4 | Massimetti 2020 p. 15 §3.2; Aveni 2024 p. 14 Tabla 2 y p. 20 §7.3; Campus 2022 p. 8 §3.4; Campus 2024 p. 4 | D17: toda magnitud contra MIROVA se reporta también con cenit ≤ 40° |
| V-13, P-04 | **Grilla**: 51 × 51 celdas de 1 km (MODIS), 67 × 67 de 750 m (M-band), 134 × 134 de 375 m (I-band); «50 km» y «51 km» son la misma | confirmado, gravedad 3 | Coppola 2023 p. 3; Campus 2022 p. 7 §3.2; Aveni 2024 p. 5 §3.2 | D17 |
| V-06, V-02, V-10 | **ROI de cumbre** caja 5 × 5 km con umbrales más altos afuera «which reduce false alerts»; web 2020 separa a 5 km fijos; radios de conteo de 0,75 a 7 km en estudios | confirmado con matiz, gravedad 3 | Coppola 2023 p. 3 §2.1; Coppola 2020 p. 4; Campus 2024 p. 5; Aveni 2024 Tabla 2 | D18 |
| V-15 | **Banda TIR MODIS**: el grupo escribe 12,02 µm (banda 32) en 2020 y 2023 y banda 31 en 2025 | confirmado, gravedad 2 | Coppola 2020 p. 3; Coppola 2023 p. 3 | D20 (corrige la nota S140) |
| P-01 | El catálogo generalizaba al NRT el filtro por distancia e intensidad de una serie de estudio de Stromboli | hallazgo propio del verificador, gravedad 3 | Laiolo 2026 (Bull. Volcanol. 88:11) p. 4, 2.º párrafo | D14 (nota de advertencia) |
| V-11 | **Supervisión**: la base supervisada a mano es la **v.1** (MODIS nocturno 2000-2019); el NRT se publica «as-are» | confirmado con matiz, gravedad 3 | Coppola 2023 p. 4 §2.5; Campus 2022 p. 8 §3.4 | refuerza `feedback_s135_techo_artificial_supervision` y la regla S139 sobre el OSF |
| V-12 | **Tasa de falsas alertas aceptada por el grupo**: 0 a 3 % de las pasadas MODIS totales | confirmado con matiz, gravedad 3 | Coppola 2020 p. 13 «Tinakula»; Coppola 2016 (JVGR 322) p. 10 §4.6 | para el auto-audit: expresar también falsas por pasadas totales, no sólo por negativos limpios |
| V-14 | En volcanes de bajo flujo MIROVA publica bastante más con VIIRS 750 que con MODIS (62 % más alertas en total) | confirmado con matiz, gravedad 3 | Campus 2022 p. 16 §5 y Tabla 4 p. 17 | paridad de cobertura: no comparar contra referencia de otro sensor |
| V-16 | Dos páginas mal citadas en el repo | confirmado | Aveni 2024 p. 11 ec. 5; Aveni 2025 GRL p. 5 Fig. 2 | corregidas en `docs/DRIFTS_S17.md:83` y `pipeline/vrptir.py:10` (comentario) |
| V-04, V-06 | Tres errores de la síntesis bibliográfica | confirmado | Campus 2022 p. 7 ec. 1; Coppola 2020 p. 3; Coppola 2023 p. 3 | corregidos en `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` (archivo local, fuera de git) |
| V-19 | «El repo no cita el filtro de Laiolo 2026» | **REFUTADO** (el grep del lector daba cero en falso, A89) | `docs/MIROVA_DIVERGENCES.md` sección D14 S128 | sin cambio |

## Lo que no se encontró en ninguna página leída

- K1, C1, C2, N·σ o la conectiva de los Tests 2 y 3: todos los papers remiten a Coppola 2016a.
- Un recorte a cero del exceso negativo de radiancia.
- Un filtro automático por ángulo cenital en el canal NRT.
- Umbrales propios de VIIRS: Campus 2022 p. 7 dice que el detector es «the same used for MODIS» con pasos «slightly modified», sin valores.

## Preguntas del correo a Coppola que estas lecturas afectan (NO se editó el borrador; Nicolás lo excluyó en S141)

Propuestas del verificador, para cuando se retome el correo:

- **Pregunta 4 (fondo)**: la mitad «8 vecinos o anillo» está contestada por siete textos; queda «¿se recorta a cero el exceso negativo?» y el tamaño exacto de la vecindad.
- **Pregunta 6 (bow tie y remuestreo)**: contestada en lo esencial; queda «¿qué método exacto de bow tie?» y «¿caja o disco para la cumbre?».
- **Pregunta 8 (filtros del archivo)**: citar Laiolo 2026 p. 4 y preguntar si el filtro por distancia, intensidad y doble conteo se aplica también al NRT y al CSV `latest`.
- **Pregunta 11 (distancia)**: Coppola 2020 p. 4 la define como distancia al píxel caliente más lejano; preguntar si sigue siendo ese el campo publicado.
- **Nueva**: ¿se cambiaron los umbrales de la Tabla 1 de 2016a para VIIRS M-band e I-band? (Campus 2022 p. 7, «slightly modified»).

## Lo que queda fuera o sin verificar

- Tesis de Massimetti (tema Sentinel-2 y Landsat 8, excluida por el plan).
- Hallazgos de gravedad menor que 3 que el verificador no revisó (listados en su sección «No verificado por mí»).
- La identidad de la ref. [82] de Aveni 2023 (Liu et al. 2008) se tomó de la capa de texto: SOSPECHA.
- Las tablas de bandas de Campus 2022 p. 6 y Aveni 2023 p. 6 no se miraron en imagen.
