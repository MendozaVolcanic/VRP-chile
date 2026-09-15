# Plan definitivo S139: paridad con MIROVA por sensor

> Diseño escrito el 2026-09-13 (S139) tras la auditoría de 6 ejes + verificador limpio
> (`docs/audit_s139/`) y dos mediciones propias verificadas (`experiments/_s139_audit/keep_peak_paridad/`,
> `docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md`). **Estado: propuesta para revisión de Nicolás.**
> Nada de esto toca `pipeline/` hasta que Nicolás apruebe el documento y cada cambio de código pase
> por tag defensivo y confirmación (A45).

## 0. Decisiones ya tomadas por Nicolás (2026-09-13, en la sesión)

| # | decisión |
|---|---|
| 1 | **Manda la paridad por sensor.** No se adopta nada que pierda noches que MIROVA publicó. La fidelidad literal al paper decide sólo entre brazos que empatan en paridad. MODIS, sin positivos fuera de Láscar, se juzga por fidelidad. |
| 2 | Rescatar los artefactos A/B que vencían (hecho: 172 de 172, `experiments/_artefactos_ab/`). |
| 3 | `keep_peak`: no adoptar ni extender sin entender por qué baja la paridad y por qué la magnitud queda en ~0,7 (hecho: §1.3 y §1.4). |
| 4 | Preparar el correo a Diego Coppola; lo envía Nicolás (borrador en `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`). |
| 5 | (antes, misma sesión) S138-B, C, D y G aprobadas: flags para fondo y segundo pase, A/B en 3 sensores, recall en noche de volcán, partición focal/nevado de S131. Este plan las reformula en §4 con lo medido después. |

## 1. Diagnóstico medido (lo que sostiene el plan)

### 1.1 La detección de alertas está bien; el problema es publicar de más

- Por noche de volcán con cualquier sensor acertamos **874 de 877** noches con alerta MIROVA
  (eje 2; ventana 2026-01-10 a 2026-09-07, CONS+OCR, nocturno).
- En noches sin alerta publicamos detección en el cráter en el **90,5 %** (cualquier sensor). Por
  sensor: VIIRS 375 **82 %**, VIIRS 750 **55 %**, MODIS **18 %** (eje 2, verificador §reconciliación).
- Nunca lo vimos porque **ninguna métrica viva mide contra negativos** (eje 6 H602): publicar de más
  no se penalizaba.

### 1.2 Cada sensor publica de más un objeto físico distinto (verificador)

| sensor | qué publica de más | fenómeno |
|---|---|---|
| VIIRS 375 | 66 % de lo publicado en pasadas MIROVA con VRP 0 es **D19**: un píxel suelto del Test 1 en el flanco bajo del cono, bajo el fondo (mediana −1,56 K), 0,050 MW | topografía, no calor |
| VIIRS 750 | cúmulos de ~0,30 MW (D19 es 20 de 693) | sin causa identificada |
| MODIS | campos de ~2 MW con p90 en el tope de 5,000 MW; publica igual con alerta (11,5 %) que sin ella (10,2 %) | ruido de la banda 21 (S137) y campo difuso: hoy no distingue actividad |

### 1.3 Por qué `keep_peak` "tenía" paridad (medido S139, evaluador S135 reproducido exacto)

Con `keep_peak` activo se publica el píxel más caliente, a menudo a ~3 km del cráter, con 0,05 a 0,1
MW (razón 0,78 contra MIROVA). Apagado, se publica el píxel del cráter con 0,001 a 0,01 MW (razón 0,37),
que está sólo 1,2 K sobre el fondo del anillo. **La paridad salía por accidente, con el píxel
equivocado.** Apagarlo solo empeora la magnitud.

### 1.4 Por qué la magnitud es ~0,7 y no ~1 (OSF v2.5, 1.499 pasadas V375 de 2025, verificado)

MIROVA calcula `VRP = k · A_fija · Σ(L_hot − L_bk)` sobre `Npix` píxeles (se cumple en el 100 % de
las filas de 375 m y 1 km). Nosotros usamos los mismos k y A. La diferencia está en qué se suma:

| factor | razón nuestra/MIROVA | qué es |
|---|---|---|
| **número de píxeles** | 0,47 cuando el conteo difiere (1 nuestro contra 3 de MIROVA, medianas) | los **vecinos tibios del foco se pierden en la detección** |
| **fondo** | 0,873 | el anillo de 5 a 25 km queda **3,5 K más tibio** que el fondo de MIROVA; con kernel 3×3 el factor vuelve a ~1 |
| selección del píxel más caliente | 1,14 a 1,49 | compensa en parte los dos anteriores |
| **a igual número de píxeles** | **0,995** (n = 342) | la fórmula y la calibración están bien |

Dentro de cada volcán el déficit crece con el ángulo cenital porque MIROVA remuestrea y su `Npix`
sube (Isluga 3 a 5) mientras el nuestro sigue en 1: el remuestreo explica la **pendiente**, no el
**nivel** (a nadir el factor de conteo ya es 0,63).

**Conclusión: las dos causas de fondo son una sola familia, la del píxel débil que rodea al foco.**
Nuestra detección no lo incluye y nuestro fondo es demasiado tibio para que aporte. Es lo mismo que
hace publicar píxeles sueltos en el flanco (1.2) y lo mismo que S124 vio en noches de 1 píxel.

### 1.5 Por qué no convergimos en meses (eje 3, con casos citados)

1. No había verdad con negativos ni **criterio de terminado** (eje 6 H601).
2. La misión pedía fidelidad **y** paridad sin regla de desempate (ahora decidida, §0.1).
3. Parches acoplados probados de a uno (S121, S133, S135).
4. Instrumentos que medían otra cosa: predicado distinto del dashboard, unidad noche-sensor, corpus que
   crece, denominadores sin cobertura (A90, A93, A94).
5. Cierres heredados de lecturas incompletas del paper (A95) y olvido del propio repo (A50).
6. Verdad externa rica sin usar: OSF v2.5, OCR, Coppola.

## 2. Definición de terminado por sensor (CONGELADA el 2026-09-14, S141, decisión Nicolás)

Medida siempre con el **banco congelado** (§3), por pasada y por noche de volcán, **por volcán**
(nunca sólo agregado, S126), con la ventana y el denominador escritos.

| sensor | detección | falsas publicaciones | magnitud |
|---|---|---|---|
| VIIRS 375 | 0 noches con alerta perdidas respecto de hoy, por estrato focal/nevado | tasa en negativos limpios por pasada **≤ 10 % en focales y ≤ 15 % en nevados** (hoy 63,5 %; ⚠️ **S142: ese valor mezcla dos regímenes**. Con sólo el régimen posterior a #571, del 2026-09-01 al 2026-09-15, la tasa es **87,1 % de 295 pasadas** y **100 % de 93 noches**. Por estrato: focal 84,5 % de 84, nevado 88,1 % de 211. Fuente: `experiments/_s142_linea_base/linea_base_post535.json`. Corregido 2026-09-14 con el ~5 % de falsas que declara el propio MIROVA, SP426.5 p. 9, ver §7.2) | mediana por pasada de nuestro/MIROVA en **[0,8 ; 1,25]** en cada volcán con n ≥ 30 (hoy 0,55 a 0,70) |
| VIIRS 750 | igual | **≤ 10 % focales, ≤ 15 % nevados** (hoy 20 % por pasada, 55 % por noche) | igual, donde haya n ≥ 30 (hoy casi sin verdad) |
| MODIS | todos los pasos literales implementados y activos (D21 a D25, D19) | en Láscar, tasa en noches con alerta **significativamente mayor** que en noches sin alerta (hoy 11,5 % contra 10,2 %) | informativa (n = 35 en OSF) |

Los umbrales numéricos eran una propuesta de partida. Se iban a revisar una sola vez, al terminar la
Fase 0, cuando se midiera la consistencia del propio MIROVA (por ejemplo, con cuánta frecuencia MIROVA
publica en pasadas vecinas de la misma noche), y después **quedar congelados**.

**Congelados el 2026-09-14 (S141), decisión de Nicolás**, con la Fase 0 cerrada salvo la tarea 10
(lectura de papers), que no mueve umbrales. Queda escrito lo que NO se hizo: **la medición de
consistencia del propio MIROVA no se corrió** antes de congelar. Si al correrla resulta que MIROVA
mismo no cumple estas bandas contra sí mismo, eso es motivo para reabrir esta tabla, y es el único.
Los valores que usa el auto-audit semanal (`scripts/auto_audit_weekly.py`, `FALSAS_BANDA_TERMINADO`)
son los de esta tabla.

## 3. Fase 0: el instrumento (sin tocar `pipeline/`)

1. **Banco congelado** en `scripts/banco_paridad.py` con tests (promovido de
   `experiments/_s139_audit/eje2/banco_noches.py` y del verificador `v1_negativo_por_pasada.py`):
   - positivos: ALERTA del consolidado + ALERTA_OCR nocturna validada (eje 1);
   - negativo limpio: gránulo MIROVA con VRP 0, nocturno, sin ALERTA ni FALSO_POSITIVO esa noche y
     sensor, con registro nuestro a ±2 min (verificador: RUTINA por gránulo sí sirve);
   - sin información: todo lo demás, fuera del denominador (incluye meses sin records nuestros);
   - predicado del dashboard ejecutado desde `frontend/index.html` con node, **sha fijado**;
   - dos unidades (pasada y noche de volcán), por volcán, con control barajado y control oráculo.
2. **Segundo instrumento, magnitud**: `scripts/descomponer_magnitud_osf.py` (promovido de
   `experiments/_s139_audit/magnitud/`), que reporta los factores de §1.4 por volcán y ángulo. Hoy
   cubre 2025; para 2026 se usa el máximo por pasada contra el CSV.
3. **Línea base congelada** con ambos instrumentos sobre `main` de hoy, commiteada con su sha.
4. Auto-audit semanal: agregar la tasa en negativos y el factor de conteo; las bandas pasan a ser las
   de §2.
5. Urgencias operacionales, en paralelo: renovar el token Earthdata antes del 2026-10-03 (Nicolás);
   investigar la cadencia del NRT (5 corridas diarias en vez de 12, eje 5 H504); corregir el reloj del
   guard de reprocesos (5,1 min por día, eje 5 H503).

**Salida de la Fase 0:** los dos instrumentos con tests verdes, la línea base commiteada y §2 con sus
umbrales congelados.

## 4. Fases de trabajo sobre el pipeline

Orden por lo que más pesa en paridad y menor riesgo. Cada fase empieza con un **probe por etapa (A75)**
de sólo lectura en GitHub Actions antes de cualquier A/B, porque tres veces una atribución sin el paso
siguiente resultó equivocada (S137, S138).

### Fase 1: VIIRS 375, el píxel débil que rodea al foco

- **Probe**: en una muestra de pasadas OSF donde MIROVA suma 3 o más píxeles y nosotros 1, registrar
  por etapa (primer pase, compuerta, segundo pase, `keep_peak`, fondo) qué pasa con cada vecino.
  Pregunta: ¿dónde se pierde el vecino y cuánto aporta con fondo local?
- **A/B** con los brazos que el probe justifique, en diseño "literal completo + ablaciones" (eje 4),
  no apilado. Candidatos hoy: fondo por vecinos (D25), `keep_peak` apagado (D19), segundo pase
  condicionado (D19/D2), sin compuerta (D22). Nunca `keep_peak` apagado solo (§1.3).
- Código nuevo necesario: flags de D25 y D22, que hoy no existen (eje 5 H501/H502; la compuerta vive en
  17 sitios). Tag defensivo + test "apagado no cambia nada" + confirmación de Nicolás.

### Fase 2: VIIRS 750

- Probe para identificar qué son los cúmulos de ~0,30 MW publicados en noches sin alerta.
- A/B con los brazos de la Fase 1 que apliquen (VIIRS 750 no tiene hoy kernel local).

### Fase 3: MODIS

- Brazo literal completo (banda 22 + fondo por vecinos + segundo pase condicionado + sin compuerta)
  con ablaciones. Criterio: fidelidad + separación en Láscar (§2). Banda 22 sola no (eje 3, eje 4).

Las respuestas de Coppola pueden reordenar o saltar brazos de cualquier fase.

## 5. Criterios pre-registrados de todo A/B (se escriben antes de mirar resultados)

1. **0 noches con alerta perdidas** por estrato focal/nevado (partición S131,
   `scripts/build_c2ab_windows.py:41-42`), medido por noche de volcán con cualquier sensor.
2. **Baja la tasa de publicación en negativos limpios**, con intervalo bootstrap que excluye el cero.
3. **La magnitud se acerca a 1** en la mediana por pasada, y no empeora más de 0,05 en ningún volcán
   con n ≥ 30.
4. Desarrollo de enero a mayo de 2026, prueba de junio a septiembre; el brazo se juzga en prueba.
5. Cobertura pareja entre brazos verificada antes del veredicto (patrón `evaluar_ab.py`).
6. Resultado anotado el mismo día en `docs/HYPOTHESIS_LOG.md` y revisado por un verificador con
   contexto limpio antes de proponer adopción.

## 6. Lo que no se hace

- No adoptar `keep_peak` apagado solo.
- No retirar juntos la etiqueta `far` y el tope del path D (S121 destapó 117 MW en PCC).
- No explicar las publicaciones en negativos con A54 (calor real) sin re-medirlo con el código de hoy.
- No subir el recall de MODIS cambiando la etiqueta: publicaría en el 92 % de las noches sin alerta.
- No usar el AUC agrupado entre volcanes (da 0,64 a 0,70 con etiquetas barajadas).
- No reprocesar la ventana completa antes del tamaño mínimo viable (6 volcanes, junio a agosto, ~63 h
  de runner, eje 5).

## 7. Revisión del 2026-09-14 (tanda 2) a partir de las preguntas de Nicolás

Fuentes: `docs/audit_s139/MAPA_BASES_MIROVA_V1.md`, `OSF_VS_NRT.md`, `NRT_CADENCIA_Y_MEJORAS.md`,
`LECTURA_PDF_TABLAS_FIGURAS.md`, y lectura propia (renderizada) de SP426.5 p. 5 a 9, 16 y 17,
Fernandina 2025 p. 9 y Coppola 2014 p. 9. Lo marcado "verificado" lo re-medí o lo leí en la página.

### 7.1 Lo que cambia en la verdad de referencia

| hallazgo | estado | consecuencia en el plan |
|---|---|---|
| ⚠️ **Corrección S142 (A105)**: la supervisión manual es de la v.1; el OSF v2.5 no tuvo revisión manual y lo filtran una clase automática (DBSCAN más reglas por distancia) y umbrales VRP por sensor (Coppola et al. 2026, Scientific Data, p. 7, p. 8 Tabla 1, p. 10 a 12). La consecuencia en el plan se mantiene. Texto original: El OSF está supervisado a mano (Coppola 2023 §2.5; Fernandina p. 9: "continuously supervised by visualizing each image"; SP426.5 p. 17: las series NRT van "as they are"). No hay ni un día de solape con el NRT que guardamos (OSF hasta 2025-12-31; scraper desde 2026-01-10; TIF desde 2026-05-09). | verificado | El OSF sirve para fórmula, fondo (`Tot_Lmir_bk`) y número de píxeles (`Npix`) por pasada; **no** para recall ni precisión. La verdad del NRT es sólo lo que nosotros guardamos. |
| `Max_Dist` del OSF es la distancia de la cumbre al píxel alertado **más lejano**, y `LAT/LON` es el píxel más caliente (esquema v2.5, verificado). **Qué distancia publica la web, medido con TIF NRT** (`docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md`, 171 pasadas, 2026-05-09 a 2026-09-07): **probablemente `Max_Dist`, no demostrado**. La pendiente del exceso con el VRP (+0,211 km/década [0,102; 0,335]) apoya `Max_Dist`; la constante (+0,113 km [0,072; 0,153]) queda **entre** las dos hipótesis (0 y +0,232); en las filas FALSO_POSITIVO (+0,063 [0,009; 0,121]) el dato no decide. **Corrección 2026-09-14 (orquestador)**: los porcentajes "87 % dentro de 1 km" y "4 a 8 % con el cráter adentro" salían del OSF, que está supervisado a mano (Coppola 2023 §2.5, p. 4, página leída): se quitaron incendios y falsas alertas, así que esos conteos **no se transfieren al NRT**. Sólo con NRT: en las 128 pasadas FALSO_POSITIVO con TIF el foco dominante (máximo del campo MIR con paso alto de 9 px, prominencia ≥ 6 σ) cae dentro del radio en el **4,7 %**; pero el mismo instrumento lo ubica dentro del radio sólo en el **33,3 %** de las 396 pasadas ALERTA, así que ve el foco dominante y **no** descarta una señal débil del cráter detrás de un foco lejano. | TIF NRT verificado; conclusión sobre la definición = SOSPECHA fuerte | FALSO_POSITIVO sigue **sin información** para el cráter. Como control de nuestras `far` (métrica `far_ref`) sirve: en ~95 % de esas pasadas el foco dominante está fuera del radio. La pregunta 11 a Coppola **sí** es necesaria para cerrar la definición. |
| El consolidado remoto de Mirova-v1 perdió filas dos veces (23-abr y 25-ago): al menos **18 ALERTAS** faltan respecto del respaldo local del 8 de abril (el agente cuenta 31 con la versión del 22-ago). VRP Chile las heredó perdidas. | verificado (18) | Fase 0: reconstruir la referencia como **unión** del snapshot actual, el respaldo del 8-abr y el OCR, y avisar a Mirova-v1 del mecanismo (`rebase -X ours` sobre un archivo reescrito entero). |
| Cobertura por fecha: tipos válidos desde 2026-01-16; cobertura ≥ 95 % desde febrero y ≥ 99 % desde marzo; Tupungatito con límite de 7 km desde 2026-02-23; OCR confiable desde 2026-03-01, con distancia desde 2026-06-13. | medido por el agente | Ventana del banco: **desde 2026-03-01** para los tres sensores; enero y febrero sólo como sin información. |
| 578 ALERTA_OCR quedan sin distancia por mojibake en las notas (loader de VRP Chile). | medido por el agente | Fase 0: arreglar el regex del loader antes de congelar el banco. |
| `float('2,178.53')` aborta el ciclo del scraper con VRP ≥ 1.000 MW. | medido por el agente | Aviso a Mirova-v1; latente para una erupción grande. |

### 7.2 Lo que cambia en la lectura del paper

| hallazgo | estado | consecuencia |
|---|---|---|
| El `.txt` de SP426.5 convierte `>` en un **punto** y `=` en `¼`; A95 debe decir "operadores y símbolos", no sólo `<`. | verificado por el agente en las 25 páginas | Regla: toda fórmula se lee renderizada. Corregir A95 en `CLAUDE.md`. |
| Fernandina 2025 ec. 2: coeficiente de Wooster en forma cerrada, `α = -8,6344e-10·λ + 6,3796e-9`, `k = σ/α`. Da 17,998 (I4), 19,67 (M13), 18,98 (MODIS b21) y 19,15 (MODIS b22). | verificado (página leída, números recalculados) | Confirma la calibración S14; **no se cambia k** (manda la paridad y S14 dio ±0,17 % contra el OSF). Sirve para cualquier sensor nuevo. |
| Fernandina p. 9: el NRT remuestrea a grilla UTM 51 × 51 km **centrada en la cumbre del GVP**; fondo = radiancia media de los vecinos no alertados. | verificado | Responde las preguntas 6 (parte) y 7 del correo a Coppola; D17 y D25 tienen cita moderna. |
| SP426.5 p. 9: con la Tabla 1 MIROVA omite ~10 % y produce ~5 % de falsas alertas (Etna y Stromboli). | verificado | Techo de la definición de terminado: falsas publicaciones por pasada **≤ 10 %** en focales (el doble del propio MIROVA), en vez del 25 % de §2. |
| Coppola 2014 p. 9: test 2 con `and` explícito. | verificado | Pesa hacia la lectura `max` de la conectiva (D26, pregunta 1). No decide solo. |
| El paper nunca escribe la ecuación del ETI: Fig. 3 rotula `NTI - NTIbk`, Fig. 4 `NTI - NTIapp`. | verificado (lo vi en las páginas 7 y 8) | Pregunta 13 para Coppola. Nuestro código usa `NTIbk` (ec. 5), que es lo que muestran los ejes de la Fig. 2. |
| `docs/MIROVA_DETAILED_CITATIONS.md:216` atribuye al paper una ecuación que no está impresa. | agente | Corregir la cita. |
| Fernandina fig. 3: "Supervised VRP timeseries"; MODIS TIR = banda 31 en 2025 (D20 cambia de signo). | agente, no verificado por mí | Anotar en el catálogo; D20 se revisa. |

### 7.3 NRT

Causa raíz de las 5 corridas diarias (verificada por el agente, hipótesis alternativas refutadas): GitHub
despacha los crones de este repo con ~3,5 h de atraso desde el 27 de agosto y funde las franjas que
vencen en la cola; la cobertura de datos está intacta y el problema es latencia (~6,5 h). Verificado por
mí: el cron corre el perfil `experimental` (`nrt.yml:192`) que escribe en `experimental_v2/` mientras el
workflow commitea `experimental/`: se calcula y se pierde; y `product_version_from_granule`
(`fetch.py:367`) no tiene llamador, así que MODIS NRT queda etiquetado "standard" (19 gránulos en Láscar
desde agosto). Mejoras, en orden: (1) sacar `experimental` del cron o commitear su carpeta real; (2) aviso
del vencimiento del token Earthdata (~2026-10-03); (3) hacer visible el cortacircuitos A64 en el resumen
del job; (4) cablear el detector de producto. Las cuatro tocan `nrt.yml` o `fetch.py`: tag y confirmación.

### 7.4 Radiancia de fondo

MIROVA la calcula y la publica por pasada (`Tot_Lmir_bk`). Nosotros guardamos `t_bg_k` y de ahí se
reconstruye; no guardamos el fondo por píxel cuando actúa el kernel local ni el número de píxeles
"suitable". Fase 0 agrega al record `diag_L_bg_w_m2_sr_um` (del anillo y, si aplica, local) y
`diag_n_suitable`, sin cambiar ninguna decisión. Permite comparar fondo contra fondo sin reprocesar.

### 7.5 Ajustes al plan (§2 a §6)

- Banco (§3.1): ventana desde 2026-03-01; referencia = unión snapshot + respaldo 8-abr + OCR; FALSO_POSITIVO
  = sin información para el cráter y positivo para `far`; negativo limpio por gránulo como estaba.
- Definición de terminado (§2): falsas publicaciones por pasada ≤ 10 % en focales y ≤ 15 % en nevados
  (MIROVA declara ~5 %); magnitud y recall como estaban.
- Fase 0 suma: loader OCR (mojibake), radiancia de fondo persistida, corrección de A95 y de la cita
  fabricada, y las mejoras 1 a 4 del NRT.
- Correo a Coppola: quitar las preguntas 6 (parte) y 7, ya contestadas por Fernandina 2025; agregar
  12 (qué distancia publica el NRT: ¿la del píxel más lejano?) y 13 (ecuación del ETI: `NTIbk` o `NTIapp`).

## 8. Decisiones que siguen pendientes (Nicolás)

| # | pregunta | recomendación |
|---|---|---|
| P1 | ¿Se aceptan los umbrales de §2 como punto de partida? | sí, y congelarlos al cerrar la Fase 0 |
| P2 | Magnitud oficial: ¿por pasada o máximo de la noche? | **por pasada**, que es como publica MIROVA y como está el OSF |
| P3 | ¿Incluir el OCR en la comparación del dashboard y abrir `VALID_CLASSES` a Moderado y Alto? | sí, en la Fase 0 |
| P4 | Prioridad de la cadencia del NRT (5 corridas diarias) frente a la Fase 0 | en paralelo, no bloquea |
| P5 | S138-E (reintento del cortacircuitos) y S138-F (limpieza de git) | siguen como estaban, fuera de este plan |
