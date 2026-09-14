# S139 (tanda 2): inventario de tablas, figuras y secciones que la extracción de texto perdió

Auditor: agente de lectura de PDF, sesión S139, 2026-09-14. Repo en `main` limpio (HEAD
`1952bd2ca`). **Auditoría read-only: no se modificó ningún archivo del repositorio.** Los
scripts viven en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\pdf_lectura\`
y los PNG de páginas de papers en su subcarpeta `out/`, que **no se commitea** (derechos de
autor, repo público): está explicado en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\pdf_lectura\out\README.md`.

**Qué se hizo.** Inventario por página de los seis PDF de prioridad 1 con PyMuPDF (imágenes,
dibujos, captions, ecuaciones numeradas, densidad de operadores), renderizado a PNG de toda
página con tabla, ecuación o figura con parámetros, y lectura de esos PNG con la herramienta
`Read`, comparando contra `documentacion/sp426_5.txt`, contra
`documentacion/BIBLIOGRAPHY_SYNTHESIS.md` y contra el catálogo `docs/MIROVA_DIVERGENCES.md`.

**Lo que NO cubre.** No se leyeron las 204 páginas de la tesis de Massimetti ni los PDF de
prioridad 2. El cruce automático «¿esta figura está citada en el repo?»
(`cruce_citas_repo.py`) **no funcionó** y sus números no se usan: cuenta etiquetas «Figure N»
dentro de documentos que nombran el paper, y esos documentos tienen sus propias figuras, así
que da 76 citas para la Figura 11 de SP426.5, que es absurdo. El instrumento falló su propia
prueba de utilidad y se reporta así. Las afirmaciones de «nunca citada» de este informe salen
de `grep` dirigidos por cadena única (la fórmula `8.6344`, el rótulo `ETI = NTI - NTIapp`,
`Alert2`, `78.4`), no de ese cruce.

---

## Resumen ejecutivo

Lo que se estaba perdiendo, en una línea cada cosa:

1. La corrupción de la capa de texto de SP426.5 es **peor y más silenciosa** de lo que dice la
   regla A95: el `>` se convierte en un **punto**, no en una coma, y el `=` en `¼`.
2. Coppola et al. 2025 (paper marcado `SIN_TOCAR`) trae el **coeficiente de Wooster en forma
   cerrada**, y reproduce dos de nuestros tres coeficientes empíricos a la cuarta cifra.
3. El paper hermano Coppola 2014, en una página que nadie citó, resuelve la misma conectiva
   que está abierta desde S136 **con un `and` explícito**.
4. Un doc del repo cita una ecuación de SP426.5 que **no existe en el paper**.
5. La figura 4 de SP426.5 rotula el ETI de una manera y la figura 3 de otra, y el paper nunca
   escribe la ecuación del ETI: sólo la prosa.

---

## (a) Inventario: PDF, páginas, tablas, figuras, ecuaciones

Fuente: `experiments/_s139_audit/pdf_lectura/inventario_pdf.py` y `mapa_captions.py`
(salida en `out/inventario.json`).

| PDF | pág. | tablas | figuras | ec. numeradas | operadores en la capa de texto | extracción fiel |
|---|---|---|---|---|---|---|
| `sp426.5.pdf` (Coppola 2016a) | 25 | 1 (p. 7) | 11 + A1 a A11 (p. 19 a 22) | 8 (p. 4, 5, 8, 9) | **2 en 25 páginas** (0,08/pág.) | **NO** (ver sección c) |
| `coppola2014_ijrs_...pdf` | 26 | 3 (p. 9, 12, 12) | 12 | 6 | 50 (1,92/pág.) | parcial (`=` → `¼`) |
| `coppola2012_jvgr_...pdf` | 14 | 0 con caption formal | 8 | 0 numeradas | 38 (2,71/pág.) | parcial (`=` → `¼`) |
| `Rapid_Response_...pdf` (Coppola 2025) | 26 | 1 (p. 5 a 10) | 10 | 4+ | 52 (2,00/pág.) | sí |
| `THESIS_MASSIMETTI.pdf` | 204 | 9 páginas con caption | 94 páginas con figura | 10 | 116 (0,57/pág.) | sí |
| `Coppola_2019_supp_DataSheet.pdf` | 37 | 18 formularios | 1 imagen | 0 | 0 | sí (es texto de formulario) |

**Diagnóstico reutilizable**: la presencia del carácter `¼` en el texto extraído marca que en
ese PDF el signo `=` se corrompió, y por lo tanto que sus desigualdades también son
sospechosas. Da positivo en SP426.5, Coppola 2014 y Coppola 2012. Da negativo en Coppola 2025,
la tesis de Massimetti y Campus 2022. Reproducir: el bloque final de
`experiments/_s139_audit/pdf_lectura/perdidas_sp426.py`.

---

## (b) Hallazgos

### H1. El `>` de SP426.5 se convierte en un PUNTO en la capa de texto, no en una coma; A95 sólo nombra la coma

- **ARCHIVO:PÁGINA** · `documentacion/sp426.5.pdf` p. 3, 6 y 7 contra
  `documentacion/sp426_5.txt` · script `experiments/_s139_audit/pdf_lectura/perdidas_sp426.py`.
- **QUÉ PASA** · La capa de texto de las 25 páginas contiene **2** caracteres de `<`, `>`, `≤`,
  `≥`, `σ`, `μ` sumados (ambos en la p. 9). El resto se sustituye así:

  | el papel dice | la capa de texto da | ejemplo verificado |
  |---|---|---|
  | `>` | **`.`** (punto) | `NTIPIX . K1` (p. 6, Test 1); `dNTIPIX . C1` (p. 7, Test 2); `DN . 32 768` (p. 3) |
  | `=` | `¼` | `DN ¼ 65 533` (p. 3) |
  | `< −` | `,2` | `dNTI or dETI ,20.1` (p. 5); `NTI ,20.93` (p. 21) |
  | `μ` | `m` | `mdNTI` (p. 7) |
  | `σ` | `s` | `C2sdNTI` (p. 7) |

  La regla A95 en `CLAUDE.md` sólo nombra el caso de la coma (`,20.93`). El caso del punto es
  el peligroso: `NTIPIX . K1` se lee como una frase truncada y **no aparece en ningún `grep` de
  `>`**. Es el modo de falla de A89 (el cero de un grep se lee como ausencia) aplicado a los
  operadores. El `or` de los Tests 2 y 3 **sí sobrevive** en la capa de texto, así que el frente
  de la conectiva nunca dependió de esto.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada directo. Cambia el método de lectura: toda
  condición de umbral leída del `.txt` de SP426.5 está sin operador, y quien busque `>` para
  encontrar un umbral va a concluir que no existe.
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/pdf_lectura/perdidas_sp426.py`
  (la p. 21 es el control: si no marca `,20.93`, el detector está roto).
- **CONFIANZA** · Alta (leído en el render y en la capa de texto). **GRAVEDAD 4.**

### H2. Coppola 2025 da el coeficiente de Wooster en forma cerrada; reproduce nuestros 18,0 y 19,7, y deja MODIS 1,3 % abajo

- **ARCHIVO:PÁGINA** · `documentacion/Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf`
  p. 9, ecuaciones 1 y 2 · script `experiments/_s139_audit/pdf_lectura/coeff_alpha_coppola2025.py`.
- **QUÉ PASA** · El paper escribe `VRP = ΔL_MIR × (σ·ε)/(α·ε_MIR) × A_pix` y, en la ecuación 2,
  `α = −8,6344e−10 × λ + 6,3796e−9`, con λ la longitud de onda central de la banda MIR. Con
  ε = ε_MIR = 1 el factor es σ/α, que es exactamente nuestro `WOOSTER_COEFF`. Evaluado:

  | banda | λ (µm) | σ/α del paper | nuestro valor (S14, empírico contra OSF v2.5) | razón |
  |---|---|---|---|---|
  | VIIRS I4 (375 m) | 3,74 | **17,998** | 18,0 | 0,9999 |
  | VIIRS M13 (750 m) | 4,05 | **19,669** | 19,7 | 0,9984 |
  | MODIS B21/B22 | 3,959 | **19,147** | 18,9 | 1,0131 |

  Dos de tres coinciden a la cuarta cifra con lo que S14 derivó empíricamente sin conocer esta
  fórmula. El tercero, MODIS, queda **1,31 % por encima** de nuestro 18,9 (que es el número
  impreso en la ecuación 7 de SP426.5 y el que la calibración empírica confirmó).
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada que haya que tocar hoy: el 18,9 está validado
  empíricamente y la diferencia es 1,3 %, menor que la dispersión de la paridad. Lo que cambia
  es que **ya no hace falta calibrar empíricamente un sensor nuevo**: si mañana entra MERSI-II,
  SLSTR o ABI, el coeficiente sale de la fórmula. Y da un valor de referencia con el cual
  contrastar cualquier coeficiente futuro. La fórmula no aparece en ningún doc ni en
  `pipeline/` (`grep -rn "8\.6344\|6\.3796" docs/ pipeline/ documentacion/*.md` da 0 líneas).
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/pdf_lectura/coeff_alpha_coppola2025.py`
- **CONFIANZA** · Alta (fórmula leída del PDF, aritmética del script). **GRAVEDAD 4** por lo que
  habilita, no por un error actual.

### H3. Coppola 2014 combina sus dos condiciones de umbral con un `and` explícito, y SP426.5 dice estar de acuerdo con ese procedimiento

- **ARCHIVO:PÁGINA** · `documentacion/coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf`
  p. 9 (Tabla 1 y test 2), leída en el render `out/coppola2014_ijrs_strombolian_1_p009.png`.
- **QUÉ PASA** · El test 2 de ese paper se escribe, literal:
  `Alert2 = (NTI_ROI3 > NTI_Max2) and [NTI_ROI3 > (NTI_Mean2 + 3 × NTI_std2)]`, y el alerta
  final es `test 1 or test 2`. O sea: **dentro de un test las dos condiciones se combinan con
  `and`** (un `max`), y los tests entre sí con `or`. En SP426.5 p. 9, la misma familia de
  parámetros se declara «in excellent agreement with those obtained using an adapted threshold
  procedure (Coppola et al. 2014)».

  Esto es una pieza nueva en el frente que S136 y S137 dejaron abierto (D26, pregunta 1 del
  correo a Coppola): hasta hoy el debate se apoyaba sólo en SP426.5, donde la **fórmula** dice
  `or` (equivale a `min`) y la **prosa** dice que C1 es un mínimo que hay que exceder (equivale
  a `max`). El paper hermano, del mismo grupo, dos años antes, escribe `and`.

  **Lo que NO prueba**: es otro algoritmo (tres ROI, umbrales estacionales del NTI, no dNTI ni
  dETI) y sus dos condiciones son de naturaleza distinta a las de SP426.5. Es una analogía
  fuerte, no una demostración. `Alert2` no aparece en ningún documento del repo
  (`grep -rn "Alert2" docs/` da 0).
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Es evidencia para el lado `max` de la conectiva de los
  Tests 2 y 3, que hoy corre en `min`. Un flip de esa conectiva cambia la detección de los tres
  sensores, así que **no se propone**: entra como argumento al expediente de D26 y a la
  pregunta 1 del correo a Coppola, que sigue siendo la vía de resolución correcta.
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 DPI=160 python experiments/_s139_audit/pdf_lectura/render_paginas.py coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf 9`
  y mirar el PNG.
- **CONFIANZA** · Alta en la cita; media en su transferencia a SP426.5. **GRAVEDAD 4.**

### H4. Un doc del repo cita textual una ecuación de SP426.5 que no existe en el paper

- **ARCHIVO:PÁGINA** · `docs/MIROVA_DETAILED_CITATIONS.md:216` (y su copia idéntica
  `documentacion/MIROVA_DETAILED_CITATIONS.md:216`), contra `documentacion/sp426.5.pdf` p. 5.
- **QUÉ PASA** · El doc presenta como cita verbatim atribuida a `sp426_5.txt:275-280`:

  > «the so-called Enhanced Thermal Index (ETI) is obtained by subtracting the background NTIbk
  > (Eq. 4) from the observed NTI (Eq. 1) so that: **ETI = NTI − NTIbk (Eq. 5)**».

  La ecuación (5) impresa en la página 5 del PDF es `NTI_bk = a·NTI²_app + b·NTI_app + c.`, y
  lo mismo dice la línea 280 del `.txt` (`NTIbk = aNTIa2pp + bNTIapp + c. (5)`). La parte en
  negrita está **fabricada**: el paper nunca escribe la ecuación del ETI. Además, las líneas
  52 y 208 del mismo doc citan la ecuación (4) como `a·NTIapp² + b·NTIapp + c`, que es la forma
  de la (5): la (4) impresa dice `b·NTI`, sin el subíndice.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada en el código: el contenido de fondo
  (ETI = NTI − NTI_bk) sí lo dice la prosa del paper y lo confirma el rótulo de la figura 3.
  Lo que importa es que ese doc se usa como fuente de citas verbatim, y una de sus citas no
  resiste el cotejo. Corresponde marcarla, no borrar el archivo.
- **CÓMO REPRODUCIRLO** · `sed -n '205,220p' docs/MIROVA_DETAILED_CITATIONS.md` contra
  `sed -n '255,285p' documentacion/sp426_5.txt`.
- **CONFIANZA** · Alta. **GRAVEDAD 4** (regla A35 y A93: una cita fabricada en el doc de citas).

### H5. La figura 4 de SP426.5 define el ETI de una manera y la figura 3 de otra; el paper nunca escribe la ecuación

- **ARCHIVO:PÁGINA** · `documentacion/sp426.5.pdf` p. 8 (rótulo del panel de la Fig. 4) y p. 7
  (rótulos de la Fig. 3), recortes `out/zoom_p8_fig4label.png` y el render de la p. 7.
- **QUÉ PASA** · El tercer panel de la figura 4 se rotula **`ETI = NTI - NTIapp`**. Los paneles
  (c) y (f) de la figura 3 se rotulan **`ETI = NTI - NTIbk`**. La prosa de la p. 5 dice
  NTI_bk. Las dos son cantidades distintas: el NTI_bk es la salida de la regresión cuadrática
  sobre el NTI_app, no el NTI_app. Como los rótulos de panel viven dentro de la imagen, **no
  existen en ninguna capa de texto**: ni el `.txt`, ni `markitdown`, ni PyMuPDF los ven. Sólo
  aparecen renderizando la página.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nuestro código implementa `ETI = NTI − NTI_bk`, que es
  la lectura de la prosa y de la figura 3, o sea dos apoyos contra uno. No se propone cambiar
  nada. Vale registrarlo como divergencia literal del paper consigo mismo, igual que se
  registró la contradicción de la conectiva.
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 DPI=170 python experiments/_s139_audit/pdf_lectura/render_paginas.py sp426.5.pdf 7 8`
- **CONFIANZA** · Alta (rótulo leído a 500 dpi). **GRAVEDAD 3.**

### H6. Las ecuaciones (4) y (5) impresas difieren entre sí; la figura 2a decide cuál vale

- **ARCHIVO:PÁGINA** · `documentacion/sp426.5.pdf` p. 5 y 6, recortes `out/zoom_p5_eq4.png`,
  `out/zoom_p5_eq5b.png`, render `out/sp426_5_p006.png`.
- **QUÉ PASA** · La ecuación (4) imprime `NTI_bk = a·NTI²_app + b·NTI + c` (segundo término con
  el NTI observado) y la (5) imprime `NTI_bk = a·NTI²_app + b·NTI_app + c.`. Una de las dos es
  errata. La figura 2a la resuelve: el eje x es `NTI_app`, el eje y es `NTI`, y la curva a trazos
  está rotulada `y = ax² + bx + c`, o sea la regresión es del NTI contra el NTI_app y todos los
  términos del polinomio son del NTI_app. **Vale la (5); la (4) tiene una errata.** Eso también
  es lo que hace nuestro código según `docs/audit_s138/EJE_2_matriz_conformidad_pdf.md:264`
  (`np.polyfit(x, y, 2)`), leído pero no verificado en el código por esta auditoría: SOSPECHA.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada. Cierra una ambigüedad que estaba abierta en el
  texto y que ningún doc del repo había resuelto con una fuente.
- **CÓMO REPRODUCIRLO** · Renderizar las p. 5 y 6 con `render_paginas.py`.
- **CONFIANZA** · Alta. **GRAVEDAD 3.**

### H7. El diagrama del flujo NRT de MIROVA rotula «Supervised VRP timeseries»

- **ARCHIVO:PÁGINA** · `documentacion/Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf`
  p. 8 (figura 3) y p. 9 (texto), render `out/Rapid_Response_to_Effusive_Eru_p008.png`.
- **QUÉ PASA** · La figura 3, cuya leyenda es «Schematic diagram of the **MIROVA NRT workflow**»,
  rotula tres de sus nueve paneles como **«Supervised VRP timeseries»**, «Supervised Vent and
  Front location» y «Supervised Length timeseries», y el panel del VRP lleva una leyenda que
  distingue puntos *cloud-free* de *cloudy*, con los *cloudy* fuera de la tendencia. El texto de
  la p. 9 lo dice con palabras: «The VRP timeseries was continuously supervised by visualizing
  each image and excluding data contaminated by clouds or acquired in unfavorable viewing
  conditions».

  Esto tensiona la nota de memoria durable «MIROVA NRT es 100 % algorítmico»
  (`feedback_mirova_no_human_supervision.md`), que hoy dice que la supervisión aplica sólo al
  archivo histórico OSF v2.5 y **no** al canal NRT.

  **Lo que NO prueba**: este paper describe una campaña de respuesta rápida sobre UNA erupción,
  donde la supervisión pudo ser específica del estudio. No dice que `latest.php` se supervise
  volcán por volcán todos los días. Pero la palabra «Supervised» está dentro del diagrama
  genérico del flujo NRT, no en un apartado del caso Fernandina.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada en el código. Cambia cuánto de la brecha de
  precisión contra MIROVA puede atribuirse a algoritmo. Si parte de la limpieza de MIROVA es
  manual, un pedazo de nuestros «falsos positivos» (marco A54) es irreducible por algoritmo, y
  perseguirlo con gates es perseguir a un humano.
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 DPI=160 python experiments/_s139_audit/pdf_lectura/render_paginas.py Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf 8`
- **CONFIANZA** · Alta en la cita; media en su alcance. **GRAVEDAD 3.**

### H8. El MIROVA de 2025 ingiere la banda 31 de MODIS como TIR, no la 32

- **ARCHIVO:PÁGINA** · `documentacion/Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf`
  p. 5 (Tabla 1, columna «ID Band(s)»: 21, 22, **31**) y p. 6 (texto).
- **QUÉ PASA** · Verbatim de la p. 6: «the MIR bands B21 and B22 and the **TIR channel B31**, at
  1 km resolution (Level 1b), are automatically ingested into the MIROVA system». Y la Tabla 1
  le asigna el rango 10,78 a 11,28 µm, que es la 31. SP426.5 p. 4 dice `L_TIR = L_32` (12,02 µm).
  Nuestro código usa la 31.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada: refuerza lo que ya hacemos. Lo que cambia es el
  estado de **D20**, registrada hoy como «usamos la 31, Coppola 2016a usa la 32, despreciable».
  Con esta cita, la 31 es la banda del MIROVA operacional de hoy y D20 deja de ser una
  divergencia con el sistema: pasa a ser una divergencia con el paper de 2016, que el propio
  grupo actualizó. Corresponde anotarlo en el catálogo (decisión de Nicolás).
- **CÓMO REPRODUCIRLO** · Leer las p. 5 y 6 del PDF con PyMuPDF (la extracción de ese PDF es
  fiel: 2 operadores por página, sin `¼`).
- **CONFIANZA** · Alta. **GRAVEDAD 3.**

### H9. La tabla 2 de Coppola 2014 mide el propio algoritmo del grupo: pierde el 21,6 % de las alertas y da 3,5 % de falsas

- **ARCHIVO:PÁGINA** · `documentacion/coppola2014_ijrs_strombolian_...pdf` p. 12 (Tabla 2),
  render `out/coppola2014_ijrs_strombolian_1_p012.png`.
- **QUÉ PASA** · Sobre 9.635 pasadas nocturnas de Stromboli entre 2000 y 2012, con la detección
  manual como referencia: 1.779 alertas manuales (18,5 %), 1.445 del algoritmo (15,0 %),
  **1.395 correctas (78,4 %), 384 perdidas (21,6 %), 50 falsas (3,5 %)**. La Tabla 3 agrega que
  las alertas diurnas son el 3,8 % de las pasadas. Denominador y ventana: los de la tabla, un
  solo volcán de conducto abierto y sensor MODIS.

  Ninguno de esos números aparece en el repo (`grep` de `9635`, `1779`, `78.4` en contexto no
  devuelve la tabla). La referencia de rendimiento que sí está citada es la de SP426.5 p. 9
  («omitted c. 10 % and false c. 5 %»), que es la estimación redonda del paper de 2016.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada. Da una vara: el propio grupo, con su propio
  algoritmo, en el volcán más favorable que tienen, pierde una de cada cinco alertas que un
  humano ve. Sirve para calibrar cuánta paridad es alcanzable antes de gastar sesiones en
  cerrar una brecha de recall.
- **CÓMO REPRODUCIRLO** · Renderizar la p. 12 con `render_paginas.py`.
- **CONFIANZA** · Alta. **GRAVEDAD 3.**

### H10. `CLAUDE.md` atribuye a la tesis de Massimetti un contenido que la tesis no tiene

- **ARCHIVO:PÁGINA** · `CLAUDE.md` del proyecto, sección «documentacion/ archivos clave»:
  la entrada de `THESIS_MASSIMETTI.pdf` la describe como «tesis con detalle **VIIRS adaptation**».
  Contra la portada del PDF (p. 1).
- **QUÉ PASA** · El título de la tesis es «Thermal remote sensing of volcanic activity by using
  **Sentinel-2 and Landsat-8**: an improvement of the MIROVA system». En sus 484.703 caracteres
  de texto, «VIIRS» aparece 26 veces y «ROI» **una**. No es una fuente de parámetros VIIRS.
  Dos documentos del repo ya lo dicen (`docs/PAPERS_AUDIT.md:102`: «marginal para MIR, 90 %
  SWIR focus»; `docs/papers_mirova_processed_S72_backlog.md:26`), o sea la corrección existe y
  `CLAUDE.md` quedó atrás.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada. Cambia el ruteo: una sesión que busque un umbral
  VIIRS y siga el índice de `CLAUDE.md` va a abrir 204 páginas de Sentinel-2. Si en algún lado
  hay un parámetro VIIRS citando esta tesis, esa cita no tiene respaldo (no se buscó; SOSPECHA).
- **CÓMO REPRODUCIRLO** · `python -c "import fitz; d=fitz.open('documentacion/THESIS_MASSIMETTI.pdf'); t=''.join(p.get_text() for p in d); print(t.count('VIIRS'), t.count('ROI'))"`
- **CONFIANZA** · Alta. **GRAVEDAD 2.**

### H11. Medí las barras de color del Apéndice A: el caso negativo A9 no contradice la conectiva `min` (resultado negativo, y un panel falló su control)

- **SCRIPT:SALIDA** · `experiments/_s139_audit/pdf_lectura/medir_figA9.py`.
- **QUÉ PASA** · Las figuras del Apéndice A traen barras de color **cuantitativas** de dNTI y
  dETI, que son la escala real con la que MIROVA trabaja y que no existe en ninguna capa de
  texto. Hipótesis que fui a probar: si en la Fig. A9 (Stromboli 19-ene-2010, caso que la
  leyenda declara **sin detección**) hubiera un píxel con dNTI y dETI sobre C1 = 0,01, la
  conectiva `min` no podría reproducir ese negativo. Mapeando el color de cada píxel del panel
  contra su propia barra:

  | panel | barra | máximo recuperado | fracción sobre 0,01 |
  |---|---|---|---|
  | A8 dNTI (Etna, **positivo**, control) | −0,010 a 0,015 | 0,0150 (satura la escala) | 0,03 % |
  | A9 dNTI (Stromboli, **negativo**) | −0,010 a 0,025 | **0,0090** | 0 % |
  | A9 dETI (Stromboli, negativo) | −0,010 a 0,015 | −0,0012 | 0 % |

  El dNTI del caso negativo se queda **justo debajo** de C1, o sea la figura es compatible con
  `min` y también con `max`: **no discrimina**, y la hipótesis queda refutada por su propio dato.
  El panel dETI de A9 falló el control del instrumento (el rango recuperado no cubre la barra:
  mínimo y percentil 99 coinciden), así que **ese número no vale** y no debe reusarse.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada. Cierra una vía que parecía prometedora para
  decidir la conectiva sin escribirle a Coppola. No lo es.
- **CÓMO REPRODUCIRLO** · `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/pdf_lectura/medir_figA9.py`
- **CONFIANZA** · Media (el recorte de los paneles se hizo por coordenadas medidas sobre el
  render, y el máximo de una barra de MATLAB puede estar fijado por encima del dato).
  **GRAVEDAD 2.**

### H12. Dos de las once preguntas del correo a Coppola ya están contestadas en papers que tenemos

- **ARCHIVO:PÁGINA** · `documentacion/Rapid_Response_...pdf` p. 9 y `documentacion/sp426.5.pdf` p. 3,
  contra `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`.
- **QUÉ PASA** ·
  - **Pregunta 6** («¿VIIRS 375 m y 750 m también se remuestrean a una grilla de área
    constante? ¿cómo se centra?»): Coppola 2025 p. 9, hablando de MODIS **y** VIIRS juntos:
    «MIR and TIR bands were resampled to a regular **51 × 51 km UTM grid centered on the volcano
    summit (coordinates provided by the Global Volcanism Program)**». Contesta las dos mitades.
    La parte del bow tie de esa pregunta sigue abierta.
  - **Pregunta 7** («¿ROI1 sigue siendo una caja fija de 5 × 5 km?»): SP426.5 p. 3 dice «inner
    region (ROI1) consists of a **box (5 × 5 km) centred on the volcano's summit**». La pregunta
    dice «sigue siendo», así que es legítima como pregunta de actualización, pero el estado de
    2016 está documentado y ya lo tenía el repo (`docs/audit_s138/EJE_2_...md` fila P07).

    La figura 1 de SP426.5 además imprime las **coordenadas del centro de grilla** que MIROVA
    usó para sus dos volcanes: Stromboli 38,7894 N / 15,2131 E y Etna 37,7342 N / 15,0044 E.
    Eso es un banco de pruebas de dos casos para D17 (¿nuestra grilla se centra donde MIROVA
    centra la suya?) que nadie ha usado: se contrastan contra la base GVP y se ve si MIROVA
    redondea, trunca o toma el valor tal cual.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada hoy. Sirve para acortar el correo a Coppola (que
  Nicolás quiere enviar) y para darle un test barato a D17.
- **CÓMO REPRODUCIRLO** · Leer la p. 9 del PDF de Fernandina y la p. 4 de SP426.5 renderizada.
- **CONFIANZA** · Alta. **GRAVEDAD 2.**

### H13. La figura 2 de SP426.5 muestra que el Test 1 no dispara en una noche normal

- **ARCHIVO:PÁGINA** · `documentacion/sp426.5.pdf` p. 6 (figura 2, ejes) y p. 7 (Tabla 1).
- **QUÉ PASA** · Los ejes de la figura 2a y 2b, que son el NTI de una imagen nocturna real de
  MODIS sobre el Etna con 2.500 píxeles, recorren de **−0,86 a −0,94**. El K1 nocturno de la
  Tabla 1 es **−0,8**. Es decir, en esa escena ningún píxel llega al umbral del Test 1, ni
  siquiera el que contiene la colada de la Bocca Nuova. Es evidencia visual, sólo disponible en
  la imagen, de que el Test 1 es un camino para anomalías grandes y no participa del régimen en
  que vivimos. Coincide con lo que mide el propio repo sobre sus datos
  (`docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:280`: `nti_max` mediano −0,927, 78,4 % bajo −0,9),
  número que leí pero no reproduje en esta sesión.
- **QUÉ PODRÍA CAMBIAR EN EL PIPELINE** · Nada. Es sustento gráfico para **D23** (el Test 1 no es
  un camino de detección en producción) y para no gastar esfuerzo ahí.
- **CÓMO REPRODUCIRLO** · Renderizar las p. 6 y 7.
- **CONFIANZA** · Alta para el Etna de esa noche; no generaliza a un volcán en erupción.
  **GRAVEDAD 1.**

---

## (c) Qué pierde el `.txt` de SP426.5, página por página

Lo sustantivo, no el ruido de encabezados. Cada fila se verificó contra el render de la página.

| pág. | qué hay | qué pierde o cambia el `.txt` |
|---|---|---|
| 3 | Bandas de interés, filtro de DN, bow tie, banda compuesta L21ok, recorte y remuestreo, ROI1 y ROI2 | `DN > 32 768` → `DN . 32 768`; `DN = 65 533` → `DN ¼ 65 533`. El contenido se conserva. |
| 4 | **Figura 1**: mapa, las dos cajas de 50 × 50 km, y las **coordenadas del centro de grilla** (38,7894 N / 15,2131 E y 37,7342 N / 15,0044 E) · Ec. (1) NTI | Las coordenadas están **dentro de la imagen**: ninguna capa de texto las tiene. |
| 5 | Ec. (2) a (5), el filtro espacial de 8 vecinos, los píxeles no aptos | `dNTI or dETI < −0,1` → `,20.1`. Las ecuaciones (4) y (5) se conservan **con su discrepancia** (`bNTI` contra `bNTIapp`), que nadie había notado. |
| 6 | **Figura 2**: regresión NTI contra NTI_app, con el rango real del NTI y el rótulo `y = ax² + bx + c` · Test 1 · el retiro de los píxeles del Test 1 | El rango de los ejes y el rótulo de la curva están en la imagen. `NTI_PIX > K1` → `NTIPIX . K1`. |
| 7 | **Figura 3** (rótulo `ETI = NTI - NTIbk`) · Tests 2 y 3 · **Tabla 1** · el retiro de los píxeles de los Tests 2 y 3 | `>` → `.`, `μ` → `m`, `σ` → `s`: `dNTIPIX . C1 or dNTIPIX . mdNTI + C2sdNTI`. El `or` **sí** sobrevive. La Tabla 1 se extrae, desordenada. |
| 8 | **Figura 4** (rótulo **`ETI = NTI - NTIapp`**, contradice la p. 7) y sus barras de color (ETI de 0 a 20e−3; dNTI y dETI de −0,01 a 0,01) · Ec. (6) y (7), el fondo de la magnitud | El rótulo del panel y las barras de color son imagen: invisibles. El texto conserva la definición del fondo (media de los píxeles que rodean al activo o al cúmulo). |
| 9 | **Sección «Performance and exportability»** · C2 ≥ 10 pierde 25 % de las alertas chicas, C2 ≤ 3 pierde 7 % con más de 7 % de falsas · omitidas ~10 %, falsas ~5 % · la exportabilidad exige «the same spatial grid and ROIs» | Es la única página donde sobreviven dos operadores (`≥` y `≤`). El contenido se conserva. |
| 10 a 18 | Resultados de Stromboli y Etna, TADR, volúmenes | Sin pérdida relevante para el algoritmo. |
| 19 a 22 | **Apéndice A**: once casos con sus mapas de NTI, NTI_bk, ETI, dNTI, dETI y máscara de alerta, cada uno con **barras de color numéricas** | Todas las barras de color son imagen. Las leyendas conservan el texto pero con `NTI < −0,93` → `NTI ,20.93`. |
| 23 a 25 | Referencias | Ruido de guiones de rango de páginas. |

---

## Cruce con el catálogo de divergencias

| divergencia | ¿algún hallazgo la toca? |
|---|---|
| **D17** (centro de la grilla) | H12: Coppola 2025 confirma 51 × 51 UTM sobre la cumbre GVP para MODIS y VIIRS; la figura 1 de SP426.5 da dos centros concretos con los que probarlo. |
| **D18** (ROI1 caja de 5 km) | H12: confirmado verbatim en SP426.5 p. 3. Sin novedad respecto de S138. |
| **D20** (banda TIR 31 contra 32) | **H8**: el MIROVA de 2025 usa la 31. Cambia el signo de la divergencia. |
| **D21** (banda MIR primaria) | Releído en la p. 3: «L21 or L22 ... depending on band 22 saturation (or not), **respectively**». La 22 es la primaria. Sin novedad; corrobora a S137. |
| **D22** (compuerta de temperatura) | Nada nuevo: la fórmula de los Tests 2 y 3 de la p. 7 no tiene condición de BT, como ya decía S137. |
| **D23** (Test 1 como camino) | **H13**: la figura 2 muestra que el NTI de una noche normal no llega a K1. |
| **D24** (píxeles saturados) | Confirmado verbatim en la p. 3. Sin novedad. |
| **D25** (fondo de la magnitud) | Confirmado en la p. 8 de SP426.5 y en la Ec. 3 de Coppola 2025 (ambas: media de los píxeles que rodean al activo o al cúmulo). Sin novedad. |
| **D26** (conectiva, μ y σ del segundo pase) | **H3**: el `and` explícito de Coppola 2014. **H11**: la vía de las figuras del Apéndice A no discrimina. |
| **D28** (bow tie) | Confirmado en la p. 3 («remove the bow-tie effect»). La pregunta de cómo lo hacen sigue abierta. |
| **D29** (refit iterativo) | La p. 5 describe **un solo** ajuste, sin rechazo de atípicos: la premisa de D29 se sostiene. Nota: `docs/MIROVA_DIVERGENCES.md:309` dice que implementamos «Eq.4 + iterative re-fit ✅», lo que **contradice** a D29, que lo llama divergencia abierta. No lo resolví (leí los dos textos, no el código): SOSPECHA. |
| **GAP #A** | La p. 6 dice que los píxeles del Test 1 se descartan de los pasos siguientes y la p. 7 dice lo mismo de los de los Tests 2 y 3. Sin novedad respecto de S128 y S138. |

---

## VERIFICADO LIMPIO

Cada afirmación numérica o textual de este informe está respaldada por un render que miré en
esta sesión, por una línea de archivo que leí en esta sesión, o por un script de
`experiments/_s139_audit/pdf_lectura/` que corrí en esta sesión. Lo que leí pero no verifiqué
por mi cuenta está marcado **SOSPECHA** (tres casos: el `np.polyfit` de H6, la posible cita
VIIRS a la tesis en H10, y la contradicción de D29). El instrumento que falló
(`cruce_citas_repo.py`) está declarado como fallido y sus números no se usan, y el panel dETI
de H11 está declarado como no válido por su propio control.
