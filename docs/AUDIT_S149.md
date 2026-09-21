# AUDIT S149: qué falta para cumplir el objetivo, y qué sabíamos y habíamos perdido

> Pedida por Nicolás el 2026-09-21. Siete auditores en paralelo, un verificador con contexto limpio sobre
> el hallazgo central, y esta síntesis. Plan de la auditoría: `docs/PLAN_AUDITORIA_S149.md`. Informes:
> `docs/audit_s149/plan_final/FRENTE_A` a `FRENTE_G` y `VERIFICADOR_MAGNITUD_CERO.md`; scripts y salidas en
> `experiments/_s149_audit/`. **Los números de esta síntesis no son míos: cada uno sale del script del
> informe que se cita al lado.** Nada de esto tocó `pipeline/` ni autoriza un cambio en producción.
> Estado: **PROPUESTA. Las metas y las decisiones de la sección 6 son de Nicolás.**

## 0. En una pantalla

**El objetivo** (palabras de Nicolás, 2026-09-21): máxima fidelidad a MIROVA en la réplica, con **paridad en
los dos sentidos** (publicar lo que MIROVA publica y callar donde calla; lo extra va al experimental); más
detecciones, con posibles falsos positivos, en el experimental.

**Dónde estamos, medido hoy en producción, del 1 al 21 de septiembre** (frente C, `tabla_hoy.txt`):

| | VIIRS 375 | VIIRS 750 | MODIS |
|---|---|---|---|
| cuando MIROVA alerta, publicamos (por pasada) | 100 % (154 de 154) | 66,7 % (14 de 21); 77,8 % de junio a agosto | 11,7 % (9 de 77, marzo a septiembre, todas de Láscar) |
| cuando MIROVA dice "nada", publicamos | **86,8 %** | 22,8 % | 11,5 % |
| volcanes dentro de la banda de la tabla de terminado | 0 de 11 | 2 de 11 | 9 de 11 |

Tres brechas de naturaleza distinta: VIIRS 375 **publica casi siempre**; VIIRS 750 **detecta y publica cero**;
MODIS **no discrimina** (publica igual con alerta que sin ella). Y una cuarta, transversal: la **magnitud**
queda cerca de 0,6 de la de MIROVA entre 0,10 y 0,50 MW.

**La respuesta a "¿nos estamos enredando?": sí, y se puede medir.** De los 28 flags encendidos en la réplica,
8 ejecutan el algoritmo del paper; 9 (más 15 constantes) son el Test 1 integrado y su séquito, que es un
detector nuestro; 3 están encendidos y no hacen nada; 2 sostienen un detector heredado que ya no detecta; 6
son la capa de magnitud y publicación (frente E). Y el veredicto de S27 que fundó el Test 1 ("el literal puro
pierde recall, no reabrir") se midió contra un perfil "literal" que **no tenía los Tests 2 y 3 del paper**:
entraron al repo 16 días después (comprobado por mí con `git log`: `db602040b` del 2026-04-29 contra
`958a7a189` del 2026-05-15; hoy `_mirova_literal` resuelve primer y segundo pase apagados y el camino de
temperatura de brillo encendido).

## 1. Lo que sabíamos y habíamos perdido (el eje nuevo de esta auditoría)

| qué | dónde estaba | cómo se perdió | qué plan torció |
|---|---|---|---|
| "VIIRS captura todo lo que MIROVA publica; sólo MODIS puede perder sub-píxel" (sesión 10) | memoria `feedback_mirova_equivalent_priorities` | el índice lo resumió como "pérdidas bajo 0,5 MW aceptables" | criterio de recall de VIIRS en 4 pre-registros, en `evaluar.py:615`, en el plan de paridad de S146; y S131 cerró **111 alertas perdidas** de VIIRS como "no fallas" (frente A, H2 y H3) |
| Ya existe una **tabla de terminado** por sensor, congelada por Nicolás el 2026-09-14 | `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:75-95` | ningún bloque de arranque ni `CLAUDE.md` la cita | esta misma auditoría iba a proponer metas desde cero (frente A, H4) |
| "Fidelidad en los dos sentidos", dicho por Nicolás en S135, S148 y hoy | bitácoras y memoria | cada resumen del agente se quedó con una mitad; `CLAUDE.md` dice "priorizamos recall sobre precision" y una memoria de S143 dice "cobertura primero", que es glosa del agente | el freno a la caja de S130 y el orden de los frentes (frente A, H1 y H5) |
| Calidad de los CSV del scraper por mes | `docs/audit_s139/MAPA_BASES_MIROVA_V1.md` §2 | sin puntero | ventana de A/B elegida sin mirarla (arreglado hoy: regla A119 y aviso en el cargador) |
| El "86 % de cobertura en enero" | el mismo documento | al resumirlo se perdió que era Tupungatito ausente en el denominador; sin él, enero da 96 a 99 % | el "enero no se usa" de A119, que hay que rebajar (frente B, B-03) |
| S131 cruzó NHI-v1 contra nuestras detecciones: en 4 de 5 volcanes su tasa de alerta iguala a su tasa basal | `docs/s131/agentes/OTRO_SENSOR.md` | no lo cita nadie | el plan de validar el experimental con SWIR: una coincidencia saldría "confirmada" por azar (frente F, F-4) |
| Nicolás pidió reportar la anomalía mayor, como MIROVA (S87, S124) | `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md` | sin puntero en el catálogo | la réplica elige el cúmulo más cercano al cráter (frente A, gravedad 3; **sin verificar por un segundo auditor**) |
| A94 dimensionó la etiqueta `far` en "1 noche de 946" | `CLAUDE.md` | la unidad (noche, todos los sensores) escondió que **por pasada y en MODIS son 68 de 77** alertas | MODIS quedó sin frente propio (frente C, H1) |

Y tres afirmaciones mías de hoy que los auditores corrigieron: "ninguna alerta MODIS depende del OCR" (hay 2
de Láscar en marzo); `evaluar_ventana.py` tira a la basura la salida de error por donde sale el aviso de
A119; y a los hitos de A119 les faltan NOAA-21 y Suomi NPP.

## 2. Restricciones de los datos que todo el plan respeta (frente B)

- **NOAA-21 no está en la tabla de MIROVA antes del 2026-04-09** (0 de 1.003 pasadas de enero a marzo) y sólo
  queda parejo en agosto (92 %). **Suomi NPP aparece en el 23 % de sus pasadas todo el año**, sesgado al borde
  del barrido; MIROVA sí lo procesa (en el OSF de 2025 está parejo con NOAA-20). El OCR es de hecho el canal de
  Suomi NPP.
- Consecuencias: **toda tasa de VIIRS se informa por satélite**; NOAA-20 es el único comparable de enero a
  septiembre; una ventana con los tres satélites parejos parte el 2026-08-01; Suomi NPP no admite una meta de
  "callar donde MIROVA calla" apoyada en la tabla. Por nuestro lado ninguna ventana empieza antes del
  2026-01-29 (hueco de la serie propia). MODIS sólo tiene sustrato de recall entre marzo y junio, y es un solo
  volcán, Láscar (398 alertas desde marzo contra 1 de Llaima y 5 de Copahue).
- Antes del 2026-06-13 decide la tabla sola (A119). `banco_paridad` avisa pero sigue etiquetando positivo con
  el OCR: la separación la hace el evaluador, y tiene que quedar dentro del etiquetador.

## 3. Las brechas, una por una, con lo que el verificador dejó en pie

**VIIRS 375: la palanca está identificada y medida en dos ventanas.** Apagar el Test 1 integrado baja la
publicación en negativos limpios de 86,1 a 28,7 %, y la conectiva de prosa (`max`) a 2,7 % en septiembre y
2,3 % en mayo. El "NO ADOPTAR" de S147 **cae** (frente D, H1): de sus cuatro criterios fallidos, dos ya estaban
caídos (C7, C8) y los otros dos (noches perdidas y magnitud) son un mismo fenómeno que **no es de detección**:
el cúmulo sigue en el cráter y sale con 0,0 MW. El verificador lo confirma en 4 de las 6 pérdidas, con una
corrección: "en el mismo lugar" vale para 2 de las 4 (las dos de Nevados de Chillán). El costo real que queda:
las alertas bajo 0,10 MW (`max` conserva 44 de 52 en mayo y 33 de 39 en septiembre entre 0,05 y 0,10 MW) y la
magnitud.

**VIIRS 750: diagnóstico firme, palanca riesgosa.** Las 28 alertas perdidas desde junio son todas un cúmulo
`summit` con 0,0 MW: el píxel queda bajo la mediana del anillo (1,4 K de mediana) y el exceso se recorta a cero
(`pipeline/process_viirs_mod.py`, cerca de la l. 1034). Pero la misma condición está en **268 de 3.118
negativos limpios**: arreglar el cero "hacia arriba" recuperaría 28 alertas y podría sumar hasta 268
publicaciones falsas (de 23,0 a 31,6 %). Y los 28 cúmulos **no tienen ningún píxel de primer pase**: los puso
el segundo pase, el que corre sin condicionar. La pieza candidata es el fondo por vecinos (D25), cuyos dos
veredictos de apagado cayeron (uno medido con el Test 1 encendido, otro decidido por noches); **tiene que
medirse en los dos sentidos a la vez**. Cuánta magnitud le daría un fondo nuevo a esos negativos está SIN
VERIFICAR, y es lo que decide.

**MODIS: no discrimina, y la etiqueta no es la palanca.** De 77 alertas desde marzo publicamos 9; las 68
perdidas son de Láscar, con un cúmulo de 0,06 a 4,85 MW a entre 0,5 y 3,2 km, etiquetado `far` y oculto. MIROVA
da ahí 0,2 a 3,8 MW: no es pérdida sub-píxel, así que la regla de Nicolás para MODIS no las cubre. Pero la
misma condición está en el **78 % de los negativos limpios**: destapar la etiqueta publicaría casi todo. La
única palanca con respaldo del paper es la banda 22 como primaria (D21), obligatoria además bajo `max` (con
banda 21 el primer pase marca píxeles en 730 de 733 pasadas con `min` y en 3 de 733 con `max`: en ningún caso
detecta). Está en la cola, Láscar de marzo a junio.

**Magnitud.** Entre 0,10 y 0,50 MW la mediana contra MIROVA está en 0,59 a 0,66 (VIIRS 375) y 0,45 a 0,51
(VIIRS 750). Tres papers del grupo dicen que MIROVA suma todos los píxeles alertados (D32); aun sin el Test 1,
139 de 450 cúmulos publicables de VIIRS 375 publican el máximo de 2 o 3 píxeles y no la suma (frente E, E-02;
su vínculo con el 0,6 es SOSPECHA). El 35 % de las alertas de VIIRS 375 recibe hoy su número del recómputo del
Test 1, así que **los A/B viejos de magnitud midieron dos fondos mezclados** y los 25 perfiles de A/B de S124 a
S143 corrieron con el Test 1 encendido (frente D, H3).

**Experimental: hoy no entrega nada** (frente F). Es idéntico a la réplica (de 144 parámetros difieren el
nombre y el directorio), está fuera del cron, si se despacha a mano su salida se pierde, y su página pide un
directorio que no existe. Si la réplica adopta `max` o apaga el Test 1, **el experimental cambia igual y en
silencio**: hay que fijarle los valores de hoy ANTES de esa decisión. Y casi no tiene contra qué validarse: no
existe una tabla de episodios de actividad de OVDAS, y el SWIR de NHI-v1 no discrimina (sección 1).

**Operación** (frente G). La pantalla no bloquea: las vistas leen campos persistidos y sus funciones
duplicadas coinciden. Lo que sí bloquea el día de la adopción: el Test 1 sostiene hoy el 88,9 % de lo
publicado, el record no guarda con qué perfil se produjo y las vistas no marcan cambios de régimen; sin
reprocesar la historia, el operador vería volcanes que "se apagan". Además: token de Earthdata vence el
2026-10-03; la ficha de transparencia está dos cambios atrás; el cron entrega el 43 % de sus corridas.

## 4. El plan, en el orden en que destraba

Regla del plan: **una palanca por vez, con "sin Test 1" como control**, porque con el Test 1 encendido ninguna
otra palanca se puede medir (A114). Única excepción honesta: condicionar el segundo pase y quitar la compuerta
de 3 K van juntos, porque se compensan (S138, S148).

**Fase 0. Poner el conocimiento donde se lee, y arreglar los instrumentos. Sin tocar el pipeline.**
1. Propagar (A113) las decisiones de Nicolás a `CLAUDE.md` (glosario l. 1619), `docs/MISSION.md` y el bloque de
   arranque; marcar el cierre de S27, los dos de D25, las 111 de S131, A94, el "enero no se usa" y la glosa
   "cobertura primero". Puntero a la tabla de terminado y a los documentos de S124 y S131 que nadie cita.
2. Evaluador: recall **por pasada, por tramo de magnitud y por satélite**; separar "perdida por detección" de
   "detectada con 0,0 MW"; sacar el corte de 0,5 MW de VIIRS (`evaluar.py:615`, `parametros.json`, Q4 de la
   caja, P4); la separación tabla contra OCR dentro del etiquetador; hitos de NOAA-21 y Suomi NPP; el `stderr`
   de `evaluar_ventana.py`. Guard nuevo: que el índice de memoria conserve el alcance de cada regla del dueño.
3. Experimental: fijar en su YAML los valores de hoy de la conectiva y del Test 1, y extender su guard para que
   los compare por dirección. Hoy no cambia ningún resultado.
4. Rotar el token de Earthdata (Nicolás) y poner la ficha de transparencia al día.

**Fase 1. Cerrar VIIRS 375.** Terminar la cola de meses (B contra F, abril a agosto) y leerla por pasada, por
tramo y por satélite. Decisión de Nicolás: si el costo bajo 0,10 MW es aceptable en la réplica sabiendo que esa
señal queda visible en el experimental.

**Fase 2. El cero y la magnitud, encima de "sin Test 1".** Brazos: fondo por vecinos (D25) solo y con `max`, en
VIIRS 375 y 750, midiendo a la vez alertas recuperadas y negativos que empiezan a publicar; suma de los píxeles
alertados (Ec. 8 del paper); segundo pase condicionado junto con la compuerta de 3 K. Antes de despachar:
medir sobre datos ya en disco cuánta magnitud le daría el fondo nuevo a los 268 negativos (barato, y decide si
el brazo vale la pena).

**Fase 3. MODIS.** Leer el brazo de banda 22 con y sin `max` (Láscar, marzo a junio, en cola) con el criterio
que propone el frente C: que la tasa de publicación con alerta supere a la tasa sin alerta con intervalos que
no se crucen. Si no separa, decirlo: MODIS queda como sensor limitado y el recall lo cubre VIIRS, que es
coherente con la regla de Nicolás para MODIS pero hay que escribirlo, no dejarlo implícito.

**Fase 4. Adopción.** Verificación a nivel de píxel contra MIROVA, tag defensivo y confirmación explícita
(A45), **reproceso de la historia o marca de régimen en las vistas** (decisión de Nicolás), ficha al día, token
ya rotado. Después, la poda: salen los 9 flags y 15 constantes del Test 1, los 3 flags inertes, `keep_peak` y
la prioridad por rival débil, que quedan sin objeto.

**Fase 5. Experimental.** Día uno: el operacional de hoy congelado (con `min` y Test 1), corriendo y
guardando datos. Después sus criterios propios, que no son los de la réplica (A115). Necesita de Nicolás la
tabla de episodios de actividad de OVDAS y las coordenadas de los rasgos reales (lago de lava de Villarrica,
campo fumarólico de Lastarria, lacolito del Cordón Caulle, cráter El Agrio).

**Lo que NO está en el plan y por qué**: la caja de 5 × 5 km (su adenda está lista, pero sólo se puede leer
encima de "sin Test 1" y no ataca ninguna de las tres brechas grandes); el remuestreo UTM (D17); el disparador
externo del cron. Esperan.

## 5. Metas: la tabla congelada contra lo que MIROVA hace consigo misma (frente C)

| criterio de la tabla del 2026-09-14 | qué dice la variabilidad de MIROVA | propuesta |
|---|---|---|
| publicación en negativos limpios: 10 % focales, 15 % nevados | MIROVA alerta en 19 a 21 % de las pasadas de VIIRS 375, 3 % de las de VIIRS 750 y 0,5 % de las de MODIS | razonable en VIIRS 375; **laxa en VIIRS 750 y MODIS**. Opción: que la tasa falsa no supere la tasa base de alerta del sensor |
| 0 noches perdidas | una noche activa trae cerca de dos pasadas con alerta (MIROVA repite el 53 %; 78 a 85 % cerca del nadir, 29 a 33 % en el borde); de junio a agosto VIIRS 375 perdió 29 pasadas, 23 bajo 0,10 MW, y fueron sólo 10 noches de 248 | **laxa en VIIRS y choca con la regla de Nicolás**: medir por pasada y por tramo de magnitud; la noche queda informativa. En VIIRS 750 la referencia es MIROVA, no "respecto de hoy" |
| magnitud entre 0,8 y 1,25 por volcán | MIROVA contra sí misma (su 750 sobre su 375, misma escena) da 1,10 en Láscar, 0,72 en Isluga y 1,31 en Cordón Caulle; entre pasadas de una noche su magnitud cambia por un factor 1,8 a 2 | **estricta por volcán**: cumple la condición de reapertura que la tabla declara. Opción: mediana agregada por sensor dentro de la banda y sin pendiente por tramo. Salvedad: compara dos resoluciones, con 11 a 34 pares |
| MODIS | una alerta en septiembre; sustrato sólo marzo a junio en Láscar | meta de forma: separación entre alertas y negativos |

## 6. Decisiones que quedan para Nicolás

1. **Las metas**: ¿se reabre la tabla del 2026-09-14 en los tres puntos de la sección 5? Recomendación: sí, por
   pasada y por tramo en VIIRS, mediana agregada en magnitud, y tasa falsa acotada por la tasa base del sensor.
2. **El costo bajo 0,10 MW en VIIRS 375**: ¿aceptable en la réplica si queda visible en el experimental?
   Esperar a leer los meses antes de contestar.
3. **La historia el día de la adopción**: reprocesar (MODIS sólo en GitHub Actions, con el token recién
   rotado) o marcar el régimen en las vistas. Recomendación: reprocesar desde el 2026-01-29 y además marcar.
4. **El experimental el día uno**: ¿el operacional de hoy congelado? ¿se le muestra al operador? ¿con qué
   cadencia?
5. **MODIS**: si la banda 22 no separa alertas de negativos, ¿se acepta escribir que MODIS es un sensor
   limitado en la réplica?
6. **La anomalía mayor contra la más cercana al cráter** (S87, S124): confirmar cuál es tu regla hoy.
7. Tuyos y sin mí: rotar el token antes del 2026-10-03; la tabla de episodios de OVDAS; las coordenadas de los
   rasgos reales.

## 7. Lo que esta auditoría no cubrió, dicho

- El tramo de veredictos de S124 a S133 se cubrió por búsqueda dirigida, no leyendo las auditorías enteras.
- El frente A leyó enteros 16 de los 53 archivos `feedback_*`; el resto por búsqueda de cadenas.
- El frente E no abrió Campus 2022, Campus 2024 ni el capítulo de Coppola; lo de VIIRS 750 más allá de los
  flags es heredado de la matriz de S138.
- Casi todo lo medido es de septiembre y de mayo de 2026. Nada de esto se vio en un navegador real.
- Sólo el hallazgo central pasó por verificador con contexto limpio. Los de gravedad 4 de los frentes A, B, F
  y G no: E-01 lo comprobé yo por `git log`; el resto queda con la confianza que declara su auditor.
