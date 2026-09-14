# S141, lectura de papers, LECTOR B

## Encabezado

**Qué leí** (sesión del 2026-09-14, rama main, sin tocar git ni código):

| archivo | quién lo firma | ¿grupo MIROVA? | cobertura |
|---|---|---|---|
| `documentacion/Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf` (Coppola, Aveni, Campus, Laiolo, Massimetti y Bernard 2025, Remote Sens. 17, 1191) | Torino (Coppola, Campus, Laiolo, Aveni, Massimetti); Aveni también Sapienza Roma; Massimetti también UNAM; Bernard IG-EPN Quito | **Sí** (p. 1, afiliaciones) | texto completo p. 1 a 22 (p. 23 a 26 son referencias, sólo busqué las citas 58, 62, 66, 74, 75 y 77); **renderizadas y miradas**: p. 5, 8, 9, 10, 12, 13, 21 |
| `documentacion/feart-11-1240107.pdf` (Coppola, Cardone, Laiolo, Aveni, Campus y Massimetti 2023, Front. Earth Sci. 11:1240107) | Torino (Cardone es CNR Torino); Aveni también Sapienza | **Sí** (p. 1) | texto completo p. 1 a 14 (p. 15 y 16 referencias); **renderizadas y miradas**: p. 3, 4, 5, 6, 8, 9, 12 |
| `documentacion/rs11131528.pdf` (Valade, Ley, Massimetti, D'Hondt, Laiolo, Coppola, Loibl, Hellwich y Walter 2019, Remote Sens. 11, 1528) | lidera TU Berlin y GFZ Potsdam; Massimetti, Laiolo y Coppola (Torino, Firenze) son coautores | **No es un paper del algoritmo MIROVA**: es el sistema MOUNTS (Sentinel 1, 2 y 5P). Tiene coautores MIROVA pero no describe su detección MIR | texto completo p. 1 a 26; **renderizadas y miradas**: p. 5, 6, 12 |
| `documentacion/Coppola_2019_supp_Table1.xlsx` | material suplementario Coppola 2019 | sí (suplemento) | hoja `Table1`, 18 filas con datos (A1:L25), leída entera con openpyxl |
| `documentacion/Coppola_2019_supp_Table2.xlsx` | idem | sí (suplemento) | hoja `Table2`, 19 filas con datos (rango declarado A1:Z1000, resto vacío), leída entera, incluido el comentario de celda |

Renders a 150 dpi en `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\render_B\` (fuera del repo). Las páginas de prosa sin fórmula ni tabla las leí por la capa de texto; toda cita con operador, número o tabla sale de una imagen mirada.

**Método de numeración**: en los tres PDF la página impresa coincide con la del visor (Fernandina imprime "N of 26", Coppola 2023 imprime "0N", rs2019 "N of 31"). Por eso doy una sola página.

**Qué NO cubrí**:
- Fernandina p. 6, 7, 11, 14 a 20 y 22 sólo por capa de texto (prosa y leyendas de figuras de mapas, sin parámetros; S139 declaró fiel la extracción de este PDF). Las figuras 4, 6, 7, 8, 9 y 10 no las miré como imagen.
- Coppola 2023 p. 1, 2, 7, 10, 11, 13 y 14 sólo por texto; figuras 3 y 6 no miradas.
- rs2019: sólo tres páginas como imagen; el resto (InSAR, CNN, SO2) por texto, porque no trata la detección MIR.
- No leí el paper de Aveni 2023 (MERSI-II), que es la fuente real de la ecuación de alfa (ver B-12).
- No verifiqué nada contra datos ni código salvo las líneas del repo citadas.

Lo ya leído en S139 (`docs/audit_s139/LECTURA_PDF_TABLAS_FIGURAS.md`: H2 coeficiente alfa, H7 "Supervised", H8 banda 31, H12 grilla 51 × 51) no lo repito; donde lo contrasto, lo digo.

---

## Hallazgos, ordenados por gravedad

### B-01. Coppola 2023 dice que los píxeles con bow tie se "identifican y eliminan", y que el remuestreo existe para que todo píxel valga 1 km²

- **Localizador**: `feart-11-1240107.pdf`, p. 3, §2.1 "MODIS-MIROVA", 3.er párrafo (empieza en la columna izquierda "MODIS Level 1B calibrated radiances..." y sigue en la columna derecha, primeras 5 líneas).
- **Cita textual**: *"This step is crucial to ensure that all pixels represent a ground area of 1 km², minimizing the effect of geometrical distortions"* y *"(i.e., pixels affected by bow-tie distortions are identified and removed; Coppola et al., 2010)"*.
- **Qué dice**: el orden descrito es (1) extraer MIR y TIR, (2) remuestrear a grillas UTM 51 × 51 centradas en la cumbre GVP, con el fin explícito de área de 1 km² por píxel, y (3) "once the scenes are geometrically corrected", los píxeles con bow tie se identifican y **eliminan** (no se corrigen ni se promedian).
- **Responde a**: D28 (`docs/MIROVA_DIVERGENCES.md:2282`, "El paper (p. 3) corrige el solapamiento de barridos antes de remuestrear"), D17 (`docs/MIROVA_DIVERGENCES.md:1913`, "El brazo fiel sería **bow-tie + regrid en ese orden**", citando Coppola 2012) y la mitad bow tie de la pregunta 6 del correo (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md:36-38`).
- **Veredicto**: **matiza**. Confirma que MIROVA trata el bow tie (D28 sigue abierta como divergencia), pero agrega que el tratamiento es **descarte de píxeles**, y en la prosa de 2023 el remuestreo aparece **antes** del paso de bow tie, al revés que el orden que D17 atribuye a Coppola 2012. La prosa no es un diagrama de flujo y "once the scenes are geometrically corrected" admite leer que ambas cosas son un solo paso, así que el orden queda ambiguo, no invertido. Nadie en el repo cita esta página para el bow tie (`grep -rn "identified and removed" docs` da 0).
- **Confianza**: 5 en la cita; 3 en el orden de los pasos. **Gravedad**: 4 (define cómo sería el brazo fiel de D17/D28 y acorta la pregunta 6).

### B-02. El grupo declara que una pasada VIIRS a 64,6° de cenit no permitió cuantificar el VRP, y que los sistemas puramente automáticos no avisan de geometría desfavorable ni de falsas alertas

- **Localizador**: `Rapid_Response_...pdf`, (a) p. 13, leyenda de la figura 5a; (b) p. 12, §3.1 "Rapid Response", 1.er párrafo; (c) p. 9, §2.3.1, párrafo "Volcanic Radiative Power", últimas dos frases; (d) p. 21, §5, punto i "Team of Experts".
- **Citas textuales**:
  (a) *"These unfavorable viewing conditions did not allow us to ascertain whether effusive activity was ongoing inside the caldera, nor to quantify the VRP"*;
  (c) *"excluding data contaminated by clouds or acquired in unfavorable viewing conditions"*;
  (d) *"Purely automatic systems, while very valuable for immediate initial assessment, can be misleading in the rapid response, as they lack indications of sub-pixel cloud contamination, unfavorable viewing geometry, or false alerts(s) detection."*
- **Qué dice**: en el producto supervisado de Fernandina, las pasadas de cenit alto (el ejemplo es 64,6°, figura 5a; en 7,6° sí se cuantificó, figura 5b) se excluyen **a mano**. El texto del §5 describe al sistema automático, en general, como uno que no marca geometría desfavorable ni falsas alertas. No hay en el paper ninguna compuerta automática por ángulo cenital.
- **Responde a**: la sobre-publicación VIIRS375 (encargo), D17 y su gradiente cenital (`docs/MIROVA_DIVERGENCES.md:1900-1908`: ratio nuestro/MIROVA 0,740 a nadir contra 0,253 sobre 50°, "MIROVA es plano"), y a la nota de memoria `feedback_mirova_no_human_supervision.md:27-28`, que lee la supervisión de Fernandina como exclusiva del estudio de respuesta rápida.
- **Veredicto**: **matiza**. La lectura de la memoria sobre las p. 9 y 21 sigue siendo defendible (el §5 habla de "the rapid response"), pero la p. 21 dice algo que la memoria no recoge: el grupo mismo afirma que la salida automática contiene falsas alertas y pasadas mal geometrizadas sin marcar. No prueba que `latest.php` se filtre a mano. Sí prueba que el grupo no considera cuantificable una pasada a 64° y no describe cómo el NRT la trataría. Qué hace el feed automático con el cenital alto: **SIN LOCALIZAR** en estos tres papers (candidata a pregunta nueva del correo).
- **Confianza**: 5 en las citas; 2 en su alcance sobre el feed NRT de la web. **Gravedad**: 3.

### B-03. Coppola 2023 declara supervisado a mano el "MIROVA database (v.1)", no el OSF v2.5

- **Localizador**: `feart-11-1240107.pdf`, p. 4, §2.5 "Supervision of the dataset", párrafo único (columna derecha); y p. 3, §1, último párrafo de la columna izquierda (v.1.0 en `https://osf.io/zm62w/`).
- **Cita textual**: *"The current version of the MIROVA database (v.1) consists exclusively of night-time data"* y *"the entire dataset has been supervised to remove obvious "non-volcanic" thermal features"*.
- **Qué dice**: la supervisión manual (quitar incendios y falsas alertas mirando series e imágenes) está declarada para la v.1: MODIS, noche, 111 volcanes, 2000 a 2019. El paper no menciona ninguna v2.5, ni VIIRS.
- **Responde a**: `feedback_mirova_no_human_supervision.md:37` ("Coppola 2023 §2.5 menciona supervisión manual SOLO para el **OSF v2.5 histórico**") y a la regla S139 de la memoria sobre conteos del OSF que no valen para el NRT.
- **Veredicto**: **matiza**. El sentido de la nota (archivo supervisado, web as-are) se sostiene; la etiqueta "v2.5" es una extrapolación: el paper habla de la v.1. Si el repo usa conteos de un OSF v2.5 con filas VIIRS (CLAUDE.md del proyecto, reglas científicas, "48,360 filas"), no hay en este paper evidencia de que ese archivo esté supervisado igual. **SOSPECHA**: que v2.5 herede la supervisión de v.1.
- **Confianza**: 5 en lo que dice el paper; 3 en la consecuencia. **Gravedad**: 3.

### B-04. Ninguno de los dos papers dice a qué tamaño de celda se remuestrea VIIRS; sólo Coppola 2023 fija 1 km² para MODIS

- **Localizador**: `Rapid_Response_...pdf`, p. 9, §2.3.1, 1.er párrafo; `feart-11-1240107.pdf`, p. 3, §2.1, 3.er párrafo (columna derecha, 1.ª línea) y ecuación (2) con su definición.
- **Citas textuales**: Fernandina: *"MIR and TIR bands were resampled to a regular 51 × 51 km UTM grid centered on the volcano summit"*. Coppola 2023: *"(for resampled MODIS image A_pix = 10^6 m)"* (sic, "m" por "m²").
- **Qué dice**: Fernandina da la extensión de la grilla (51 × 51 **km**) para MODIS y VIIRS juntos, sin tamaño de celda. Coppola 2023 da el área de celda sólo para MODIS (1 km²). Para I-band (375 m) y M-band (750 m) el tamaño de celda de la grilla MIROVA no aparece en ninguno. Tabla 1 de Fernandina (p. 5) sólo da "Pixel res. at nadir" 1 km, 0,75 km y 0,375 km.
- **Responde a**: D17 (magnitud por gradiente cenital en VIIRS375 y VIIRS750), `CLAUDE.md` del proyecto (reglas científicas: "MIROVA usa **A_pix nadir fijo** ... para los 3 sensores") y la pregunta 6 del correo, que hoy da por contestado el remuestreo VIIRS (`BORRADOR_CORREO_COPPOLA.md:36`; y `LECTURA_PDF_TABLAS_FIGURAS.md` H12 dice que Fernandina "contesta las dos mitades").
- **Veredicto**: **matiza** a H12 de S139: contesta la extensión y el centro, **no** el área de celda VIIRS. Los coeficientes empíricos S14 para VIIRS (18,0 y 19,7 con área nadir) son compatibles con celdas de 375 m y 750 m, pero eso es inferencia del repo, no texto del grupo. Tamaño de celda VIIRS: **SIN LOCALIZAR** (probablemente en Campus 2022, cita [66] de Fernandina, que no leí).
- **Confianza**: 5 (ausencia verificada en las dos páginas renderizadas). **Gravedad**: 3.

### B-05. Coppola 2023 confirma el ROI de cumbre como área de 5 × 5 km con umbrales algo más bajos, y umbrales algo más altos a mayor distancia

- **Localizador**: `feart-11-1240107.pdf`, p. 3, §2.1, 3.er párrafo, columna derecha, líneas 9 a 15.
- **Cita textual**: *"in the summit area (5 × 5 km) slightly lower thresholds are applied to detect the smallest thermal anomalies"* y *"At greater distances, the algorithm uses slightly higher thresholds which reduce false alerts"*.
- **Qué dice**: en 2023 el esquema dual-ROI sigue vigente y el ROI1 sigue siendo un área de 5 × 5 km. No da valores numéricos ni la forma (caja o disco), aunque "5 × 5 km" implica caja. La justificación declarada del ROI2 con umbral más alto es reducir falsas alertas.
- **Responde a**: D18 (`docs/MIROVA_DIVERGENCES.md:1975`, caja de 5 km contra círculo de 3 a 20 km) y a la mitad ROI1 de la pregunta 6 del correo ("is ROI1 still a fixed 5 by 5 km box?").
- **Veredicto**: **confirma** D18 con un texto del grupo 7 años posterior a SP426.5. Relevante para la sobre-publicación: un `inner_radius_km` de 5 a 20 km aplica umbrales de cumbre (más bajos) sobre un área mucho mayor que los 25 km² del paper, que es donde el grupo dice que usa umbrales más altos "which reduce false alerts". La pregunta 6 puede acortarse a sólo el bow tie y el tamaño de celda VIIRS (B-01, B-04).
- **Confianza**: 5. **Gravedad**: 3.

### B-06. El fondo de la magnitud se calcula "generalmente" de los píxeles que rodean la anomalía, y la base v.1 publica la suma de fondos de todos los píxeles alertados

- **Localizador**: `feart-11-1240107.pdf`, p. 3, §2.2, ecuación (1) y el párrafo que la define (columna derecha); p. 6, Tabla 1, fila `Tot_Lmir_bk`. Contraste: `Rapid_Response_...pdf`, p. 9, ecuación (3).
- **Citas textuales**: Coppola 2023 ec. (1), impresa con paréntesis: ΔL_MIR = Σ_{i=1}^{Npix} (L_MIR,hot(i) − L_MIR,bk), y *"L_MIR,bk is the background radiance, generally calculated from pixel(s) surrounding the anomaly"*. Tabla 1: *"Sum of MIR background radiance from all alerted pixels"*.
- **Qué dice**: (1) el fondo sale de los píxeles que rodean la anomalía, con un "generally" que admite excepciones; (2) la resta es por píxel (paréntesis dentro de la suma); (3) el campo `Tot_Lmir_bk` de la base v.1 es una **suma sobre los píxeles alertados**, es decir, del orden de Npix × L_bk. En Fernandina la ec. (3) está impresa **sin** paréntesis (Σ L_MIRhot(i) − L_MIRbk), que leída al pie de la letra restaría el fondo una sola vez; la versión 2023 con paréntesis decide que es por píxel, y la tabla lo corrobora.
- **Responde a**: D25 (`docs/MIROVA_DIVERGENCES.md:2254`, mediana de anillo de 5 a 25 km contra media de los vecinos) y a la tarea T7 de S140 (`pipeline/process_modis.py:1513`: "fondo en radiancia ... para comparar con Tot_Lmir_bk de MIROVA").
- **Veredicto**: **confirma** D25 (vecinos, no anillo regional) y **matiza** la comparación de T7: nuestro `diag_L_bg_w_m2_sr_um` es una radiancia de fondo única; `Tot_Lmir_bk` es una suma por píxel alertado. Comparar ambos exige dividir `Tot_Lmir_bk` por `Npix` (o multiplicar el nuestro por el número de píxeles). Si el esquema v2.5 que se usa conserva esta definición es **SOSPECHA** (no lo verifiqué en el CSV). El "generally" no dice cuándo se usa otra cosa: **SIN LOCALIZAR**.
- **Confianza**: 5 en las citas; 4 en la lectura por píxel. **Gravedad**: 3.

### B-07. Coppola 2023 cita la precisión del VRP de MODIS como "above ~1 MW"

- **Localizador**: `feart-11-1240107.pdf`, p. 4, §2.3 (continuación), columna izquierda, 3.er párrafo ("It is therefore important to emphasize...").
- **Cita textual**: *"In the case of MODIS with a resolution of 1 km, accurate values of VRP can be detected above ~1 MW (Coppola et al., 2016a)"*.
- **Qué dice**: el límite es de **exactitud** del valor para MODIS, equivalente a un emisor de radio ~1,5 m a 1.000 °C o ~6,9 m a 330 °C. Es un límite de lo que el sistema mide bien, no una compuerta de publicación declarada.
- **Responde a**: la sobre-publicación y a la decisión S130 de sacar el piso VRP (`MEMORY.md`, S130 "piso VRP fuera"); también a la prioridad de memoria "FN subpíxel <0.5 MW aceptables".
- **Veredicto**: **matiza**. No autoriza un piso de 1 MW (el paper no dice que MIROVA descarte lo que está bajo 1 MW, y las ALERTAS de MIROVA en Chile incluyen valores menores). Sí es cita del grupo para decir que un VRP MODIS bajo ~1 MW es de baja exactitud, útil para rotular o para no sobreinterpretar magnitud. No dice nada de VIIRS.
- **Confianza**: 5. **Gravedad**: 3.

### B-08. Coppola 2023 describe el TIR de MIROVA a 12,02 µm (banda 32); Fernandina 2025 dice B31

- **Localizador**: `feart-11-1240107.pdf`, p. 3, §2.1, 3.er párrafo, columna izquierda, penúltimas líneas. Contraste: `Rapid_Response_...pdf`, p. 5, Tabla 1 (MODIS "21 22 31", 10.78 a 11.28 µm), ya leído en S139 H8.
- **Cita textual**: *"the Middle InfraRed (MIR [guion] 3.959 µm) and the Thermal InfraRed (TIR [guion] 12.02 µm) data matrices are first extracted"* (el original separa sigla y longitud de onda con un guion largo; lo reemplacé por "[guion]" para cumplir la regla de estilo del repo).
- **Qué dice**: en 2023 el grupo sigue escribiendo 12,02 µm (banda 32); en 2025 escribe B31.
- **Responde a**: D20 (`docs/MIROVA_DIVERGENCES.md:2150-2154`, nota S140: "el grupo MIROVA describe hoy la banda 31 ... La divergencia queda sólo contra SP426.5").
- **Veredicto**: **contradice parcialmente** la nota S140: la divergencia no queda sólo contra SP426.5 de 2016; un paper del grupo de 2023, que describe la base v.1 de MODIS, dice 12,02 µm. Puede ser que el archivo histórico use la 32 y el NRT de 2025 la 31, o que uno de los dos textos esté mal: no se resuelve con estos papers. No cambia el código (efecto despreciable, S128).
- **Confianza**: 5. **Gravedad**: 2.

### B-09. La base v.1 define Lat/Lon como el píxel alertado más caliente y `max Dist` como el más lejano; no hay columna "class"

- **Localizador**: `feart-11-1240107.pdf`, p. 6, Tabla 1 "List of parameters distributed for each volcano. MIROVA Database v1", filas `Lat`, `Lon`, `max Dist`, `SatZen`, `Dayflag`.
- **Citas textuales**: *"Latitude of the hottest alerted pixel"*; *"Distance of the alerted pixel furthest from the volcano summit"*.
- **Qué dice**: 13 campos: UTC, Dayflag, Sensor (1 Terra, 2 Aqua), Resolution, SatZen, SatAzi, Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP, Lat, Lon, max Dist. La distancia se mide desde "the volcano summit". No existe columna "class". La base guarda `SatZen` por detección, pero el texto (p. 4) no dice que se use para filtrar.
- **Responde a**: pregunta 11 del correo (`BORRADOR_CORREO_COPPOLA.md:45-46`) y pregunta 8 (`:40`, columna "class").
- **Veredicto**: **confirma** el esquema que usa `docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md:148` para v2.5, ahora con texto del grupo para v.1. La pregunta 11 queda contestada **para el archivo**; qué distancia muestra la **página web** sigue **SIN LOCALIZAR**. "class" no existía en v.1: es una columna posterior y la pregunta 8 sigue abierta.
- **Confianza**: 5. **Gravedad**: 2.

### B-10. Los rankings de la base v.1 muestran siete volcanes chilenos; Tupungatito, Lastarria, Planchón-Peteroa e Isluga no se ven

- **Localizador**: `feart-11-1240107.pdf`, p. 8, figura 4C (persistencia) y p. 9, figura 5C (VRPmax); p. 12, figura 7C (Nevados de Chillán).
- **Cita textual** (leyenda figura 4): *"(C) Ranking of volcanoes sorted by the persistence of activity"*.
- **Qué dice**: en las etiquetas del eje x leo Lascar, Villarrica, Chaitén, Copahue, "Chillán, N", "Puyehue-Co" y Llaima. Lectura aproximada de barras de la figura 4C: Láscar ~84 %, Villarrica ~62 %, Chaitén ~48 %, Copahue ~19 %, Chillán N ~11 %, Puyehue-Co ~9 %, Llaima ~5 %. No encontré Tupungatito, Lastarria, Planchón-Peteroa ni Isluga. La figura 7C pone a Nevados de Chillán entre los domos andesíticos con "excess of VRE". Las planillas del suplemento 2019 (B-15) dan 15 blancos MIROVA en Chile.
- **Responde a**: pregunta 9 del correo (`BORRADOR_CORREO_COPPOLA.md:42`, Tupungatito ausente del archivo) y a D3.
- **Veredicto**: **matiza** la pregunta 9: la ausencia de Tupungatito ya se ve en la base v.1 de 2023, junto con otros tres Tier A. **SOSPECHA**: que las figuras 4C y 5C listen los 111 volcanes (no conté las etiquetas; puede haber volcanes sin barras), y los porcentajes son lectura de ojo de un gráfico.
- **Confianza**: 3. **Gravedad**: 2.

### B-11. Las series web se entregan "as-are", sin corrección atmosférica ni fracción de nube; el filtro de nube de la base es un filtro de mínimos locales, no supervisado

- **Localizador**: `feart-11-1240107.pdf`, p. 4, §2.5 (columna derecha, 1.ª mitad) y §2.4 "Method-2" (columna derecha, 3.er párrafo).
- **Citas textuales**: *"the VRP data provided by MIROVA are provided "as-are", i.e., without atmospheric corrections and cloud fraction estimates"*; *"by applying a local minima filter to the original VRP time series of each volcano"*.
- **Qué dice**: MIROVA no estima nube por pasada en lo que publica; para energía (VRE) de la base usa un filtro de mínimos locales sobre la serie, y el grupo lo llama "unsupervised".
- **Responde a**: D14 (máscara de nube BT < 260 K, cerrada S128) y a la nota de memoria de supervisión (ya citaba "as-are", S139).
- **Veredicto**: **confirma**. Ninguna compuerta de nube por pasada en el MIROVA descrito; el filtro de mínimos locales actúa sobre VRE semanal, no sobre detecciones.
- **Confianza**: 5. **Gravedad**: 2.

### B-12. La ecuación de alfa de Fernandina viene de Aveni 2023 (MERSI-II), y en 2023 el grupo sigue imprimiendo 18,9 para MODIS

- **Localizador**: `Rapid_Response_...pdf`, p. 9, ecuación (2) y la frase que la introduce ("According to [58]"); referencia 58 en la lista de referencias (p. 24, por capa de texto). `feart-11-1240107.pdf`, p. 3, ecuación (2).
- **Citas textuales**: Fernandina: *"According to [58], the value of α can be computed for any MIR channel as follows"*; ref. 58: *"Aveni, S.; Laiolo, M.; Campus, A.; Massimetti, F.; Coppola, D. The capabilities of FY-3D/MERSI-II sensor..."*. Coppola 2023: VRP = A_pix · 18.9 · ΔL_MIR, *"18.9 is a best-fit, wavelength-dependent regression coefficient"*.
- **Qué dice**: la fórmula cerrada de alfa que S139 H2 atribuye a Coppola 2025 es de Aveni et al. 2023, Remote Sens. 15, 2528 (hay un PDF local, `documentacion/The_Capabilities_of_FY-3DMERSI-II_Sensor_to_Detect.pdf`, que no leí). Y el paper de 2023 mantiene 18,9 para MODIS, no el 19,147 que da la fórmula.
- **Responde a**: `LECTURA_PDF_TABLAS_FIGURAS.md` H2 y a los coeficientes de `CLAUDE.md` del proyecto (reglas científicas, MODIS 18,9).
- **Veredicto**: **confirma** el 18,9 MODIS con texto del grupo de 2023 (y refuerza que la diferencia de 1,3 % de H2 no pide cambio) y **matiza** la atribución de H2: la autoridad primaria de alfa es Aveni 2023.
- **Confianza**: 5 en las citas; 4 en la identificación del PDF local (sólo por nombre de archivo). **Gravedad**: 2.

### B-13. La posición del cráter y del frente en el producto de Fernandina es "subject to supervision", con error de ±1 píxel por la dispersión del PSF

- **Localizador**: `Rapid_Response_...pdf`, p. 10, §2.3.1, párrafo "Vent location, Active flow length (Lhot) and velocity (vhot)".
- **Cita textual**: *"can be estimated at a pixel-level accuracy (from 0.375 to 1 km; Table 1), subject to supervision"* y *"even a small hot component lets the overall MIR pixel-integrated radiance rise exponentially and spread across adjacent pixels"*.
- **Qué dice**: la ubicación del cráter se fija al inicio "manually", y todo píxel caliente puede contagiar a los vecinos por el PSF, de ahí ±1 píxel.
- **Responde a**: D19 (`docs/MIROVA_DIVERGENCES.md:2062`, `keep_peak` publica un píxel de borde en 0,0 km) y A61 (eje espacial).
- **Veredicto**: **matiza**. El grupo trata la posición MIR como aproximada a ±1 píxel y supervisada; la precisión espacial sub-píxel no es algo que MIROVA declare. No aporta regla para D19.
- **Confianza**: 5. **Gravedad**: 2.

### B-14. rs2019 (MOUNTS) describe a MIROVA sólo con MODIS, algoritmo contextual, latencia < 4 h y 215 volcanes; no trae umbrales MIR

- **Localizador**: `rs11131528.pdf`, p. 3, §2.1, 3.er párrafo; p. 5, Tabla 1, fila MIROVA; p. 12, §3.3.2, 2.º párrafo.
- **Citas textuales**: p. 3: *"developed by the University of Torino and the University of Firenze [43]. It currently monitors 215 volcanoes"*; p. 12: *"It is based on fixed ratios between SWIR bands, and on a contextual threshold derived from a statistical distribution of the thermal anomaly clusters"* (algoritmo SWIR de Sentinel-2, no el de MIROVA).
- **Qué dice**: Tabla 1: MIROVA, Aqua/Terra MODIS, MIR-TIR, 1 km, "contextual algorithm [43]", productos "VRP (timeseries)", "NTI (map)", "TADR (timeseries, offline)", "< 4 h", 215 volcanes. El único algoritmo térmico detallado es el SWIR de Sentinel-2 (HOTMAP mejorado), comparado con el VRP de MIROVA en las figuras 5d y 9c.
- **Responde a**: contexto de A77 (SWIR alta resolución para focos sub-píxel); a ninguna divergencia D17 a D29.
- **Veredicto**: sin impacto sobre umbrales. Confirma afiliación Torino y Firenze de MIROVA.
- **Confianza**: 5. **Gravedad**: 1.

### B-15. Planillas del suplemento Coppola 2019: Chile tenía 15 blancos MIROVA y SERNAGEOMIN usaba MIROVA, MODVOLC y FIRMS

- **Localizador**:
  - `Coppola_2019_supp_Table2.xlsx`, hoja `Table2`, fila 2 (Chile), columnas A a F; fila 19 (Total) con fórmulas `=SUM(E2:E18)` y `=SUM(F2:F18)` (sin valor calculado guardado); celda B6 con un comentario de revisión.
  - `Coppola_2019_supp_Table1.xlsx`, hoja `Table1`, fila 10 (MIROVA), columnas A a L; fila 18 (MOUNTS).
- **Cita textual** (Table2 fila 2): `Chile | Servicio Nacional de Geologia y Mineria | SERNAGEOMIN | MIROVA, MODVOLC, FIRMS | 99 | 15`.
- **Qué dice**:
  - **Table1** (columnas: Developper, System, Sensor, Bands, Spatial resolution, Temporal resolution, Coverage, Website, Images, VRP, Timeseries, Reference): 17 sistemas térmicos. Fila 10: `UNITO | MIROVA | MODIS | MIR, TIR | ~ 1 km | 6-12 h | Specific Targets - Global scale | http://www.mirovaweb.it/ | x | x | x | Coppola et al., 2016`. Ningún umbral.
  - **Table2** (columnas: Country, Observatory/Institution, Acronym, Thermal system, holocene volcanoes, MIROVA targets): 17 instituciones de 14 países. Chile: 99 volcanes holocenos, **15 blancos MIROVA**. El comentario de B6 ("Institut de Physique du Globe de Paris", firmado por Aline Peltier, 2019-07-15) es una corrección de nombre, sin contenido técnico.
- **Responde a**: pregunta 9 del correo y a D3 (cobertura de volcanes chilenos), en el contexto de nuestros 11 Tier A.
- **Veredicto**: dato de contexto. La planilla no lista cuáles son los 15, así que no permite decir si Tupungatito era blanco en 2019 (**SIN LOCALIZAR**). En 2019 MIROVA se describía como sólo MODIS.
- **Confianza**: 5. **Gravedad**: 1.

---

## VERIFICADO LIMPIO (lo que busqué y no estaba)

Revisé la capa de texto completa de los tres PDF (con búsqueda de términos: K1, C1, C2, sigma, threshold, ETI, dNTI, saturat, B22, zenith, cloud, bow, resampl, "false alert", nombres de volcanes chilenos) y miré como imagen las páginas con fórmulas, tablas y figuras con parámetros: Fernandina p. 5, 8, 9, 10, 12, 13, 21; Coppola 2023 p. 3, 4, 5, 6, 8, 9, 12; rs2019 p. 5, 6, 12.

| busqué | resultado | páginas donde debería estar si existiera |
|---|---|---|
| Conectiva de los Tests 2 y 3 (min o max, and u or) | **ausente** en los tres. Fernandina remite a [62, 66] (SP426.5 y Campus 2022) sin describirla | Fernandina p. 9 §2.3.1; Coppola 2023 p. 3 §2.1 |
| Valores de K1, C1, C2, N·sigma, Tabla de umbrales por sensor | **ausentes**. Coppola 2023 sólo dice "slightly lower" y "slightly higher" (B-05) | Coppola 2023 p. 3; Fernandina p. 9 |
| Definición o ecuación del ETI, NTIbk, regresión cuadrática, refit iterativo (D29) | **ausentes**. El ETI sólo se nombra (Coppola 2023 p. 3, con cita a Coppola 2016a) | Coppola 2023 p. 3 |
| Compuerta de temperatura BT > fondo + k (D22) | **ausente** | Coppola 2023 p. 3; Fernandina p. 9 |
| Banda 22 primaria o 21 en saturación (D21) | Coppola 2023 p. 3 sólo dice "dual channel ... centred at 3.959 µm" con ganancia baja y alta, sin regla de selección; Fernandina p. 6 ingiere B21 y B22 sin regla | Coppola 2023 p. 3; Fernandina p. 5 y 6 |
| Tratamiento de píxeles saturados DN 65533 (D24) | **ausente** | Coppola 2023 p. 3 |
| Test 1 como camino propio (D23) | **ausente** | idem |
| Mu y sigma del segundo pase, filtros de no aptos (D26) | **ausente** | idem |
| Umbrales diurnos o uso de pasadas diurnas (D27) | Coppola 2023 p. 4: la base v.1 es "exclusively of night-time data"; ningún umbral diurno | Coppola 2023 p. 4, p. 6 (Dayflag) |
| Compuerta automática por ángulo cenital | **ausente** en el sistema automático; sólo exclusión supervisada (B-02) | Fernandina p. 9, 12, 13, 21; Coppola 2023 p. 4 y 6 |
| Tamaño de celda de la grilla para VIIRS | **ausente** (B-04) | Fernandina p. 9; Coppola 2023 no trata VIIRS |
| Forma del ROI1 (caja o disco) de forma explícita | sólo "summit area (5 × 5 km)" (B-05) | Coppola 2023 p. 3 |
| Columna "class" del archivo | **ausente** en la Tabla 1 de v.1 (B-09) | Coppola 2023 p. 6 |
| Distancia que muestra la página web (pregunta 11) | **ausente**; sólo la del archivo (B-09) | Coppola 2023 p. 6 |
| Tupungatito, Lastarria, Planchón-Peteroa, Isluga | 0 apariciones en la capa de texto de los tres PDF; no visibles en las figuras 4C y 5C de Coppola 2023 (B-10) | Coppola 2023 p. 8, 9 |
| Umbrales MIR, parámetros de fondo o ROI en rs2019 | **ausentes**: el único algoritmo térmico descrito es SWIR de Sentinel-2 | rs2019 p. 3 a 6, 12, 13 |
| Umbrales o volcanes concretos en las planillas 2019 | **ausentes**: Table1 es un catálogo de sistemas y Table2 de observatorios, sin nombres de volcanes | ambas hojas completas |
| Ecuaciones con operadores corrompidos | Fernandina y Coppola 2023 miradas como imagen en p. 9 y p. 3: sin discrepancia con la capa de texto en los operadores citados. Sí hay una ambigüedad tipográfica real (ec. 3 de Fernandina sin paréntesis, B-06) y una errata de unidad (A_pix = 10^6 "m", B-04) | Fernandina p. 9; Coppola 2023 p. 3 |
