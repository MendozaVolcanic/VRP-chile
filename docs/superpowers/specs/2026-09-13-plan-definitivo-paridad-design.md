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

## 2. Definición de terminado por sensor (propuesta, decide Nicolás)

Medida siempre con el **banco congelado** (§3), por pasada y por noche de volcán, **por volcán**
(nunca sólo agregado, S126), con la ventana y el denominador escritos.

| sensor | detección | falsas publicaciones | magnitud |
|---|---|---|---|
| VIIRS 375 | 0 noches con alerta perdidas respecto de hoy, por estrato focal/nevado | tasa en negativos limpios por pasada **≤ 25 %** (hoy 63,5 %) | mediana por pasada de nuestro/MIROVA en **[0,8 ; 1,25]** en cada volcán con n ≥ 30 (hoy 0,55 a 0,70) |
| VIIRS 750 | igual | **≤ 25 %** (hoy 20 % por pasada, 55 % por noche) | igual, donde haya n ≥ 30 (hoy casi sin verdad) |
| MODIS | todos los pasos literales implementados y activos (D21 a D25, D19) | en Láscar, tasa en noches con alerta **significativamente mayor** que en noches sin alerta (hoy 11,5 % contra 10,2 %) | informativa (n = 35 en OSF) |

Los umbrales numéricos son una propuesta de partida. Se revisan una sola vez, al terminar la Fase 0,
cuando se mida la consistencia del propio MIROVA (por ejemplo, con cuánta frecuencia MIROVA publica
en pasadas vecinas de la misma noche), y después **quedan congelados**.

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

## 7. Decisiones que siguen pendientes (Nicolás)

| # | pregunta | recomendación |
|---|---|---|
| P1 | ¿Se aceptan los umbrales de §2 como punto de partida? | sí, y congelarlos al cerrar la Fase 0 |
| P2 | Magnitud oficial: ¿por pasada o máximo de la noche? | **por pasada**, que es como publica MIROVA y como está el OSF |
| P3 | ¿Incluir el OCR en la comparación del dashboard y abrir `VALID_CLASSES` a Moderado y Alto? | sí, en la Fase 0 |
| P4 | Prioridad de la cadencia del NRT (5 corridas diarias) frente a la Fase 0 | en paralelo, no bloquea |
| P5 | S138-E (reintento del cortacircuitos) y S138-F (limpieza de git) | siguen como estaban, fuera de este plan |
