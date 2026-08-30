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
