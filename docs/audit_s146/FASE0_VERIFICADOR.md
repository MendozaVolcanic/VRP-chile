# Fase 0, verificador con contexto limpio: las marcas de rebaja en los tres documentos rectores

Fecha: 2026-09-20. Rol: intentar romper las ediciones sin commitear de `CLAUDE.md`, `docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md`, `experiments/_s145_censo_cierres/censo.py` y `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`. No edité ningún archivo existente ni usé git para escribir. Scripts propios en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\verificador_fase0\` (`f0_forma.py`, `f0_forma2.py`, `f0_mutar_censo.py`). Cada hallazgo lleva pegada la línea del diff y la línea de la fuente, las dos salidas de herramienta de esta sesión.

## 1. Cobertura, primero

| qué | universo | cubierto | cómo |
|---|---|---|---|
| Marcas nuevas | 42 (10 en `CLAUDE.md`, 5 en `MISSION.md`, 25 en el catálogo, 1 en el borrador, 1 en `censo.py`) | 42 | cada número contra `docs/AUDIT_S146.md`, `VERIFICADOR_CONTEXTO_LIMPIO.md`, `FASE1_SUSTRATO_SOBREPUBLICACION.md`, y los frentes A, C y E donde la marca los cita |
| Citas `archivo:línea` nuevas | 17 | 17 | abiertas con `sed -n` |
| Flags citados | 10 | 10 | leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` |
| Forma (texto viejo conservado, guiones, voseo) | 5 archivos | 5 | script sobre `git diff -U0` |
| Control de `censo.py` | 1 | 1 | 8 mutantes sobre copias en directorio temporal, md5 del original antes y después |
| Propagación | 3 rectores más 6 secundarios | grep por identificador y el grafo del frente E | ver sección 4 |
| Tests que leen estos documentos | 7 archivos | 7 | `98 passed, 2 xfailed` |

Lo que NO cubrí: no re-corrí los scripts de medición del verificador anterior ni los de la Fase 1 (comparé texto contra texto, que era el encargo); no abrí el PDF de SP426.5 (las citas verbatim de D30 y D31 las cotejé contra lo que el verificador anterior dejó pegado, no contra la página); no consulté Crossref ni OpenAlex; `docs/META_RULES_S80.md` y `README.md` sólo por grep (cero coincidencias); no corrí la suite completa.

## 2. Hallazgos que piden corrección, por gravedad

### H-01 (gravedad 4, confianza alta). `CLAUDE.md` y `MISSION.md` dicen que el test de temperatura de brillo está «SIN MEDIR», y D31 del catálogo, escrita el mismo día, dice que está APAGADO con sustrato CERO

Diff, `CLAUDE.md`:
```
+  que A69 marca como vulnerable al gradiente topográfico (cuánto decide hoy: SIN MEDIR).
```
Diff, `docs/MIROVA_DIVERGENCES.md` (D31):
```
+**El camino está APAGADO hoy: la divergencia es de atribución, no de comportamiento.**
+- El contador `diag_n_bt_path` vale **0 en las 2.360 pasadas nocturnas** de la ventana
```
Mi comprobación:
```
ENABLE_BT_PATH_HOT False
pipeline/process_viirs.py:997:            if not ENABLE_BT_PATH_HOT:
pipeline/profiles/mirova_equivalent.yaml:414:  enable_bt_path_hot: false
1b0c3bdb5 2026-05-13 S40 ADOPCIÓN operacional: bt_path_hot OFF
Villarrica, diag_n_bt_path > 0 por mes: 2026-04 [331, 0] ... 2026-09 [229, 0]
```
El «SIN MEDIR» es del V-08, anterior a la Fase 1. Quien lea `CLAUDE.md` o `MISSION.md` (que se leen primero) se lleva que hay un camino de BT absoluta activo y vulnerable a la topografía; quien llegue a D31 se lleva que está apagado desde S40. Es justo el defecto que A113 describe, cometido en el mismo PR. La marca de `MISSION.md` sobre el 5 / 10 tampoco dice que el camino está apagado.

Texto corregido para `CLAUDE.md` (reemplaza el paréntesis): «(cuánto decide hoy: **nada**, el camino está apagado desde S40, `ENABLE_BT_PATH_HOT = False` leído de `pipeline.profile`, comprobado por la Fase 1 de S146 y por su verificador; la divergencia es de atribución, no de comportamiento, ver D31)».
Texto a agregar al final de la marca V-08 de `MISSION.md`: «El camino de BT está apagado hoy (`ENABLE_BT_PATH_HOT = False`); lo que cae es la atribución a la Tabla 1, ver D31 en el catálogo.»

### H-02 (gravedad 3, confianza alta). La marca de A23 dice «esta regla vuelve a ser trabajo vivo», y A23 manda correr tres alternativas de las que el catálogo, en el mismo PR, mantiene una descartada y otra ya adoptada

Diff, `CLAUDE.md`:
```
+- **A23. ⚠️ La declaración de obsolescencia cayó S146 (AUDIT_S146 V-01): D9 NO está cerrada y esta
+  regla vuelve a ser trabajo vivo.**
```
Texto viejo de A23 que queda reactivado: «A/B test 3 alternativas (gate atm `t_bg ≥260K`, co-validación obligatoria, cap magnitud)».
Diff, catálogo:
```
+> `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`. Lo que **no** se reabre es el gate por `t_bg` (sigue
+> descartado: es anti-MIROVA, Coppola 2016a §247 y 2023 §554) ni el tope de 5 MW, que funciona.
```
Fuente (V-01): «el argumento con que se descartó para siempre cualquier co-validación del path D en fondo frío [...] no tiene respaldo». Sólo la co-validación. La marca de `CLAUDE.md` reabre más de lo que la auditoría sostiene: es una rebaja exagerada.

Texto corregido: «**A23. ⚠️ La declaración de obsolescencia cayó en parte, S146 (AUDIT_S146 V-01): D9 vuelve a estar abierta SÓLO en la cara de co-validación del path D sobre fondo frío. De las tres alternativas que esta regla manda probar, sigue descartado el gate por `t_bg` (anti-MIROVA) y el tope de magnitud ya está adoptado y funciona; lo único vivo es la co-validación (Fase 3 del plan).**»

### H-03 (gravedad 3, confianza alta). La marca de D9 en el catálogo no recoge lo que la Fase 1 midió sobre ese mismo camino, y D30, escrita al lado, sí lo recoge

Diff, catálogo:
```
+(medido, A/B propio) y sigue descartado el gate por `t_bg`. La acción abierta es la **Opción 2
+(co-validación)**, con su sustrato re-medido en el régimen actual: Fase 3 de
```
Fuente, Fase 1 §8 y §9:
```
- **Camino contextual sobre fondo frío con tope de 5 MW (D9):** como camino separado no existe en la máscara actual (el `dnti_ctx` legacy es diagnóstico). Lo que existe es el tope, que sólo actúa en MODIS.
| co-validación del contextual en fondo frío (Fase 3) | bajo en V375 y en MODIS, medio en V750 |
```
y el código: `process_viirs.py:1237  # Paths legacy se calcularon arriba (diag) pero no contribuyen cuando ON.`
La marca deja a D9 «REABIERTA» sin avisar que, según la única medición del régimen actual (todavía sin verificar), el path D ya no entra a la máscara y el sustrato de la co-validación es bajo. No contradice, pero omite el dato que decide cuánto vale reabrir.

Texto a agregar al final del párrafo «Estado D9 (actualizado S146)»: «Adelanto de la Fase 1 (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` §7 a §9, hallazgo del que midió, sin verificador todavía): en el régimen actual el `dnti_ctx` legacy es sólo diagnóstico y no entra a la máscara, el tope de 5 MW actúa sólo en MODIS, y el sustrato de un brazo de co-validación es bajo en VIIRS 375 y MODIS y medio en VIIRS 750. Reabierta no quiere decir prioritaria.»

### H-04 (gravedad 3, confianza alta). Propagación incompleta dentro del propio catálogo: el «90 % pipeline-cráter» de D11 y el encabezado de D11 quedaron sin la rebaja V-02 que sí se puso en `CLAUDE.md` y `MISSION.md`

```
docs/MIROVA_DIVERGENCES.md:1391  ## D11 ... **CERRADA S114, CONDICIONADA S138** (...)          [sin S146]
docs/MIROVA_DIVERGENCES.md:1437  re-auditoría por sensor con data fresca destapó que el recall dashboard MODIS es 16% (vs 90%
docs/MIROVA_DIVERGENCES.md:1438  pipeline-cráter) = bug de etiquetado A46 far→summit
awk de la sección D11 (l. 1391 a 1530) buscando "S146": 0 líneas
```
En la misma sección, la l. 1447 a 1449 repite «la detección MODIS YA es FIEL a Coppola 2016a (dual-ROI 5/10 enable_dual_roi_bt ...)» sin la marca V-08.

Texto a insertar bajo el encabezado de D11 (l. 1391): «> ⚠️ **S146 (AUDIT_S146 V-02 y V-08).** El «90 % pipeline-cráter» del cierre S114 de abajo no tiene tasa base: con negativos limpios hay cúmulo con magnitud dentro del inner en 89,1 % de 4.800 pasadas MODIS, contra 93,7 % de 158 cuando MIROVA alertó (ventana 2026-01-29 a 2026-08-28; 144 de las 158 positivas son de Láscar). Mide presencia de cúmulo, no detección. Y el «dual-ROI 5/10» que el mismo bloque cita como fidelidad no está en la Tabla 1 (ver D31). Texto original intacto abajo, conservado por historia.»

### H-05 (gravedad 3, confianza alta). `MISSION.md` sigue listando D5 como resuelta, sin marca; la marca nueva cubre D9, D4 y D8 pero no D5

Diff (la marca nombra sólo tres): `**D9 no está cerrada** ... **D4** se apoya ... **D8** sigue vigente`.
Texto que queda sin marca: `D5 magnitud (nadir S102/103 + ctxpeak D10 S100)`.
Fuentes: `AUDIT_S146.md` §2, fila 1: «catálogo: D5 abierta con signo opuesto»; E-06: «D5 magnitud ... Contra `MIROVA_DIVERGENCES.md:131-137`: "Rebajada de calibración lograda a **abierta pendiente de re-medición**"»; y el catálogo hoy, l. 135-136: «Rebajada de "calibración lograda" a **abierta pendiente de re-medición**».

Texto a agregar dentro de la marca, antes de «Lo que sigue se conserva por historia»: «**D5 tampoco está resuelta**: el catálogo la tiene desde S125 como «abierta pendiente de re-medición», con el signo opuesto (sub-reporte cerca de 0,75 y no sobre-reporte de 1,35), y sus dos patas están rebajadas (nadir fijo no es el remuestreo, A66; `keep_peak` daba paridad por accidente, A100) (AUDIT_S146 §2 y E-06).»

### H-06 (gravedad 2, confianza alta). D31 cita `detection_context.py:997`; la línea está en `process_viirs.py:997`

Diff: `+  'detection_context.py:997' la pone en cero`.
```
pipeline/detection_context.py:997:  ) -> np.ndarray:            (fin de una firma)
pipeline/process_viirs.py:997:            if not ENABLE_BT_PATH_HOT:
pipeline/process_modis.py:660 / pipeline/process_viirs_mod.py:640: idem
```
La Fase 1 decía «la l. 997» sin archivo, dentro de un párrafo sobre `process_viirs.py`. Texto corregido: «pero `process_viirs.py:997` la pone en cero (lo mismo en `process_modis.py:660` y `process_viirs_mod.py:640`)».

### H-07 (gravedad 2, confianza alta). Las dos citas nuevas «l. 1319-1335 de este mismo archivo» quedaron corridas por las propias inserciones; la de «l. 294» tampoco apunta

```
HEAD:  1318-1319  ... GAP #A RESUELTO S115 = mislabel ... REABIERTO S128
AHORA: 1450-1467  (mismo texto)
l. 478 y l. 489 nuevas citan "l. 1319-1335"
l. 274 nueva cita "(lo dice la l. 294)"; la frase «la Fase 1 leyó solo notas Vault» está hoy en la l. 306 (en HEAD, l. 295)
```
Es A101 aplicada a uno mismo: una cita por número de línea dentro del archivo que se está alargando nace rota. Texto corregido: reemplazar «(l. 1319-1335 de este mismo archivo)» por «(en este mismo archivo, bloque CIERRE S114 de D11, buscar «REABIERTO S128»)» en los dos lugares, y «(lo dice la l. 294)» por «(lo dice el «Trigger» de la sub-sección S71 de más abajo)».

### H-08 (gravedad 2, confianza alta). D-PCC: «se revirtió el mismo día» no es cierto; fue al día siguiente, dentro de la misma S62

Diff: encabezado `la adopción se revirtió el mismo día (S62, PR #85)` y nota `y, el mismo día, '5d2bea4b9'`.
```
fab02ec1c author=2026-05-18T22:41:16-04:00
5d2bea4b9 author=2026-05-19T07:37:18-04:00
```
El verificador anterior escribió «en la misma S62»; «el mismo día» viene de `AUDIT_S146.md` §2. Texto corregido: «se revirtió a las nueve horas, en la misma S62 (PR #85, 2026-05-19)» en el encabezado, y «y, a la mañana siguiente, `5d2bea4b9`» en la nota.

### H-09 (gravedad 2, confianza alta). D30 atribuye al auditor C de S146 una medición que es de S138, y no da la cifra de la ventana que ella misma usa

Diff: `+dominante ...: el auditor C de S146 midió 'triggered_test1' en el **77,89 %** ... **22,21 %**`.
Fuente, frente C l. 126-127: «`docs/audit_s138/EJE_2_matriz_conformidad_pdf.md:112` mide que `triggered_test1` vale en 77,89 % ...». El auditor C cita, no mide. En la ventana de la Fase 1 (misma D30) el crudo da `VIIRS375 n 954, triggered_test1 800` y `VIIRS750 n 949, triggered_test1 200`, o sea 83,9 % y 21,1 %.
Texto corregido: «S138 midió `triggered_test1` en el 77,89 % de los records VIIRS 375 y el 22,21 % de los VIIRS 750 (`docs/audit_s138/EJE_2_matriz_conformidad_pdf.md:112`, citado por el auditor C de S146; no pasó por el verificador). En la ventana de la Fase 1 son 800 de 954 (83,9 %) y 200 de 949 (21,1 %).»

### H-10 (gravedad 2, confianza alta). A113 da un desglose de los 50 que suma 49

Diff: `+  evidencia** (de los 50 «sin respaldo» del censo S145, 27 se verifican, 5 en parte, 7 se refutan y 10 no eran cierres)`.
Fuente, `AUDIT_S146.md` §1: «de los 50, 27 se verifican, 5 en parte, 1 queda sin evidencia, 7 se refutan y 10 no eran cierres».
Texto corregido: agregar «1 queda sin evidencia,» entre «5 en parte,» y «7 se refutan».

### H-11 (gravedad 2, confianza alta). Voseo en líneas AGREGADAS de A113

```
+  - **How to apply**: (a) cuando rebajes, refutes o matices una afirmación, en el **mismo PR** buscá
+    quién la cita (`grep` del número, de la frase y del ID) y marcá cada hijo, aunque el hijo esté en
```
Texto corregido: «busca quién la cita» y «marca cada hijo». Guiones largos o medios en líneas agregadas: sólo dentro de texto viejo re-emitido (A23, D11 de MISSION, filas y encabezados del catálogo), ninguno en texto nuevo. Limpio en eso.

### H-12 (gravedad 2, confianza alta). El control nuevo de `censo.py` sí puede fallar, pero no vigila el bucle que produce las filas ni los respaldos, y su comentario dice lo contrario

Mutantes sobre copias temporales (`f0_mutar_censo.py`; original intacto, md5 `85a383be...` antes y después):
```
M0 sin cambio                                   ok=True  n=107 sin_resp=62
M1 PATRONES vaciado                             ok=False n=0
M2 regex cerrada rota                           ok=False n=102
M3 detector de control invertido                ok=False
M4 detector del BUCLE PRINCIPAL invertido       ok=True  n=6569 sin_resp=4362   (SOBREVIVE)
M5 bucle principal solo mira 'cerrada'          ok=True  n=9                    (SOBREVIVE)
M6 RESPALDOS vaciado                            ok=True  n=107 sin_resp=107     (SOBREVIVE)
M7 patron que marca todo                        ok=False
todos: exit=0
```
Confirmado: el control puede fallar (4 de 7 mutantes lo tumban), así que V-14 queda resuelto en lo esencial. Tres matices: (a) el comentario agregado dice «corren el MISMO detector que usa el censo (la comprension de `PATRONES`, no una copia)», y `_tipos` ES una copia de la comprensión de la l. 93, por eso M4 y M5 sobreviven; (b) no hay caso positivo para `RESPALDOS` (M6 sobrevive y pone los 107 como «sin respaldo»); (c) el script devuelve 0 aunque `instrumento_ok` sea False.
Corrección: definir `_tipos` y un `_respaldos(ventana)` a nivel de módulo, usarlos en el bucle principal y en el control; agregar un tercer texto sintético con respaldo conocido (por ejemplo «CERRADA, ver `censo.py` y PR #535») y exigir `{"script", "pr"} <= respaldos`; terminar con `return 0 if instrumento_ok else 1`. Y cambiar el comentario a lo que de verdad hace.
Dato lateral (A90): con los tres documentos editados el censo da hoy 107 afirmaciones y 62 sin respaldo, contra 89 y 50 de S145, porque las marcas nuevas traen las palabras clave («CERRADA», «irreducible», «no reabrir»). El censo cuenta las rebajas como cierres.

### H-13 (gravedad 2, confianza media). La marca de A84 dice que el «irreducible» heredado «no sigue en pie»; la fuente lo deja condicionado, no caído

Diff: `+  frente A lo reprodujo; lo que no sigue en pie es el «irreducible» heredado.`
Fuente: V-02 «CONFIRMADO ... Esto toca la premisa de A82»; A82 en `CLAUDE.md`: «"irreducible" vale sólo bajo esa configuración». Ninguna fuente refuta el «irreducible»; le quita el respaldo. Texto corregido: «lo que queda sin respaldo, y condicionado igual que en A82, es el «irreducible» heredado.»

### H-14 (gravedad 2, confianza alta). D13: «se reproduce exacto 41 de 2.704», y once líneas más abajo el texto conservado dice 41 de 2.694

Diff: `+> Lo que se reproduce exacto: **41 de 2.704 (1,5 %)**`. Catálogo l. 1687 y 1694: «2.694 records», «41 de 2.694 (1,5 %)». Fuente V-10: «41 de 2.704 (1,5 %; S126 tenía 2.694, el corpus creció)».
Texto corregido: «Lo que se reproduce: **41 de 2.704 (1,5 %)** hoy (S126 tenía 41 de 2.694; el corpus creció, el porcentaje es el mismo)».

### H-15 (gravedad 2, confianza media). Borrador del correo: «sin necesidad de A/B» choca con lo que D30 pide medir

Diff, tabla del borrador: `+si la respuesta es «no», los dos caminos quedan fuera del clon literal sin necesidad de A/B`.
D30, mismo PR: «Lo que sigue abierto es cuánto de las 4 noches SIN DATO ... sobreviviría sin él ... Eso pide el probe». Y el cuerpo en inglés dice «two such steps exist in our implementation» cuando uno de los dos está apagado (H-01). Texto corregido de la fila: «si la respuesta es «no», queda resuelta la pregunta de fidelidad (los dos caminos son nuestros) sin necesidad de A/B; qué hacer con el Test 1 integrado sigue pidiendo la medición de recall de D30». Y en el inglés: «two such steps exist in our code (the second one currently disabled)».

### H-16 (gravedad 1, confianza alta). Números sin ventana o con poblaciones mezcladas en marcas que van a leerse por meses (A90)

- A82 (`CLAUDE.md`) y D11 (`MISSION.md`): 89,1 % y 93,7 % sin ventana. Fuente: `('2026-01-29', '2026-08-28')`, entera anterior a #535; en el tramo posterior el verificador midió `neg: n=500 crater=430 (86.0%) | pos n=2`. Agregar «(2026-01-29 a 2026-08-28; después de #535, 86,0 % de 500 negativos y sólo 2 positivos)».
- A23 y D9: «59 de 214» es la población de junio y «3 de cada 4 son VIIRS 750» es la de hoy (`población de hoy por sensor: v750 162, modis 38, v375 16`, n = 216). La mezcla viene del propio V-01. Agregar «(sensor medido sobre la población de hoy, 162 de 216)».
- A99: «1,39 en Villarrica» sin decir que son 8 pares (`Villarrica 8 1.386`); el extremo con muestra es Planchón Peteroa, 1,33 con 63. Agregar «(n = 8)». Tampoco dice que el pareo es contra el OSF de 2025, anterior a #535.
- D30: «`T1_SOBRE_CTX`: 56 en VIIRS 375, 11 en VIIRS 750» son sólo negativos limpios publicados; en positivos hay 23 más en VIIRS 375 (`"pos": {... "T1_SOBRE_CTX": 23 ...}`). Agregar «en negativos limpios publicados (más 23 en positivos de VIIRS 375)».

### H-17 (gravedad 1, confianza alta). «S128 ya había establecido, por hash» (D30 y marca de H_S27_1)

Fuente, `BIBLIOGRAPHY_SYNTHESIS.md:40-43`: «Re-verificado S128 (el PDF `coppola2015.pdf` ya no está en disco, así que el hash no se puede re-correr, pero la prueba sustantiva es más fuerte)». El hash es anterior a S128; S128 lo confirmó por contenido. Texto corregido: «El proyecto ya había establecido (por hash antes de S128, y por contenido en S128) que ...».

### H-18 (gravedad 1, confianza alta). «seis perfiles más» con la cita Gaua: son 23 más

Diff: `+> y seis perfiles más`. Medido: `grep -l "Gaua" pipeline/profiles/*.yaml | wc -l` da 24 de 73. El «seis» viene de V-07 y del plan. Texto corregido: «y otros 23 perfiles (24 de 73 con `grep -l Gaua`)».

### H-19 (gravedad 2, confianza alta). Mientras yo verificaba apareció `docs/audit_s146/FASE1_VERIFICADOR.md`: D30 y D31 dicen «todavía sin verificador» y D31 usa como prueba un contador que ese verificador declara muerto por construcción

Diff, D31: `+- El contador 'diag_n_bt_path' vale **0 en las 2.360 pasadas nocturnas** ... Ninguna excepción.`
Fuente nueva, `FASE1_VERIFICADOR.md` l. 97-105:
```
{"campos_presentes": {"diag_n_bt_path": 60112, "n_bt_path": 47928}, "n_records_con_bt>0": {}}
El flag es la evidencia buena. El contador **no** lo es: nunca fue mayor que cero en ningún record de ningún volcán de toda la historia del corpus ... el cero es **por construcción**
```
La conclusión de D31 (sustrato cero, no correr ese brazo) no cambia: la sostiene el flag. Pero el contador no es evidencia independiente, y la frase «sin verificador con contexto limpio todavía» de D30 y D31 quedó vieja el mismo día. No leí ese informe entero: sólo su tabla de veredictos (6 de 6 CONFIRMADO, 4 con matiz, gravedad máxima 2).
Texto corregido para la viñeta de D31: «El contador `diag_n_bt_path` vale 0 en las 2.360 pasadas de la ventana, pero eso **no es evidencia independiente**: con el flag en False el contador cuenta un arreglo de ceros, y nunca fue mayor que cero en ningún record del corpus (`docs/audit_s146/FASE1_VERIFICADOR.md` §4). La evidencia es el flag.» Y en D30 y D31, reemplazar «todavía sin verificador con contexto limpio» por «verificado en `docs/audit_s146/FASE1_VERIFICADOR.md`: confirmado con matiz, leer sus §5 y §6 antes de usar la banda 21,4 a 36,5 % y el 74 de 78 (por sensor, VIIRS 750 pierde 1 de 14 noches)». Quien integre debe cotejar los números de D30 contra ese informe; yo no lo hice.

## 3. Exageración: lo que revisé y está bien

Ninguna marca llama «refutado» a algo que la fuente deja «con matiz», salvo H-02 y H-13. Comprobado uno por uno que NO se apagó lo que la auditoría dejó sano: «D13 no es palanca» se sostiene y la marca lo dice («la conclusión se sostiene por otra vía», 92 noches, 1 con alerta); la conclusión práctica de A83 «sale reforzada» (textual en la marca); el tope de 5 MW «sí funciona» (A23, D9, `MISSION.md`, puntero de Estado); los denominadores 199 y 214 «se reproducen exactos»; A84 «sigue en pie y el frente A lo reprodujo»; D12 «el NO ADOPTAR no cambia»; D16 «todo lo factual se sostiene»; D20 «no cambia ninguna decisión hoy»; D30 «no dice que el Test 1 integrado esté mal ni que haya que apagarlo». D30 y D31 presentan la Fase 1 como «hallazgo del que midió, todavía sin verificador con contexto limpio», en los dos lugares donde la usan. «FALSO» aparece en tres marcas (NEW-8 desde S72, «Test 1 ES Coppola 2015», «serie continua») y en las tres la fuente lo sostiene (V-05 CONFIRMADO, V-06 CONFIRMADO más fuerte, V-15 con hueco en 10 de 11).

## 4. Propagación: apariciones que siguen diciendo lo viejo sin marca

Nuevas (hallazgo mío):

| dónde | qué dice | qué le falta |
|---|---|---|
| `docs/MIROVA_DIVERGENCES.md:1391` y `:1437-1438`, `:1447-1449` | D11 «CERRADA S114», «16% (vs 90% pipeline-cráter)», «dual-ROI 5/10 ... YA es FIEL» | V-02 y V-08 (H-04) |
| `docs/MISSION.md`, viñeta «Resueltas» | D5 magnitud resuelta | E-06 (H-05) |
| `docs/MIROVA_DIVERGENCES.md:776` (encabezado H_S27_1) y `:772, 779, 803, 827, 852, 892, 956, 1335` | «Test 1 integrated-ROI (Coppola 2015 §2.2 Eq.1)» | la marca V-06 está sólo en la l. 810, 34 líneas bajo el encabezado; A113 (b) pide marca al inicio del pasaje. La l. 1335 (D10) queda fuera del bloque |
| `docs/MIROVA_DIVERGENCES.md:1140` | «❌ NO ES DRIFT (S100) ... Código actual (flag OFF) ya fiel» | E-07 la lista (antes `:1028`); sin marca |
| `docs/MIROVA_DIVERGENCES.md:458` (fila F1.2) | «**Mantener OFF permanentemente.**» | la marca agregada en la celda habla de NEW-8 y del GAP #A pero no rebaja esa frase en el lugar |
| `docs/MIROVA_DIVERGENCES.md:2551` | «la razón de magnitud a igual conteo ya está en 0,995 (A99)» | V-12 la nombra (antes `:2331`) |
| `docs/MIROVA_DIVERGENCES.md:2452` (D21) | «ningún brazo cumple aún la batería» | `AUDIT_S146.md` §4: con la vara corregida el mejor brazo da 9 de 9. Es la raíz con más arrastre del grafo (E-08); no estaba en la tabla de la Fase 0 del plan |
| `docs/MIROVA_DIVERGENCES.md:1659` | «mueve el 31 % de la magnitud publicada» (cuerpo de D13, pegado a la marca nueva) | mismo pendiente conocido que el título |
| `CLAUDE.md` A76 (l. 900) y «Drift D3 RESUELTO» (reglas científicas, VRP TIR) | cita «~5 % tolerados, aleatorios en espacio/tiempo»; D3 apoyada en la Ec. 16 | C-05 y C-06, fila 12 de la Fase 0 del plan; sin marca |
| `CLAUDE.md` A81 | «73 de NdC = artefacto A69 (NO destapar)» | hija INFERIDA de A82 en el grafo; A113 no la nombra |
| `docs/HYPOTHESIS_LOG.md:468, 471, 890, 894-895` | «Coppola 2015 Eq.1 ... ¿En papers core? SÍ» | V-06 (0 menciones de S146 en el archivo) |
| `docs/HYPOTHESIS_LOG.md:1492, 1503` | «R 0,995 a igual número de píxeles (la fórmula está bien, falta selección)» | V-12 la nombra |
| `docs/INDEX.md:80` | «far→summit MODIS **irreducible** (A82); detección MODIS fiel a Coppola file:line» | sin marca |
| `tasks/BLOQUE_ARRANQUE_S146.md:95-97` | «No buscar un discriminante físico per-record ... A83 lo declaró agotado» | contradice la marca nueva de A83; que el bloque de S147 no lo copie |
| `docs/AUDIT_S121_D12_AB.md:19, 44` | «76 (reales)», «76 noches de FN recuperadas» | fila 7 de la Fase 0 del plan; 0 menciones de S146 |

Pendientes ya conocidos, confirmados SIN marca hoy: título de D13 «31 % de la magnitud» (`:1615`; `grep 70,7` en el catálogo da 0); `docs/AUDIT_S122_C2_PASO0.md` (0 menciones de S146; l. 1, 16, 56-59 «irreducible a 1 km», «76 noches reales de FN»); «Gaua» en `pipeline/profiles/mirova_equivalent.yaml:482` y 23 perfiles más; cabecera de `pipeline/test1_integrated.py:12-18` y `pipeline/process_modis.py:16`. `docs/FICHA_SDA_VRP_CHILE.md`, `docs/META_RULES_S80.md` y `README.md`: cero coincidencias de las frases viejas.

## 5. Contradicciones entre los tres documentos y coherencia de A113

- H-01 (BT «SIN MEDIR» contra «APAGADO») y H-02 (A23 reabre tres alternativas, el catálogo una) son las dos contradicciones nuevas. No encontré ningún caso de «REABIERTA» en un documento y «cerrada» sin marca en otro para D9, GAP #A o NEW-8: `MISSION.md`, A23, el puntero de Estado y el catálogo dicen lo mismo de D9; GAP #A aparece reabierto en los tres.
- A113 es coherente con A95 y A111: A95 y A111 tratan de cómo cae un cierre, A113 de qué hacer cuando cayó. Dos roces: el desglose que suma 49 (H-10) y que el mismo PR incumple su letra (b) en H_S27_1 y su letra (a) en D11 (H-04). A113 (d), «un encabezado que contradice a su propio cuerpo cuenta como texto sin marcar», se cumple en D8, D-PCC, D16, D20 y D26, y no en D11, D13 ni D21.

## 6. Forma

- Texto viejo: las 19 líneas eliminadas de los tres rectores reaparecen íntegras como agregadas, partidas en prefijo y sufijo alrededor de la marca (`f0_forma2.py`, 19 de 19 OK). En el borrador cambió el título y la numeración 13 a 14 (es un borrador, no historia). En `censo.py` el control viejo se reemplazó y queda descrito en el comentario.
- Citas `archivo:línea` nuevas que SÍ apuntan: `profile.py:676`; `process_modis.py:696/704/866-867`; `process_viirs.py:1071/1079/1272-1273`; `process_viirs_mod.py:705/713/854-855`; `mirova_equivalent.yaml:128-134`, `:279-282`, `:482`; `test1_integrated.py:12-18`; `process_modis.py:16`; `BIBLIOGRAPHY_SYNTHESIS.md:36-47`; `process_viirs.py` l. 1763-1786; `anchor.py` l. 67-89; commits `d58f7a46f`, `1d6b5b932`, `fab02ec1c`, `5d2bea4b9`. Las que no: H-06 y H-07.
- Tests que leen estos documentos: `98 passed, 2 xfailed` (7 archivos, sin caché ni bytecode).

## 7. Sospechas (no verificadas)

- S-1 (gravedad 2). A87 en `CLAUDE.md` (texto viejo, fuera del diff) dice «482 píxeles del path BT ... en agosto»; mi conteo sobre `data/mirova_equivalent/Villarrica.json` da `diag_n_bt_path > 0` en 0 records de abril a septiembre de 2026, y el flag está apagado desde el 2026-05-13. O el corpus se reprocesó o A87 nombra otro contador. El verificador de la Fase 1 agrega que ese contador nunca fue mayor que cero en ningún record de toda la historia (`FASE1_VERIFICADOR.md` §4), así que el «482» de A87 no puede ser `diag_n_bt_path`. No lo investigué más; choca con D31 y conviene mirarlo antes de que alguien use A87 como evidencia de que el camino de BT decide.
- S-2 (gravedad 1). Las citas verbatim de la p. 6 y la p. 7 en D30 y D31 coinciden con lo que el verificador anterior pegó; no abrí el PDF.

## 8. VERIFICADO LIMPIO, marca por marca

`CLAUDE.md`: (1) reglas científicas, V-08 y V-06: números y DOI iguales a la fuente; falla sólo el «SIN MEDIR» (H-01). (2) A23: 199, 214, 80 de 214 (37,4 %), 201 a 211, 59 de 214, 2.236 m, 63 a 88 %: iguales; falla el alcance (H-02). (3) A82: 89,1 % de 4.800, 93,7 % de 158, 144 de 158, 84,5 contra 62,1, 47,5 contra 22,8: iguales; falta ventana (H-16). (4) A83: 0,859 sin script, n = 4.547, 0,762, 0,706, 0,554, 11 estratos, tres bajo 0,50: iguales, LIMPIA. (5) A84: H-13. (6) A85: B-03 citado como «sólo leído, sin verificador»: LIMPIA. (7) A99: 1,140, 0,873, 342, 0,66, 1,39, 156 de 342, 23 %, 233 de 343, 14 y 13 %: iguales; H-16. (8) A113: H-10 y H-11. (9) serie continua: 2025-11-16 a 2026-01-28, 9 de 11 más PCC con 111 días desde 2025-10-10, Villarrica continuo, 19 días: iguales, LIMPIA. (10) puntero de Estado: LIMPIA.

`docs/MISSION.md`: (11) «Resueltas»: números iguales; falta D5 (H-05). (12) D11: iguales; falta ventana (H-16). (13) 5 / 10: H-01. (14) GAP #A: guard y ruta existen, LIMPIA. (15) NEW-8: flag True, tres procesadores, dos ramas: LIMPIA.

Catálogo: (16) fila Gaua y (17) nota Gaua: cero apariciones, JVGR 322 p. 10 §4.6, frase de la p. 17, diurnas: iguales; H-07 y H-18. (18) «Cobertura física»: LIMPIA. (19) «NO es un parche»: fiel a C-02 y a A105, LIMPIA. (20) fila F1.2: LIMPIA en lo que dice; ver sección 4. (21) nota NEW-8: flags, líneas y commit comprobados; H-07. (22) nota S100: H-07, resto LIMPIA. (23) nota F2.1: LIMPIA. (24) nota D9 S113: todos los números iguales; H-16. (25) sub-viñeta 207: LIMPIA. (26) Estado D9: H-03. (27) H_S27_1 pregunta 1: H-17; ubicación, sección 4. (28) D8: cita de D25 textual comprobada (l. 2536-2537), 5 de 11 con `local_kernel_bg: true` comprobado, A12 igual: LIMPIA. (29) D-PCC: commits y `inner_radius_km: 20` comprobados; H-08. (30) D12: 0 filas, 79 en 55 noches, 39 de 73: iguales, LIMPIA. (31) D13 «irreducible»: LIMPIA. (32) D13 1,5 %: 18 alertas MODIS, 0,6 y 1,0 %, 1.266, 92, 1, 36,1 contra 38,8: iguales; H-14. (33) D16 encabezado y nota: 61 días, n = 1 y 2, 0,740 a 0,253, n = 2.767, ventana anterior a #535: iguales, LIMPIA. (34) D16 «NO REABRIR»: LIMPIA. (35) D18: ventana 2026-05-29 a 08-24 igual a A-13, LIMPIA. (36) D19: D11 CONDICIONADA S138 comprobada en la l. 1391, LIMPIA. (37) D20: 0,0001, 0,0054, 47 veces, 0,74 C1, 0,024, 6 a 9 y 1 a 3 %: iguales, LIMPIA. (38) D26: 58,7 y 75,0 %: iguales a `AUDIT_S146.md` §2, LIMPIA. (39) D30: tabla, 78, 74, 4, 0, las cuatro noches, 2 de 143, 0,5637 contra 0,2506 a 0,3718, 38 de 50, 5 pasadas: iguales a la Fase 1; H-09, H-16, H-17. (40) D31: Tabla 1, 2.360 = 457 + 954 + 949, flags comprobados; H-06.

Otros: (41) borrador: H-15. (42) `censo.py`: puede fallar, H-12.
