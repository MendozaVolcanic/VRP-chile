# Protocolo de auditoría profunda — buscar el error arrastrado

> Escrito al cierre de S124, cuando tres auditorías adversariales encontraron
> que el veredicto de esa misma sesión estaba mal en dos puntos. La pregunta que
> lo motiva es de Nicolás: *"¿qué más habremos concluido mal en estos meses?"*

## Por qué existe

En **una sola sesión**, aplicando estas técnicas, aparecieron:

- un volcán **escondido** de la tabla de un veredicto por un alias faltante — y
  era el único con daño real;
- una correlación publicada (**r = −0,47**) que con la variable correcta daba
  **+0,054**, y sin script detrás;
- un reproceso que cerró **en verde sin tocar nada** (tres meses de datos
  idénticos byte a byte);
- una función escrita hace **26 sesiones** para resolver exactamente el problema
  que estábamos atacando, **nunca cableada**;
- **tres reglas vinculantes** falsas u obsoletas, una de ellas diciendo "no
  reabrir" sobre el frente correcto;
- una figura que mezclaba **dos meses de datos** fuera de su ventana declarada.

Ninguno se veía. Todos aparecieron al **verificar en vez de confiar**.

Escala del terreno: **71 reglas A** · **32 auditorías previas** · **8
divergencias catalogadas** · **114 archivos de test** · **102 experimentos** ·
**39 perfiles A/B**.

---

## Las 8 técnicas que probaron encontrar errores

Cada una está validada: encontró algo real en S124. **No inventar técnicas
nuevas antes de aplicar éstas** — su tasa de acierto ya está medida.

### T1 · Verificar cada afirmación contra un script que la reproduzca

Toda conclusión citada en un doc debe poder recomputarse **hoy**. Si el número
no sale de correr algo, es una afirmación sin respaldo.

- **Encontró**: que ~45 % de las afirmaciones centrales de S124 no tenían script.
- **Cómo**: correr el script que el doc cita y comparar salida contra texto.
- **Señal de alarma**: docs que citan números sin nombrar el script, o que
  nombran uno que no calcula ese número.

### T2 · Buscar la trampa del nombre (alias, campo, nivel del YAML)

- **Encontró**: PCC escondido de la tabla (`"Puyehue-Cordon Caulle"` con guion);
  `local_kernel_bg` vs `..._compatible`; `enable_utm_regrid` bajo `thresholds:`
  y no en la raíz.
- **Cómo**: para todo diccionario de alias, verificar contra los valores REALES
  del CSV (`sorted(set(df.Volcan))`). Para todo flag,
  `VRP_PROFILE=<p> python -c "import pipeline.profile as p; print(p.<FLAG>)"`.
- **Por qué es traicionera**: falla en silencio. No hay excepción, no hay log —
  simplemente el volcán no aparece o el flag queda apagado.

### T3 · Distinguir "sin efecto" de "efectos que se cancelan"

- **Encontró**: «la grilla no hace nada» era una mediana de 0,000 que promediaba
  Láscar +0,11 y PCC −0,10.
- **Cómo**: nunca reportar una mediana de diferencias sin la **distribución**.
  Contar cuántos suben, cuántos bajan, y mirar los extremos.
- **Corolario**: «ratio 1,00» tapaba que 190 de 274 pasadas tenían ratio ≠ 1.

### T4 · Verificar que un reproceso tocó los datos

- **Encontró**: el bug del merge — jun/jul/ago **100 % idénticos byte a byte**
  tras un run verde.
- **Cómo**: `python experiments/_s124_ndc_focus/05_verificar_reproceso.py <json>`
  compara contra el commit previo. Sale con código 1 si hay meses sin tocar.
- **Cuándo**: tras **todo** reproceso sobre un `data_subdir` que ya tenía datos.

### T5 · Buscar capacidad construida y no conectada

- **Encontró**: `get_grid_center()` (S98, 26 sesiones sin uso), el módulo
  TIRVolcH completo, `mirova_eq_vrp` con la lógica canónica triplicada a mano en
  el frontend, 15.606 PNG y 1.965 KMZ del archivo sin lectores, 21 campos
  `diag_*` invisibles al dashboard.
- **Cómo**: alcanzabilidad transitiva desde los entry points de los workflows.
  Lo llamado **solo desde `tests/`** es la señal más fuerte: testeado y no
  cableado.

### T6 · Verificar las reglas vinculantes contra el código

- **Encontró**: A13 falsa, A36 obsoleta, A82 apoyada en una auditoría que nunca
  miró el eje relevante.
- **Cómo**: separar las reglas con afirmación **falsable** (algo está activo,
  un campo se llama así, un archivo está ahí) de las de método puro, y
  verificarlas una por una.
- **Prioridad**: las que dicen *"cerrado"*, *"agotado"*, *"no reabrir"*. Si una
  de ésas se apoya en un experimento hoy sospechoso, está bloqueando trabajo
  válido.

### T7 · Auditoría adversarial de lo que se le muestra al usuario

- **Encontró**: 9 problemas en las figuras, 3 graves — entre ellos una
  conclusión mía que era espuria por triple confusión, y una figura que mezclaba
  mayo en una serie titulada "desde junio".
- **Cómo**: subagente con instrucción explícita de **romper** la figura, con
  todo el contexto de datos pero sin el historial de la conversación.
- **Chequeo específico**: ¿lo que la leyenda DICE coincide con lo que el código
  HACE? ¿los filtros son simétricos entre las series comparadas?

### T8 · Poder estadístico antes de afirmar una diferencia

- **Encontró**: los IC de control y brazo B **se solapaban en los 10** volcanes;
  6 de 10 cruzaban el borde de banda. El "juez" del experimento tenía un IC que
  cruzaba el umbral.
- **Cómo**: `experiments/_s124_f70/05_poder_estadistico.py` (bootstrap 5000).
- **Regla**: una mediana sin intervalo no decide nada.

---

## Cómo aplicarlo — orden por rendimiento esperado

El terreno es grande; conviene barrer donde el costo de un error es mayor.

### Fase 1 — Lo que hoy gobierna decisiones (máxima prioridad)

1. **Las 71 reglas A** con T6. Empezar por las 12 que dicen "no reabrir" o
   "cerrado": son las que apagan trabajo futuro.
2. **Las 8 divergencias del catálogo** (D2, D3, D11 a D17) con T1: ¿el
   experimento que cerró cada una es reproducible hoy?
3. **`MISSION.md`** entero con T6: ya sabemos que declara removidos dos parches
   que siguen activos (pisos VRP y máscara de nube).

### Fase 2 — Las adopciones que cambiaron el operacional

Cada flag en `true` dentro de `mirova_equivalent.yaml` fue una decisión con
A/B detrás. Para cada uno: ¿el A/B que lo justificó tiene script reproducible?
¿comparaba pasadas comunes? ¿reportó distribución o solo mediana? ¿el alias de
volcanes estaba completo?

Sospechosos por construcción: los adoptados **antes de S124**, cuando no
existían T2, T3, T4 ni T8 como reglas.

### Fase 3 — La cadena de magnitud (nunca auditada)

La detección se auditó file:line contra Coppola 2016a en S114. **La magnitud
jamás.** Y el sesgo es factor 2 en 4 de 11 volcanes. Auditar Eq. 6-8 con el
mismo rigor: fondo, área de píxel, coeficiente, integración.

### Fase 4 — Capacidad dormida

T5 completo. Los tres candidatos ya identificados: cablear
`get_grid_center()`, reactivar el índice de imágenes (congelado desde S90), y
leer los `<LatLonBox>` de los KMZ (que ya contradicen el `half_km=25.5` fijo).

---

## Regla de salida

Cada hallazgo se clasifica y se actúa distinto:

| clase | qué hacer |
|---|---|
| **Falso** (el dato lo contradice) | corregir el doc/regla **citando la evidencia**, conservar el texto original por historia |
| **Obsoleto** (fue cierto, ya no) | marcar con la sesión en que dejó de valer y por qué |
| **Sin respaldo** (puede ser cierto, nadie lo probó) | **no borrar**: rebajar de "cerrado" a "abierto pendiente de prueba" |
| **Confirmado** | anotar el comando que lo confirma, para no re-auditarlo |

**Lo que NO se hace**: borrar una conclusión porque suene mal, o rehacer un
experimento cuyo resultado ya es reproducible. La auditoría busca **errores**,
no repetir trabajo válido.

---

### T9 · Verificar que lo declarado coincide con lo efectivo

**Qué busca**: afirmaciones que el sistema hace sobre sí mismo —en comentarios,
docstrings, cabeceras de perfil, mensajes de commit y notas de sesión— que nunca se
contrastaron contra su comportamiento real.

**Por qué existe**: S126 encontró **doce** instancias sin buscarlas, ocho de ellas
persiguiendo otra cosa. Un comentario que decía «no-op» apagó la máscara de nube en
producción; dos claves de YAML declaraban valores que el código nunca lee, en 31
perfiles. S127 barrió el eje a propósito y encontró más:

| lo declarado | lo efectivo |
|---|---|
| docstring: «Volcanes NO afectados … Láscar, Villarrica, Copahue, Isluga, Lastarria, Llaima, NdC» | falso para **los siete**; Láscar es el **más** afectado de la flota (33,9 %) y Tupungatito —para el que se construyó el modo— el **menos** (7,5 %). Copiado en 13 perfiles, incluido el operacional |
| `_s124_kernelbg_ab.yaml`: «la rama del kernel nunca corre en producción» | corre en **5 de los 11** Tier A |
| corona Eq.6 cableada en VIIRS375 y MODIS | anulada aguas abajo: 1.164 de 1.179 records en VIIRS375, y el **100 %** en MODIS |

**Cómo se aplica**: los barridos de `experiments/_s127_declarado/`. El 01 inventaría las
afirmaciones (221 en el repo, 123 en `pipeline/` y `.github/`); la verificación de cada
una es manual y se persiste con su propio script.

**El sub-patrón dominante: el nombre en el punto de uso no es el nombre en la
definición.** No da error — da **cero resultados**, y el cero se lee como ausencia. En
S127 apareció **cinco veces**, en tres formas distintas:

| forma | ejemplo | el falso negativo |
|---|---|---|
| el parámetro no se llama como la clave | `local_kernel_bg_compatible` (firma) vs `local_kernel_bg` (YAML), con `run_pipeline.py:244` de puente | «el kernel no corre en ninguno» — corre en 5 de 11 |
| la clave se lee de otra sección | `enable_utm_regrid` escrito en la raíz, leído de `thresholds:` (S124) | el flag arrancaba siempre apagado; el A/B habría corrido 4 brazos idénticos |
| la llamada es calificada o renombrada | `store.append_record(`, `from pipeline.vrptir import vrp_tir_mw as _aveni_vrp_tir_mw` | «nadie la llama» sobre funciones que corren en cada granule |

**Antes de concluir «esto no se usa en ningún lado», trazá cómo lo lee el código** (A6),
no cómo se llama donde está definido. Un `grep` del nombre de la definición es
justamente el instrumento que no sirve para esta pregunta.

Y el corolario incómodo: las cinco veces el error fue de quien estaba **auditando**, no
de quien escribió el código. La técnica se equivoca en la misma dirección que el defecto
que busca.

**Señal de que hay que aplicarla**: cualquier frase de la forma «esto no cambia nada»,
«esto ya no se usa», «esto sólo afecta a X», «está apagado en todos». Las cuatro fueron
falsas al menos una vez.

**La regla que lo resume**: *una afirmación sobre el estado del sistema necesita un test
detrás, o no es una afirmación — es una intención.*

**Cómo se cierra**: con un guard, no con una corrección. Corregir la lista la deja
envejecer de nuevo; el arreglo correcto es **borrarla y apuntar al script que la mide**
(`tests/test_guard_afirmaciones_de_alcance_s127.py` prohíbe declararla y permite citarla
como historia, distinguiendo por contexto).

---

# Cómo se audita, medido — las tres reglas que salieron de auditar las auditorías

> S128. Se midió el rendimiento de las once auditorías del proyecto. Lo que sigue no es
> opinión de método: es lo que dijeron los números.

## El hallazgo: el rendimiento es del EJE, no de la profundidad

Fracción de hallazgos provenientes de un **eje de comparación nunca usado antes**:

| auditoría | eje nuevo | hallazgos que movieron el pipeline |
|---|---|---|
| S105 | **0 %** | ninguno |
| S122 | ~8 % | ninguno |
| S116 | ~17 % | ninguno |
| S123 | ~20 % | ninguno |
| S125 | ~35 % | el factor 2 en magnitud |
| S119 | ~50 % | el mapa de gaps por etapa |
| S114 | ~58 % | el cierre de D11 |
| S121 | ~63 % | poda y arqueología de backlog |
| S124 | ~70 % | la grilla UTM |
| S127 | **~75 %** | la corona anulada aguas abajo |

Las cuatro auditorías con menos del 20 % de eje nuevo produjeron **sólo deuda documental**.
Las cinco con 50 % o más produjeron **todos** los veredictos que cambiaron el pipeline.

**Regla A — está prohibido repetir el barrido general** de 6-8 ejes (misión / código /
reglas / data / git / docs). Rindió 0 % en S105 y ~8 % en S122. Cada auditoría debe estrenar
al menos un eje que ninguna haya usado, y declararlo al abrir.

## Las dos fugas que explican por qué siempre queda inventario

**Fuga 1 — cerrar con prosa.** Nueve hallazgos se redescubrieron en más de una auditoría:

| hallazgo | veces |
|---|---|
| `diario.html` sin cap de 50.000 MW | **4** |
| gates intra-radio S84/S85 encendidos | 3 |
| `docs/INDEX.md` congelado | 3 |
| poda de `data/` | 3 |
| PAT en `settings.json` | 3 |
| contradicción del GAP #A | 3 |
| conmutación per-volcán vs MISSION | 3 |
| «tif-archive stale» — **refutado en S121 y reafirmado igual en S125** | 3 |

S127 fue la única que cerró con tests (3 guards) y es la única sin reincidencias.

**Regla B — cierre por guard, obligatorio.** Ningún hallazgo pasa a CONFIRMADO / FALSO /
OBSOLETO sin un test que lo mida, o la razón escrita de por qué no se puede medir.

**Fuga 2 — declarar sin verificar.** S121 cerró con **19** hallazgos «sin verificación
individual»; S125 con **9** «sin respaldo». Ese inventario es, literalmente, la materia
prima que la auditoría siguiente reporta como nueva.

**Regla C — los pendientes se publican y son la puerta de entrada.** Cada auditoría cierra
con tres números —confirmados / refutados / pendientes— y la siguiente **empieza** por los
pendientes antes de abrir eje nuevo.

## Registro de ejes de comparación

El protocolo listaba nueve *técnicas* y ningún *eje*. Los ejes son contra qué se compara:

| eje | último uso | rendimiento |
|---|---|---|
| código vs código | S105, S116, S122 | bajo |
| docs vs código | S123, S125, **S127 (T9)** | **alto** |
| nuestros datos vs el CSV de MIROVA | continuo | medio, y es el único que se repite |
| código vs paper, file:line | S114 (detección), S125 (magnitud) | **alto** |
| figuras vs datos | S124 | **alto** |
| clasificación física de FP | S86 | alto, **nunca recomputado** |
| transparencia legal CPLT 372 | S116, S127 | medio |
| matriz sensor × mecanismo | S127 | **alto** |
| auditar las auditorías | S128 | **alto** (produjo esta sección) |
| **evidencia exógena: TIF/KMZ por pasada** | S126 (2 usos puntuales), **S131** (control de instrumento) | 2 de 2 dieron vuelta una creencia; **S131 refutó el GeoTIFF como árbitro de POSICIÓN** (error mediano 4,80 km vs `Distancia_km`, pierde contra el nulo «está en el cráter» en MODIS/V750) — sirve para confirmar, no para arbitrar |
| **evidencia exógena: papers verbatim** | A35 (1 uso), **S131** (Coppola 2014 §2.2 + ATBD VIIRS Tabla 2.2-1) | 2 de 2: el remuestreo es una ley de área; el docstring de `viirs_pixel_areas` tenía el multiplicador por eje leído como área |
| **evidencia exógena: otro sensor (NHI, Landsat)** | **S131** (1 uso, NHI-v1 SWIR S2+Landsat) | **medio**: confirmó el FN A77 de NdC con evidencia independiente y mostró que nuestras detecciones sin MIROVA no se distinguen de la actividad crónica (A54); basal demasiado alta para gate automático |
| **ATBD del sensor vs código** | **S131** | **alto**: 4,38× vs tope 2,0× en `scan_geometry.py` |
| **utilidad para el operador (dashboard como producto)** | **S131** (mitad B del eje dashboard) | **alto**: badge 100 % «Muy Bajo» en 4.279 ventanas; semáforo HTML fijo; 23,7 % de detecciones visibles con MIROVA de la misma pasada y el dato sólo en el popup |
| idempotencia y estabilidad temporal | S128 | **alto** (93 % de pares con esquema mixto) |
| ground truth end-to-end | S128 | **alto** (MODIS sólo existe en Láscar) |

**El patrón de la última columna es el punto**: los tres ejes exógenos suman cuatro usos en
127 sesiones, y los cuatro encontraron algo. Es el terreno menos explorado del proyecto.
