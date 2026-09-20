# Frente C (S146): los cierres que se apoyan en un paper

> Auditoría de sólo lectura, 2026-09-20. No se modificó ningún archivo existente del repo. Archivos
> creados: este informe, `experiments/_s146_auditoria/frente_C/render.py`,
> `experiments/_s146_auditoria/frente_C/localizar.py` y 17 PNG de respaldo en
> `experiments/_s146_auditoria/frente_C/png/` (4,2 MB). El resto de las páginas renderizadas se borró.
>
> **Método.** Cada cita se localizó con la capa de texto (`localizar.py`, que sólo sirve para saber
> qué página abrir) y se validó mirando la página renderizada a imagen con PyMuPDF
> (`render.py`, 110 a 200 dpi). Un veredicto CITA CORRECTA significa que vi la página. Lo que sólo
> se leyó en capa de texto queda marcado SOSPECHA. Numeración de páginas: la del PDF (visor), salvo
> que se diga "impresa".
>
> **Las dos preguntas del instrumento.** (1) Si lo que mido estuviera roto, ¿fallaría la prueba?
> Sí: la página renderizada mostraría otro texto u otro operador, y eso fue lo que pasó en C-05,
> C-07 y C-09. (2) Si el instrumento estuviera muerto, ¿se vería distinto? Sí: sin PNG no hay
> veredicto, y `localizar.py` con cero páginas se reporta SIN LOCALIZAR, nunca OK. Control de
> método: las citas de D21 (p. 3) y D22 (p. 7), ya reconocidas, salieron correctas al renderizar.

## 1. Cobertura (primero)

| conjunto | identificados | cotejados contra imagen | no cotejados | por qué no |
|---|---|---|---|---|
| Censo S145: cierres que citan paper o son de tipo `es_fiel` | 25 | 21 | 4 | `MIROVA_DIVERGENCES.md:224` es una nota de numeración, no una afirmación; `HYPOTHESIS_LOG.md:472` y `CLAUDE.md:1160` no afirman nada sobre un paper (el censo los marcó por la palabra); `MIROVA_DIVERGENCES.md:2088` ("fiel al paper en sus valores") se cubre con la Tabla 1 y queda contado como cotejado indirecto en la fila 8 |
| `CLAUDE.md`, "Reglas científicas" y reglas A con cita de página | 14 | 14 | 0 | |
| Encabezados D de `MIROVA_DIVERGENCES.md` que citan página o afirman fidelidad | 16 | 14 | 2 | D17 y D18 traen baterías de citas S141 (Massimetti 2020, Coppola 2013 JVGR, Coppola 2020 p. 3 y 4, Aveni 2024 p. 5, 14 y 20) que ya fueron verificadas con página renderizada en `docs/audit_s141/lectura/VERIFICADOR_LECTORES.md`; re-verifiqué 4 de ellas como muestra (todas bien) y no el resto por costo |
| Bloque bibliográfico de D9 (S71) y tabla de "refutaciones bibliográficas" | 12 | 10 | 2 | "Coppola 2016b enhanced" no se pudo identificar como documento; "Tabla 3 lista 19 sistemas NRT" del capítulo Springer no se abrió |
| **Total** | **67** | **59** | **8** | |

Salvedad sobre esta tabla: el total (67 identificadas, 59 cotejadas, 8 no) es exacto y corresponde
a las filas de la sección 2 más las 8 listadas en la columna "por qué no". El reparto por conjunto
es aproximado, porque varias afirmaciones aparecen a la vez en el censo, en `CLAUDE.md` y en el
catálogo, y las agrupé en una sola fila.

Crecimiento respecto del censo: el censo daba 25 cierres con paper; leyendo las secciones pedidas
aparecieron 42 afirmaciones más que citan página, ecuación o tabla y que el patrón de palabras
clave no recoge (por ejemplo "Pasa las 3 preguntas de MISSION: Test 1 ES Coppola 2015 §2.2", que
no contiene ninguna palabra de cierre y es el hallazgo más grave de este frente).

Conteo por veredicto principal sobre las 59 filas cotejadas: **CITA CORRECTA 40, CITA CORRUPTA 8,
EL PAPER NO LO SOSTIENE 8, SIN LOCALIZAR 2 (más una parte de la fila 14), SOSPECHA 1** (fila 38,
sólo capa de texto). De las 18 filas que caen, 2 ya estaban reconocidas por el proyecto (fila 7:
"detección MODIS fiel" con D21 y D22; fila 6: GAP #A) y no se cuentan como hallazgos nuevos; en la
fila 6 lo nuevo es sólo que el texto viejo sigue sin marca.

Papers abiertos y vistos en imagen: Coppola 2016a (`sp426.5.pdf`, p. 3 a 9, 16, 17, 21), Wright
2002 (p. 7, impresa 141), Wooster 2003 (p. 6, impresa 88), Coppola 2025 cap. 11 del libro Springer
(`978-3-031-86841-2.pdf`, p. 335, 340, 341; impresas 331, 336, 337), Aveni 2024 RSE (p. 11), Aveni
2025 GRL (p. 4), Campus 2022 (p. 7 y 8), Campus 2024 (p. 3 y 4), Coppola 2023 Frontiers (p. 3 y
4), Coppola 2020 Frontiers (p. 15), Coppola 2026 Scientific Data (p. 7 y 8), Laiolo 2026 Bull.
Volcanol. 88:11 (p. 4), Coppola 2014 IJRS (p. 9, impresa 3409), Fernandina 2025 (p. 9), Laiolo
2017 (p. 5, recorte), Di Bella 2024 (p. 7, recorte), MODIS L1B User Guide C7 (p. 40), VIIRS L1B
User Guide (p. 40).

## 2. Tabla de veredictos

Gravedad 1 a 5 = cuánto trabajo futuro apaga el cierre si está mal. "Conf." = confianza en mi
veredicto.

| # | cierre (archivo:línea) | paper y localizador | qué afirma el cierre | qué dice la página | veredicto | conf. | grav. |
|---|---|---|---|---|---|---|---|
| 1 | `MIROVA_DIVERGENCES.md:677, 707, 740, 1203`; `pipeline/test1_integrated.py:12-18`; `pipeline/process_modis.py:16`; `docs/F62_TEST1_K_SIGMA_BRAINSTORM_S78.md:14-24` | "Coppola et al. 2015, Bull. Volcanol. 77:55, §2.2 Eq. 1" | el Test 1 integrado en el ROI (exceso de radiancia MIR sumado en 3 km, k = 3, piso relativo 0,02) "ES Coppola 2015 §2.2 Eq. 1, paper MIROVA core", y por eso pasa las 3 preguntas de MISSION | el PDF no está en `documentacion/`; S128 estableció que "Coppola 2015" es el mismo `sp426.5.pdf`, y ahí la Ec. 1 es el NTI (p. 4) y el Test 1 es `NTI_PIX > K1`, por píxel (p. 6). Ningún paper del grupo que abrí cita ese artículo: todos citan el algoritmo como "Coppola et al. 2016" | **SIN LOCALIZAR**, y contra `sp426.5`: **EL PAPER NO LO SOSTIENE** (C-01) | alta | **5** |
| 2 | `MIROVA_DIVERGENCES.md:259, 265, 287` | "Coppola 2016a, caso Gaua p. 17: <2 % FPs, siempre <5 MW" | respaldo del tope de 5 MW de D9 | "Gaua" no aparece en ninguna de las 25 páginas ni en `sp426_5.txt`; la p. 17 habla de falsas alertas en general | **SIN LOCALIZAR** (C-03) | alta | 3 |
| 3 | `MIROVA_DIVERGENCES.md:300-301, 327-333` | Coppola 2016a p. 16-17, "False alerts" | el tope de 5 MW "NO es un parche, es la implementación programática del trade-off documentado" | la cita existe (p. 17), pero la frase empieza en p. 16: las falsas alertas "principally occur on daytime images", en bordes de agua y nubes dispersas, y el remedio del paper es inspección visual. No hay tope de magnitud. Además el paper dice que las falsas son chicas (<5 MW); el tope actúa sobre registros inflados 20 a 150 veces, que es otro fenómeno | **EL PAPER NO LO SOSTIENE** (C-02) | alta | 3 |
| 4 | `CLAUDE.md:106-112` y `mirova_equivalent.yaml:128-134, 280-282` | Coppola 2016a Tabla 1, p. 7 | `enable_dual_roi_bt` aplica "N·σ = 5 summit / 10 scene (Coppola 2016a Tabla 1)" a la temperatura de brillo MIR | en la Tabla 1, C2 = 5 / 10 multiplica la desviación de **dNTI y dETI** (Tests 2 y 3). El paper no tiene ningún test sobre temperatura de brillo | **EL PAPER NO LO SOSTIENE** (C-04); emparentado con D22, pero es otro camino | alta | 3 |
| 5 | `CLAUDE.md:102-105`; `HYPOTHESIS_LOG.md:770-781` | Coppola 2025 cap. 11 Ec. 16 (p. 341, impresa 337); Aveni 2024 Ec. 5 (p. 11); Aveni 2025 Ec. 9 (p. 4) | "Drift D3 RESUELTO": el VRP TIR por Stefan-Boltzmann es lo que usa el grupo; la Ec. 9 es "investigación no adoptada" | Aveni 2024 Ec. 5 es Stefan-Boltzmann con emisividad 1: correcto. Pero la Ec. 16 del capítulo es la potencia del modelo de dos componentes (`A_hot σ ε (T_hot^4 − T_bk^4)`, exige suponer T_hot), la misma que el catálogo (l. 505) dice que el NRT no usa. Y Aveni 2025 (Fig. 1, p. 4) muestra que el enfoque de píxel puro subestima más de 90 %. Ningún paper dice cuál está "adoptado operacionalmente" | Ec. 5 **CORRECTA**; Ec. 16 **EL PAPER NO LO SOSTIENE**; "no adoptada" **SOSPECHA** (C-06) | media | 2 |
| 6 | `MIROVA_DIVERGENCES.md:455` | Coppola 2016a p. 6 y 7 | "`enable_test1_k1_retire_from_hot_mask` OFF permanentemente; el código actual ya es fiel" | la lectura S100 es buena (p. 7 usa la misma fórmula, "eliminated from further analysis", para los píxeles de los Tests 2 y 3, que sí se reportan). Pero el paper sí los saca del pool de μ y σ, y el código no (`test1_mask=None`), como ya registró S128 | lectura **CORRECTA**, cierre **EL PAPER NO LO SOSTIENE**; ya reconocido en l. 1319-1335 y en `CLAUDE.md`, pero la l. 455 sigue viva sin marca (C-08) | alta | 3 |
| 7 | `CLAUDE.md:112, 965`; `MIROVA_DIVERGENCES.md:1259, 1315`; `MISSION.md:106-107` | Coppola 2016a p. 3 y 7 | "la detección MODIS es FIEL a Coppola 2016a" | p. 3: L21ok usa la 22 y la 21 sólo si la 22 satura; p. 7: sin condición de temperatura | **EL PAPER NO LO SOSTIENE**, ya reconocido (D21, D22, S138). Control de método, no es hallazgo nuevo | alta | (5, ya abierto) |
| 8 | `CLAUDE.md:106-115`; `MIROVA_DIVERGENCES.md:332, 2088` | Coppola 2016a Tabla 1 y Tests 2 y 3, p. 7 | K1 = −0,8 / −0,6; C1 = 0,003 / 0,01 / 0,02; C2 = 5 / 10 / 15; conectiva "or" (= `min`); μ y σ de todos los píxeles aptos de la imagen | idéntico en la imagen. La prosa de la misma página ("a minimum threshold needs to be exceeded") tira hacia `max`, como ya anotó S136 | **CITA CORRECTA** | alta | |
| 9 | `MIROVA_DIVERGENCES.md:889` | "Coppola 2016a Table 2" | C1 summit 0,003 y scene 0,010 | esos valores están en la **Tabla 1** (p. 7) | **CITA CORRUPTA** (número de tabla) (C-09) | alta | 1 |
| 10 | `MIROVA_DIVERGENCES.md:306-307` | Coppola 2016a Fig. A6, p. 21 | cita verbatim "(NTI ≤ -0.93)" | la página dice "NTI < −0.93" | **CITA CORRUPTA** (operador) (C-07) | alta | 1 |
| 11 | `MIROVA_DIVERGENCES.md:446` | Coppola 2016a p. 7 | cita verbatim "m and s are the arithmetic mean..." | la página dice "μ and σ": símbolos corrompidos por la capa de texto y pegados como verbatim | **CITA CORRUPTA** (símbolos; el sentido se conserva) | alta | 1 |
| 12 | `MIROVA_DIVERGENCES.md:309, 332` | Coppola 2016a Ec. 4 y 5, p. 5 | "ETI = NTI − NTIbk (Eq. 5)" | el texto define así el ETI, pero la Ec. 5 **impresa** repite la fórmula de NTIbk (errata del paper); la igualdad ETI = NTI − NTIbk sólo aparece escrita en la Fig. 3 (p. 7). La Ec. 4 impresa también trae una errata ("bNTI" por "bNTIapp") | **CITA CORRECTA** en sustancia, localizador impreciso (C-10) | alta | 1 |
| 13 | `MIROVA_DIVERGENCES.md:314-315, 330` | Coppola 2020 Frontiers p. 15, "Image Quality Assessment" | cita verbatim en negrita: "currently absent in all available algorithms" | la página dice "currently absent in all the operational systems (Supplementary Table S1)" | **CITA CORRUPTA** (paráfrasis presentada como verbatim; sentido conservado) (C-11) | alta | 1 |
| 14 | `CLAUDE.md:880-890` (A76) | "Coppola 2023 §2.5 (FP removidos a mano, ~5 % tolerados, aleatorios en espacio/tiempo)" | la base v.1 se limpió a mano y tolera ~5 % | §2.5 (p. 4) sí dice que se supervisó a mano y que quedan errores; no trae "5 %" ni "random". El "c. 5 %" de falsas está en Coppola 2016a p. 9. "aleatorios en espacio/tiempo" no aparece en ninguno de los dos | **CITA CORRUPTA** (mezcla de fuentes) y una parte **SIN LOCALIZAR** (C-05) | alta | 2 |
| 15 | `CLAUDE.md:239` (A12) | "Fix kernel-bg (Coppola 2024 L1129)" | el fondo por vecinos está en el capítulo | esa línea del `.txt` (p. 341, impresa 337) habla de T_bk en el modelo de dos componentes. El respaldo real está una página antes (impresa 336, bajo las Ec. 11 y 12: fondo "generally calculated from pixel(s) surrounding the anomaly") y en Coppola 2016a Ec. 6 (p. 8) | **CITA CORRUPTA** (localizador equivocado; la afirmación sí tiene respaldo) (C-12) | alta | 1 |
| 16 | `MIROVA_DIVERGENCES.md:1267, 1281` | "Coppola 2024 Eq. 13" | MIROVA detecta con "fondo local al cluster (Eq. 13)", "la topografía se cancela por construcción" | la Ec. 13 es sólo la suma del exceso de radiancia de los píxeles; el fondo local está en el texto de las Ec. 11 y 12. "Se cancela por construcción" ya fue rebajado por A69 con Wright 2002 | **CITA CORRUPTA** (número de ecuación) | alta | 1 |
| 17 | `MIROVA_DIVERGENCES.md:1040` | "Aveni 2024 Eq. 5" | "falta emisividad ε≈0,95 explícita" | la p. 11 dice que la emisividad se asume **uno** "for sake of simplicity" | **EL PAPER NO LO SOSTIENE** (el paper dice lo contrario del drift anotado) (C-13) | alta | 1 |
| 18 | `CLAUDE.md:123-124` | "Coppola 2016a + Campus 2024" | kernel de 8 vecinos del dNTI con media aritmética | Coppola 2016a p. 5: media aritmética de los ocho vecinos, correcto. Campus 2024 p. 3 usa "arithmetic mean" para el **fondo de radiancia**, no para el dNTI | primera cita **CORRECTA**, segunda **EL PAPER NO LO SOSTIENE** | alta | 1 |
| 19 | `MIROVA_DIVERGENCES.md:320-323, 333` | Coppola 2023 p. 4, Method-2 | "mecanismo MIROVA que VRP Chile NO replica, drift remanente" | Method-2 es un filtro para calcular la **energía semanal de la base de datos**, no un paso del NRT | **EL PAPER NO LO SOSTIENE** como "drift" del NRT | alta | 1 |
| 20 | `MIROVA_DIVERGENCES.md:504` | Laiolo 2017 p. 5 | "MIROVA detecta fumarolas 1,6 MW con Tabla 1 estándar", luego no perseguir C2 por régimen | la página dice que la primera alerta genuina fue de 1,6 MW; no dice con qué umbrales (el paper remite a Coppola 2016a en general) | **CITA CORRECTA** en el dato, inferencia razonable pero no textual | media | 1 |
| 21 | `CLAUDE.md:126` | Coppola 2016a p. 3 | "MODIS 21/22 (3.929/3.959 μm)" | el paper da 3,959 µm para **las dos** bandas | **CITA CORRUPTA** leve (3,929 es el borde inferior del paso de banda, no un centro) | media | 1 |
| 22 | `CLAUDE.md:95-101` | Coppola 2016a Ec. 7 (p. 8); Campus 2022 Ec. 1 (p. 7); Campus 2024 (p. 4); Coppola 2026 Tabla 1 (p. 8); Di Bella 2024 (p. 7) | k = 18,9 / 19,7 / 18,0 con área nadir fija; no usar 2,48×10⁷ de Di Bella | los tres coeficientes y las tres áreas están publicados por el grupo (Coppola 2026, Tabla 1: 18.9, 19.7, 18; 1.0×10⁶, 5.6×10⁵, 1.4×10⁵ m²). Di Bella (Catania) da 2,48×10⁷ y el proyecto lo rechaza bien | **CITA CORRECTA** | alta | |
| 23 | `MIROVA_DIVERGENCES.md:2232-2236` (D21) | Coppola 2016a p. 3 | L21ok con L21 o L22 "depending on band 22 saturation" | verbatim | **CITA CORRECTA** (control) | alta | |
| 24 | `MIROVA_DIVERGENCES.md:2257-2262` (D22) | Coppola 2016a p. 7 | Tests 2 y 3 sin condición de temperatura | confirmado | **CITA CORRECTA** (control) | alta | |
| 25 | D23, l. 2290 | Coppola 2016a p. 6 | Test 1 `NTI > K1`, activos y descartados para pasos siguientes | verbatim | **CITA CORRECTA** | alta | |
| 26 | D24, l. 2300 | Coppola 2016a p. 3 | conserva DN = 65 533 | verbatim | **CITA CORRECTA** | alta | |
| 27 | D25, l. 2310-2312 | Coppola 2016a Ec. 6 (p. 8); Fernandina 2025 Ec. 3 (p. 9) | fondo = media aritmética de los píxeles que rodean; vecinos no alertados | ambos confirmados; también Campus 2022 p. 7, Campus 2024 p. 3, Coppola 2023 p. 3 | **CITA CORRECTA** | alta | |
| 28 | D26, l. 2355-2357 | Coppola 2016a "p. 6-7"; Coppola 2014 p. 3409 | no aptos excluidos de los pasos siguientes; `and` explícito en 2014 | la lista de no aptos (borde, dNTI o dETI < −0,1) está en la **p. 5**, no en 6-7; el K1 sí en p. 6. Coppola 2014: confirmado | **CITA CORRECTA**, localizador incompleto | alta | |
| 29 | D27, l. 2363-2365 | Coppola 2016a Tabla 1 y p. 16-17 | Tabla diurna; falsas alertas sobre todo de día | confirmado | **CITA CORRECTA** | alta | |
| 30 | D28, l. 2371 | Coppola 2016a p. 3; Coppola 2023 p. 3 | bow tie removido antes de remuestrear | confirmado en ambos | **CITA CORRECTA** | alta | |
| 31 | D29, l. 2379 | Coppola 2016a Ec. 4, p. 5 | un solo ajuste cuadrático | confirmado ("A quadratic best-fit regression") | **CITA CORRECTA** | alta | |
| 32 | D20, l. 2194-2209 | Coppola 2016a p. 3 y 4; Wright 2002; Coppola 2023 p. 3; cap. 11 Tabla 2 | el paper usa L32 (12,02 µm) en el NTI | confirmado en los cuatro | **CITA CORRECTA** | alta | |
| 33 | D18, l. 1999-2004 | Coppola 2016a p. 3; Coppola 2023 p. 3 | ROI1 caja de 5 × 5 km | confirmado | **CITA CORRECTA** | alta | |
| 34 | D17, l. 1906-1910; `CLAUDE.md` A66 | Coppola 2016a p. 3; Coppola 2023 p. 3; Campus 2022 p. 7; Campus 2024 p. 3 | recorte y remuestreo a grilla de 1 km; 51 × 51, 67 × 67, 50 × 50 km | confirmado en las cuatro páginas | **CITA CORRECTA** | alta | |
| 35 | D14, l. 1550, 1642-1662; `MISSION.md:142` | Laiolo 2026 Bull. Volcanol. 88:11 p. 4; Campus 2022 p. 8 §3.4; Campus 2024 p. 4 | sin filtro automático de nube; la salvedad S141 sobre el filtro por distancia | verbatim, y la salvedad está bien puesta | **CITA CORRECTA** | alta | |
| 36 | `MIROVA_DIVERGENCES.md:297-298` | Coppola 2016a p. 5 | "the presence of clouds is not taken into account" | verbatim | **CITA CORRECTA** | alta | |
| 37 | `MIROVA_DIVERGENCES.md:303-304` | Coppola 2016a p. 17 | "no robust method", "as they are" | verbatim | **CITA CORRECTA** | alta | |
| 38 | `MIROVA_DIVERGENCES.md:311-312` | Coppola 2020 p. 13 | falsas alertas "between 0 and 3%" | localizado en capa de texto, no vi la imagen | **SOSPECHA** (probablemente correcta) | media | |
| 39 | `MIROVA_DIVERGENCES.md:317-318` | Coppola 2023 p. 4 §2.5 | "as-are", sin correcciones atmosféricas | verbatim | **CITA CORRECTA** | alta | |
| 40 | `MIROVA_DIVERGENCES.md:337, 1011-1014` | Coppola 2016a Ec. 8 (p. 9); cap. 11 Ec. 13 | RP = suma sobre los píxeles alertados | confirmado | **CITA CORRECTA** | alta | |
| 41 | `MIROVA_DIVERGENCES.md:339` | Coppola 2016a p. 8 | "(or around the active cluster)" | verbatim | **CITA CORRECTA** | alta | |
| 42 | `MIROVA_DIVERGENCES.md:472` | Coppola 2016a p. 5 | no aptos: borde y dNTI o dETI < −0,1 | verbatim, con "<" correcto | **CITA CORRECTA** | alta | |
| 43 | `CLAUDE.md:385-400` (A35) | Wooster 2003 Fig. 4 (p. 6); cap. 11 Tabla 1 (p. 335) | 57,6 es ejemplo de la Fig. 4; saturación ~450 K en Wooster y 500 K en el capítulo | confirmado todo; el 500 K es una fila de la tabla de sensores (canal de baja ganancia), no un "umbral operacional" redefinido | **CITA CORRECTA** con matiz | alta | |
| 44 | `CLAUDE.md:417-427` (A37) | MODIS L1B UG Tabla 5.6.1 (p. 40); VIIRS L1B UG Apéndice C (p. 40) | 65533 = detector saturado; VIIRS usa bandera de valor 4 | confirmado. La capa de texto del MODIS UG desordena código y descripción: otro ejemplo de por qué se renderiza | **CITA CORRECTA** | alta | |
| 45 | `CLAUDE.md:786-800` (A69) | Wright 2002 p. 141 | el NTI depende de la geografía y la estación | verbatim | **CITA CORRECTA** | alta | |
| 46 | `CLAUDE.md:1197-1199` (A105) | Coppola 2026 Sci. Data p. 7 y Tabla 1 | sin control manual; umbrales de VRP por sensor | verbatim. La Tabla 1 empieza en p. 7 y sigue en p. 8 | **CITA CORRECTA** | alta | |
| 47 | `HYPOTHESIS_LOG.md:774` | Aveni 2025 GRL Ec. 8 y 9 (p. 4) | k_TIR = 60,17 a 11,45 µm | la Ec. 8 renderizada da 60,17 al evaluarla en 11,45 | **CITA CORRECTA** | alta | |
| 48 | `HYPOTHESIS_LOG.md:776` | "Aveni 2024 Eq. 5 p. 12" | Stefan-Boltzmann | la Ec. 5 está en la **p. 11** | **CITA CORRECTA**, página corrida en uno | alta | |

Filas 49 a 59 (todas CITA CORRECTA, confianza alta, sin gravedad): `CLAUDE.md` A9 sobre Di Bella
(autores de Catania, confirmado en p. 1 y 7); las cuatro citas S141 que re-verifiqué de D17 y D18
(Campus 2022 p. 7 y p. 8, Campus 2024 p. 3 y p. 4); Coppola 2016a p. 8 "visual inspection ... a
posteriori"; Coppola 2016a p. 7 y 8 "Second run"; Coppola 2016a p. 9 "omitted c. 10 %, false c.
5 %"; Fernandina 2025 p. 6 banda 31 (localizada en capa de texto y coherente con la p. 9 vista);
capítulo 11 Ec. 17 (σε/αε, p. 341); que el capítulo de Coppola es efectivamente el 11 del libro
(tabla de contenidos, p. 7).

## 3. Los que caen, por gravedad

### C-01 (gravedad 5). El camino que dispara en el 78 % de los registros VIIRS 375 se atribuye a un paper que no está, y el paper que sí está no lo describe

**El fenómeno.** El "Test 1 integrado" suma el exceso de radiancia MIR de todo un disco de 3 km
sobre el fondo de un anillo y dispara si esa suma supera 3 sigmas propagadas. Es el camino que en
S27 subió el recall de 50 a 80 % y cerró D4, y el mismo que A69 identifica como el que capta el
valle tibio en los nevados. `docs/audit_s138/EJE_2_matriz_conformidad_pdf.md:112` mide que
`triggered_test1` vale en 77,89 % de los registros V375 y 22,21 % de los V750; `ENABLE_TEST1_PATH`
es `True` en el perfil operacional (verificado hoy leyendo `pipeline.profile`).

**La cita.** `MIROVA_DIVERGENCES.md:707` lo hace pasar las 3 preguntas de MISSION con "Test 1 ES
Coppola 2015 §2.2 Eq.1, paper MIROVA core foundational". La ficha SDA del código
(`pipeline/test1_integrated.py:12-18`, `pipeline/process_modis.py:16`) cita "Coppola et al. 2015,
MIROVA: a new hotspot detection system based on MODIS Level 1B data, Bulletin of Volcanology
77:55, §2.2".

**Lo que encontré.**
1. Ese PDF no está en `documentacion/` (busqué por "2015", "0953", "77:55", "new hotspot detection
   system" en nombres y en el contenido de todos los `.txt` y `.md`).
2. `docs/F62_TEST1_K_SIGMA_BRAINSTORM_S78.md:18-24` trae una cita "verbatim" entre comillas y
   debajo admite: "Cita reconstruida desde docstring + design doc. PDF físico no presente". Es
   decir, la cita textual se escribió sin el paper a la vista.
3. `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:36-47` (S128) ya estableció que "Coppola 2015" y
   `sp426.5.pdf` son el mismo paper. En ese paper, visto en imagen: la Ec. 1 es el NTI (p. 4) y
   el Test 1 es `NTI_PIX > K1`, un umbral fijo por píxel (p. 6). No hay §2.2, no hay suma sobre
   el ROI, no hay k = 3 ni piso relativo de 0,02.
4. Todos los textos del grupo que abrí citan el algoritmo de MODIS como "Coppola et al. 2016":
   Laiolo 2026 (p. 4), Campus 2024 (p. 3), Coppola 2023 (p. 3), Laiolo 2017 (p. 2 y 3, capa de
   texto). Ninguno menciona un Bull. Volcanol. 77:55. No puedo afirmar que el artículo no exista
   (no busqué en línea, por instrucción); sí que nadie en el proyecto lo ha tenido nunca en la mano.
5. El manuscrito ya lo dice en una nota interna (`docs/paper/sec5_methods.md:288`: "el Test 1
   integrado en 3 km, que el paper no describe"), pero el catálogo no tiene una D para esto, la
   auditoría S138 lo siguió tratando como "Coppola 2015 BV, no SP426.5", y la ficha de
   transparencia publicada sigue citando la referencia.

**Por qué es grave.** Es el único camino de detección del perfil "clon literal" cuyo respaldo
bibliográfico nadie ha visto, es el dominante en el sensor que sostiene el recall, y su entrada
por la puerta 1 de MISSION ("está en un paper MIROVA") apaga la pregunta de si es un parche propio.
Si es propio, la sobre-publicación que S139 identificó como la brecha real de paridad tiene acá un
candidato que hoy está protegido por una cita. Además es un SDA bajo la Resolución 372: la ficha
declara una fuente que no se puede mostrar.

**Prueba.** `experiments/_s146_auditoria/frente_C/png/sp_p06.png` (Test 1 del paper),
`png/sp_p03.png` y la p. 4 vista en sesión (Ec. 1 = NTI), `png/bv2026_p04_clip.png` y
`png/campus24_p03.png` (el grupo cita "Coppola et al. 2016").

### C-02 (gravedad 3). El tope de 5 MW de D9 no es "la implementación programática" de nada que diga el paper

`MIROVA_DIVERGENCES.md:327` afirma que el tope (`path_d_only_cap_mw: 5.0` con
`path_d_only_cap_tbg_max_k: 270`, vigente en el perfil) "NO es un parche". La frase citada existe,
pero leída completa (p. 16-17): las falsas alertas ocurren principalmente **de día**, en bordes de
cuerpos de agua y nubes dispersas, irradian típicamente menos de 5 MW y se identifican por
inspección visual. El paper describe cuánto miden las falsas; no propone recortar nada a 5 MW, y
el caso que el tope ataca (registros nocturnos inflados 20 a 150 veces sobre cirrus) es el
fenómeno opuesto al de la cita. El tope puede ser una buena mitigación, pero es propia. D9 figura
como "EFECTIVAMENTE RESUELTA" apoyada en esta lectura. Prueba: `png/sp_p17.png`.

### C-03 (gravedad 3). "Caso Gaua, p. 17" no existe en Coppola 2016a

`MIROVA_DIVERGENCES.md:259, 265, 287` citan "Coppola 2016a Gaua: <2 % FPs, siempre <5 MW, Tier A
sospechoso". "Gaua" tiene cero apariciones en las 25 páginas del PDF y en `sp426_5.txt`; los casos
del Apéndice A son Bezymianny, Eyjafjallajökull, Erta Ale, Dubbi, Ubinas, Villarrica, Tolbachik,
Etna y Stromboli. En `documentacion/` Gaua sólo aparece en Coppola 2023 (lista de volcanes con
fumarolas, sin cifras de falsas alertas) y en el suplemento de Coppola 2019. La línea 287 usa este
caso como segundo respaldo del tope de 5 MW. La tabla viene de un subagente que leyó notas del
Vault y no el PDF (lo dice la l. 294). SIN LOCALIZAR.

### C-04 (gravedad 3). La Tabla 1 no tiene umbrales para temperatura de brillo

`CLAUDE.md:108-110` y el perfil (`mirova_equivalent.yaml:128-134, 280-282`) atribuyen a "Coppola
2016a Tabla 1" el N·σ = 5 / 10 que `enable_dual_roi_bt` aplica a la BT MIR. En la página, C2
multiplica la desviación estándar de dNTI y dETI; el paper no tiene ningún test de temperatura.
D22 reconoce la compuerta de 3 K, pero este es otro camino (el "Path A") y sigue descrito como
"MIROVA literal". No medí cuánto decide hoy en producción: el efecto operacional es SOSPECHA.
Prueba: `png/sp200b_p07_clip.png`, `png/sp200_p07_clip.png`.

### C-08 (gravedad 3). "El código actual ya es fiel" sigue vivo en la l. 455

La lectura de S100 del "discarded for further steps" es defendible y la página la apoya. Pero la
conclusión de la misma línea es falsa desde S128: el paper saca los píxeles K1 del pool de μ y σ
y el código no. `CLAUDE.md` ya lo marca y el catálogo lo reabre en l. 1319-1335, pero la l. 455 no
lleva ninguna advertencia y el censo la recoge como `es_fiel`. Un lector que llegue por F1.2 se va
con el cierre viejo. Prueba: `png/sp_p06.png`, `png/sp200b_p07_clip.png`.

### C-05 (gravedad 2). A76 mezcla dos papers y agrega una frase que no está en ninguno

`CLAUDE.md` A76 cita "Coppola 2023 §2.5 (FP removidos a mano, ~5 % tolerados, aleatorios en
espacio/tiempo)". La supervisión manual sí está en §2.5 (p. 4). El 5 % es de Coppola 2016a p. 9 y
se refiere al algoritmo, no a lo que queda tras limpiar. "Aleatorios en espacio/tiempo" no aparece
("random" tiene cero apariciones en Coppola 2023 y en Coppola 2020). La lección de A76 sobre los
artefactos diurnos no depende de esto, pero la cita entre comillas es inventada o viene de otra
fuente. Prueba: `png/c2023_p04.png`.

### C-06 (gravedad 2). "Drift D3 resuelto" se apoya en una ecuación que el mismo catálogo dice que el NRT no usa

Detalle en la fila 5. Lo que sí sostiene el cierre es Aveni 2024 Ec. 5. La Ec. 16 del capítulo es
el modelo de dos componentes, y "no adoptada operacionalmente" no lo dice ningún paper: es una
inferencia. El trabajo posterior del mismo grupo (Aveni 2025, Fig. 1) dice que el enfoque que
usamos subestima fuerte bajo 600 K. El VRP TIR no es el producto principal, por eso gravedad 2.
Prueba: `png/libro_p341.png`, `png/aveni24_p11.png`, `png/aveni25_p04.png`.

### C-07, C-09, C-10, C-11, C-12, C-13 y filas 11, 16, 21 (gravedad 1)

Errores de transcripción que no cambian ningún veredicto pero que son exactamente el tipo de
corrupción que el proyecto ya conoce: "≤" por "<" en la Fig. A6 (`png/spA6_p21_clip.png`), "Table
2" por Tabla 1, "m and s" por "μ and σ", una paráfrasis en negrita presentada como verbatim
(`png/c2020_p15_clip.png`), dos números de ecuación del capítulo Springer corridos
(`png/libro_p340.png`), el drift R6 #12 que pide una emisividad de 0,95 que Aveni 2024 no usa, y
la Ec. 5 del paper que en el papel es una errata. Conviene que el manuscrito no cite "Eq. 5" para
el ETI sino la definición en el texto de la p. 5 o la Fig. 3.

## 4. Verificado limpio

Lo central del algoritmo está bien transcrito. Contra la página renderizada coinciden: la Tabla 1
completa; la forma de los Tests 2 y 3 con "or" y sin temperatura; μ y σ globales por imagen; la
media aritmética de los ocho vecinos; los no aptos (borde, dNTI o dETI < −0,1); el segundo pase;
la Ec. 6 con el fondo por vecinos y la Ec. 8 como suma; el remuestreo a 1 km, la grilla de 50 km,
la caja de 5 km y el bow tie; la banda 32 en el NTI; la conservación del DN 65 533. Las citas
verbatim de D21 (p. 3) y D22 (p. 7) están correctas. Las divergencias D20 a D29 registradas en
S138 describen bien lo que dice el paper (con dos localizadores de página imprecisos, filas 12 y 28).

Los tres coeficientes de Wooster y las tres áreas nadir de `CLAUDE.md` tienen hoy respaldo
publicado por el propio grupo (Coppola 2026, Tabla 1), además de la calibración empírica de S14.
El rechazo al coeficiente de Di Bella (INGV Catania) es correcto y la afiliación está bien
tratada: no encontré ningún cierre que use a Catania o a Potenza como autoridad MIROVA.

A35 (Wooster Fig. 4), A37 (tablas de saturación de MODIS y VIIRS), A69 (Wright p. 141), A105
(Coppola 2026 p. 7) y D14 (Laiolo 2026 p. 4, con la salvedad de S141) están bien citadas. Las
cuatro citas S141 que re-verifiqué como muestra salieron bien, lo que habla a favor del método de
esa sesión.

## 5. Límites de este frente

- No busqué en línea. Que el Bull. Volcanol. 77:55 no esté en `documentacion/` no prueba que no
  exista; prueba que el proyecto nunca lo leyó.
- No corrí código ni medí efectos: todo efecto operacional mencionado (C-01, C-04) viene de
  documentos del repo o queda marcado SOSPECHA.
- 8 afirmaciones quedaron sin cotejar (sección 1). SIN DATO no es OK.
- La tesis de Massimetti y Coppola 2019 (suplemento) no se abrieron.
