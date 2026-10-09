# Auditoría S150 (2026-10-08): ojos nuevos, con un volcán en erupción

> Cuatro frentes en paralelo (plan: `docs/PLAN_AUDITORIA_S150.md`), un verificador con contexto limpio sobre
> los hallazgos de gravedad 4 y 5 (`docs/audit_s150/VERIFICADOR_AUDITORIA.md`) y dos verificadores sobre el
> pre-registro de Nevados de Chillán, que confirmaron por su cuenta los hallazgos del frente B
> (`docs/audit_s150/VERIFICADOR_PREREGISTRO_NDC*.md`). Informes de cada frente: `docs/audit_s150/AUDITOR_<X>.md`;
> scripts y salidas: `experiments/_s150_audit/<X>/`. Primera auditoría hecha con Claude Opus 5.5.

## 0. En una pantalla

Dos cosas pasaron a la vez y el sistema no se las dijo a nadie: **el NRT estuvo caído 5 días y 11 horas**
(2026-10-03 07:36 a 2026-10-08 18:08 UTC) por un token vencido, y **Nevados de Chillán entró en erupción** el
2026-09-28. La auditoría encontró que el problema de fondo es el mismo en los dos casos: **el sistema calcula
bien, pero lo que muestra y lo que avisa no se diseñó para el caso que importa.** Los avisos existían y nadie
los recibe; el tablero oculta o deforma justo las señales fuertes, porque todo se calibró sobre volcanes en
reposo.

| familia | qué pasa | gravedad tras verificar | quién lo arregla |
|---|---|---|---|
| **1. El aviso no llega a una persona** | los avisos del token salieron diez días antes y los del apagón a las 14 y 33 h, pero nadie vigila el repo; el monitor cerró el issue del apagón en falso; la auditoría semanal leyó el apagón como falla de detección | 4 | Nicolás (vigilar el repo) y yo (monitor, auditoría semanal, hook de sesión) |
| **2. MODIS en erupción** | la etiqueta `far` oculta la alerta más fuerte; el tope D9 de 5 MW recorta magnitudes reales; y bajo ambos hay un detector que grita casi todas las noches frías | 4 | prueba de Chillán (pre-registro v3, mergeado, sin despachar) |
| **3. Magnitud en erupción** | el modo de un solo píxel salta entre el píxel más fuerte y la suma: el tablero de Chillán VIIRS 750 mostró 2,66, 11,08 y 2,49 MW en 54 minutos | 4 | prueba propia, después de la de Chillán |
| **4. La línea de MIROVA del tablero** | no lee el canal OCR, así que le faltan las dos pasadas más fuertes de la erupción (9,0 y 10,0 MW del 1-oct); el texto dice "CONS ∪ OCR" | 3 | decisión de Nicolás (frontend) |
| **5. Instrumentos** | la auditoría semanal no mira la etiqueta; el nulo de la selectividad no está estratificado por zona del barrido; el libro de cuentas usa un predicado viejo; los congelados de S149 no nombran su commit | 3 | yo |
| **6. Infraestructura** | Ubuntu 26 llega a `ubuntu-latest` entre el 19-oct y el 19-nov; un timeout de NASA LANCE marca caído también a LAADS | 2 | yo, con tu visto bueno |

## 1. Familia 1: el aviso no llega a una persona

**Lo que pasó** (A-1, A-2, A-3, D-02, verificados):
- El issue #752 avisó del vencimiento del token el 2026-09-23, diez días antes. El vencimiento también se te
  dijo por chat en las sesiones 144 a 149 ("renovarlo esta semana"). Los issues #754 y #756 avisaron del
  apagón a las 14 y 33 h. **Pero el repo tiene 0 suscriptores**, ningún issue tiene asignado y ningún
  workflow avisa fuera de GitHub. Si te llegaron los correos de "Run failed" queda SIN VERIFICAR.
- El monitor (`nrt-monitor.yml`) **cerró #754 como "recuperado" el 2026-10-07 06:19 con el sistema caído**:
  la API de GitHub le devolvió corridas del 3 de septiembre y el monitor no compara fechas. Hubo unas 17 h
  sin issue abierto. Además filtra sólo corridas `schedule`: con el cron externo no vería las despachadas.
- La auditoría semanal abrió #757 ("recall VIIRS 375 bajo la banda") cuando 11 de sus 14 fallos eran noches
  del apagón sin ningún dato nuestro; contando sólo noches con dato, el recall era 98,4 %. Su guarda de
  cobertura cuenta días con detección, no días con datos, y el veredicto DEGRADADO no abre issue.
- En esta misma sesión el apagón se detectó al retomar (2026-10-04 ~01:20 UTC) y se te avisó por chat como
  urgente; el aviso al celular no salió porque las notificaciones están apagadas. Ningún hook de sesión lee
  el vencimiento del token ni los issues abiertos.

**Arreglo por familia, en orden:**
1. **Tú**: activar "Watch" en VRP-chile (al menos Issues) y revisar si llegan los correos de Actions.
2. **Yo**: el monitor compara la fecha de la corrida más nueva contra la hora actual antes de cerrar, y
   cuenta también las corridas `workflow_dispatch`. **HECHO S150** (`scripts/nrt_monitor_decision.js`, `tests/test_nrt_monitor_decision_s150.py`):
   ordena, usa las tres más nuevas y, si la más nueva tiene más de 12 h, no alerta ni cierra (SIN DATO).
3. **Yo**: la auditoría semanal separa "noche sin datos nuestros" de "noche sin detección", y DEGRADADO abre
   issue. **HECHO S150** (`scripts/auto_audit_weekly.py`, `tests/test_auto_audit_cobertura_s150.py`): el recall
   excluye las noches sin ningún record nuestro y las informa como `noches_sin_datos`; la cobertura cuenta días
   con datos y avisa si faltan más de un día al final de la ventana; DEGRADADO abre un issue (uno por incidente).
4. **Yo, con tu visto bueno** (es configuración de tu Claude Code): un hook de inicio de sesión que lea los
   issues abiertos con etiqueta de alerta y los días que le quedan al token, y lo diga al empezar.

## 2. Familia 2: MODIS en erupción

Ya medido sin correr nada (frente B, frente C y los verificadores del pre-registro):
- La pasada MODIS del 2026-10-01 08:35 (MIROVA 5,18 MW) tiene el cúmulo a 0,9 km del cráter, pero la
  etiqueta `far` sale del píxel más caliente de la escena (32,8 km), un píxel que `store.py` ya había
  descartado por estar fuera de 25 km. El tablero la oculta.
- Arreglar sólo la etiqueta recupera esa alerta y destapa 22 de 28 pasadas de reposo en que MIROVA no vio
  nada: la etiqueta esconde un detector ruidoso.
- El tope D9 de 5 MW se arma con sólo tener el fondo bajo 270 K (el camino de temperatura de brillo está
  apagado desde S40) y ya recortó 11 de 27 magnitudes MODIS de la erupción. El tablero rotula esos 5,00 como
  "probablemente artefacto". Todavía no recortó ninguna alerta de MIROVA.

**Arreglo**: la prueba de Chillán (`experiments/_s150_ndc/PREREGISTRO_NDC.md`, v3, PR #759) separa detector,
tope y etiqueta con diez brazos y un evaluador probado 10 de 10. Espera tu "sí" y no puede despacharse antes
del 2026-10-13 (producto estándar de NASA).

## 3. Familia 3: magnitud en erupción

- **C-03, confirmado (4)**: bajo 5 MW el modo de un solo píxel publica el píxel más fuerte; sobre 5 MW, la
  suma. En Chillán VIIRS 750 el tablero mostró 2,66, 11,08 y 2,49 MW en 54 minutos, contra 9,0, 10,0 y 7,06 de
  MIROVA. Tampoco es monótono en el número de píxeles: tres de 1,6 MW publican 1,6 y cuatro de 1,0 publican
  4,0 (V-2).
- La magnitud MODIS focal da 0,57 de MIROVA contra 0,74 de la suma de píxeles del cráter (C-04, n 14,
  SOSPECHA sobre la causa).
- En el 29 % de los records con varios cúmulos, el primario es el más cercano al cráter y no el más
  energético (C-05).
- El píxel VIIRS 375 saturado se borra (C-02, matizado a 3): nunca ha pasado (máximo del corpus 354,24 K
  contra un techo de 361,27 K), pero Chillán ya llegó a 4,21 MW en un píxel.

**Arreglo**: una prueba propia del modo de un solo píxel, con su pre-registro, después de la de Chillán. No
se agrega a la de Chillán porque ya está verificada y cambiarla obliga a verificarla de nuevo.

## 4. Familia 4: la línea de MIROVA del tablero

`rebuild_mirova_from_consolidado.py` sólo lee la tabla de MIROVA, no el OCR, y sólo acepta las clases "Muy
Bajo" y "Bajo" (B-H4 y B-H5, V-1). Resultado: las dos pasadas más fuertes de la erupción (2026-10-01 05:24,
9,0 MW, y 06:00, 10,0 MW "Moderado") **no aparecen en la línea de MIROVA del tablero**, que además dice
"CONS ∪ OCR". Las métricas en vivo cuentan como falso negativo las pasadas que nunca procesamos (12 de 17 eran
del apagón). **Decisión tuya**: leer el OCR y aceptar todas las clases, o corregir el texto.

**HECHO S150 (decisión de Nicolás 2026-10-09, opción a)**: `rebuild_mirova_from_consolidado.py --ocr` suma las
alertas nocturnas del OCR marcadas `source: ocr` y acepta la escala completa de MIROVA (incluida "Medio", la
etiqueta de la versión 21 del OCR); la tabla manda si las dos traen la misma pasada; las pasadas diurnas del
OCR quedan fuera (A76). `index.html` y `diario.html` dibujan los puntos del OCR como rombo hueco, con una nota;
`diario.html` deja de leer el CSV a mano y usa el mismo `data/mirova/<Volcán>.json`. Verificado en navegador:
Chillán muestra 10,0 MW el 2026-10-01 en VIIRS 750 y 8,24 MW el 2026-10-05 en VIIRS 375. Pendiente: las métricas
en vivo siguen contando como falso negativo las pasadas que nunca procesamos.

## 5. Familia 5: instrumentos

- D-01 (matizado a 3): la auditoría semanal usa una vara "cráter" que no mira la etiqueta; en MODIS da 85,7 %
  donde el tablero da 28,6 % (n 7: no podía decidir en esa ventana, pero mide mal).
- D-03 (3): el nulo de la selectividad (C8b) baraja sólo dentro de cada volcán; un brazo que apaga todo lo
  publicado sobre 52° de cenit lo cumple. Con un nulo estratificado por zona ese brazo falla y `max` sigue
  cumpliendo: **los veredictos de S150 sobre `max` se mantienen**.
- D-04 (2): `libro_de_cuentas.py` usa un predicado anterior a #642 (recall VIIRS 750 83,52 % donde el tablero
  da 79,78 %).
- D-05 (2): los CSV congelados de S149 no están en git, pero se reconstruyen exactos desde los commits
  `3872fedd4` (tabla) y `d21fe1c0d` (OCR); los manifiestos no nombran esos commits y nada verifica el sha256.
- D-07 (2): la auditoría semanal mide la magnitud VIIRS 375 con `pc.vrp_mw` y no con el núcleo que ve el
  operador.

## 6. Familia 6: infraestructura

- A-9 (matizado a 2): `ubuntu-latest` migra a Ubuntu 26.04 entre el 2026-10-19 y el 2026-11-19 (anuncio
  runner-images #14748). `pyhdf` 0.11.7 trae rueda para Python 3.11 y `libhdf4-dev` existe en 26.04, así que el
  riesgo es menor. Seguro barato: fijar `ubuntu-24.04` en `nrt.yml` hasta probar 26.04.
- A-13 (3): un timeout de LANCE marcó caído también a LAADS (`pipeline/fetch.py:696-716`); a Llaima le
  faltaron las pasadas VIIRS del 2026-10-08 y el job salió verde.
- V-3: el cron del NRT corre unas 4,25 a 5 veces al día, no 12. Lo resuelve el cron externo (plan de S142,
  con la franja `10 1-12 * * *` recomendada en S150 y dos enmiendas del frente A: el monitor debe contar las
  despachadas, y "no se pierden datos" vale sólo para cortes de menos de 7 días).

## 7. Pruebas de campo

| qué mirar | qué decide |
|---|---|
| Tu correo, "Run failed: NRT VRP Pipeline" entre el 3 y el 8 de octubre | si GitHub avisó y se perdió, o no avisó |
| El issue #758 en los próximos días | si se cierra citando corridas de septiembre, A-2 se repite y el arreglo del monitor es urgente |
| El tablero de Chillán con "Incluir lejanas" encendido, filas de 5,00 MW en MODIS | cuánto de lo `far` es tope D9 |
| La línea de MIROVA VIIRS 750 del 1-oct en el tablero contra su imagen (10,0 MW) | si la referencia del tablero tiene que leer el OCR |
| La tarjeta de Chillán hora a hora en una noche activa | si en erupción debe mostrar el máximo de la noche y no la última pasada |

## 8. Decisiones que esperan a Nicolás

| # | pregunta | recomendación |
|---|---|---|
| 1 | Despachar la prueba de Chillán desde el 2026-10-13 | **sí** |
| 1b | El recall de `max` en VIIRS 375 (abril a agosto) | ya no hay pérdidas fuertes CONFIRMADAS: las cinco de Suomi NPP tienen VRP real de su pasada pero la distancia y la clase de otra pasada, así que no se sabe si eran del cráter (`docs/S150_IMAGENES_SNPP.md`, corregido); la pregunta es sólo si se acepta perder parte del tramo bajo 0,10 MW en la réplica |
| 2 | La línea de MIROVA del tablero: leer el OCR y todas las clases, o corregir el texto | **leer el OCR**: hoy oculta las alertas más fuertes |
| 3 | El hook de inicio de sesión que lee issues abiertos y días del token | **sí**: es el único aviso que no depende de que alguien abra GitHub |
| 4 | Fijar `ubuntu-24.04` en `nrt.yml` hasta probar 26.04 | **sí**: una línea, reversible |
| 5 | `first_processed_utc` en `store.py` (A45) y cron externo cada hora de 01 a 12 UTC | **sí** a las dos |

### Decisiones de Nicolás registradas el 2026-10-09

- **Regla de selección en la réplica: gana la anomalía MAYOR de la escena**, como MIROVA (que por eso a veces
  reporta incendios). Comprobado en los datos de MIROVA: desde marzo, además de 1.398 alertas dentro del radio del
  cráter, publicó **858 detecciones a una mediana de 20 km** (hasta 34,5 km) que el scraper rotula FALSO_POSITIVO
  por distancia (`latest_consolidado.csv`). Producción hoy hace lo contrario: `enable_vent_anchored_clustering: true`
  (S38, elige el cúmulo más cercano al cráter); la opción `vrp_max` de `pipeline/clustering.py` es la anomalía mayor.
  **Pendiente: A/B con pre-registro** (`vent_anchored` contra `vrp_max`), midiendo además la paridad de distancias
  contra MIROVA incluyendo sus detecciones lejanas. Va después del A/B de D22 y de la prueba de Chillán.
- **Experimental**: congelado en la producción de hoy (PR #771); sus áreas se definen más adelante, con las
  coordenadas de los rasgos reales.
- **S149 §6**: se reabren las metas de la tabla del 2026-09-14 (por pasada y por tramo en VIIRS, mediana agregada en
  magnitud, tasa falsa acotada por la tasa base de alerta del sensor); el día de la adopción se reprocesa la historia
  desde el 2026-01-29 y además se marca el cambio de régimen en las vistas.
- **Quedan para después**: la cronología de OVDAS de Chillán y las coordenadas de los rasgos reales.

## 9. Lo que esta auditoría no cubrió

- La fidelidad al paper (cubierta en S138, S146 y S149) y la conectiva (medida en S149 y S150).
- Nada después del 2026-10-08 18:30 UTC; las alertas del 5-oct de Chillán con el relleno se miden en la prueba.
- Si MIROVA conserva la banda I4 saturada; todo el régimen sobre 10 MW (no hay pares).
- El tablero se miró con navegador sólo en el frente B y sólo para leer.
