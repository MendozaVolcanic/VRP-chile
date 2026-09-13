# Bloque de arranque S138

> Cierre de S137 (2026-09-12 al 2026-09-13, hora del servidor 11:29 UTC). Rama `main`, verificado
> contra el remoto. Suite **1325 passed**, 4 skipped, 2 xfailed. No hay runs en curso ni trabajo en
> vuelo: los diez PRs de la sesión (#627 a #636) están mergeados y el NRT sigue produciendo (último
> verde 2026-09-13 08:57 UTC). Los commits automáticos del cron seguirán aterrizando sobre `data/`;
> no invalidan nada de esto.
>
> `git cherry` marca dos ramas `s137-*` como "sin integrar": es el squash, que cambia el patch id.
> Verificado archivo por archivo que su contenido está en `main`. No las reintegres.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| El cierre de S136 ("sigma irrelevante") era **circular**: valía sólo bajo la conectiva `min`, que S136 mismo refutó | documentado | `experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md`, PR #627 |
| **La banda 21 fabrica el primer paso de MODIS**: con B22 (la del paper) el sigma del dNTI cae 3,5 a 4,7× y el primer paso queda vacío en 80 de 84 escenas | medido | `RESULTADO_SIGMA_DNTI.md`, run 34706563697, PR #630 |
| **La compuerta `bt > t_bg + 3 K` elimina el cráter de Villarrica** en la pasada de la figura A6; el paper no la tiene | causa verificada | `RESULTADO_ETAPA_Y_FIGURAS.md`, run 34746870643, PR #633 |
| **Sigma del dNTI de MIROVA medido en sus figuras**: ~0,0008 contra 0,0076 (B21) y 0,0016 (B22) nuestro, misma escena | medido, control de mediana pasa | `medir_figuras_apendice.py` → `out_figuras/figuras_apendice.json` |
| **Eyjafjallajökull**: el autor detecta a 9,5-9,7 km, rumbo 83°; con B22 publicamos ahí; hoy publicamos otra cosa a 3,1 km | medido en la figura A2 | mismo doc, PR #633 |
| Batería del Apéndice A, 8 brazos: el mejor (B22 + sin compuerta + fondo local + prosa) da **5/6 y 3/3**; hoy 6/6 y 0/3 | corrido, **ningún brazo cumple** | `RESULTADO_FONDO_LOCAL.md`, `COMPARACION_8_BRAZOS.txt`, PR #636 |
| D21 (banda 21 primaria) y D22 (compuerta en Tests 2/3) | registradas | `docs/MIROVA_DIVERGENCES.md`, PR #634 |
| Indicador de corroboración MIROVA por volcán en el dashboard (D5 de S134) | **en producción** | PR #628; Llaima 0 alertas en 90 d, verificado por dos vías |
| Recomendé correr el A/B de `keep_peak` que **ya estaba corrido** en S135 (ningún brazo cumple) | corregido en la sesión | `EL_AB_DE_D1_YA_ESTABA_CORRIDO.md`, PR #629; tag falso borrado |
| Plan de auditoría S138, seis ejes en paralelo más verificador | escrito | `docs/PLAN_AUDITORIA_S138.md` |
| Nada a medias, nada en rama sin mergear | verificado | `git cherry` + diff por archivo |

## b. Decisiones que esperan a Nicolás

| # | pregunta | opciones | mi recomendación |
|---|---|---|---|
| 1 | Las dos correcciones que hoy sólo viven en la batería (compuerta fuera de los Tests 2/3; fondo local uniforme) ¿se implementan como **flags apagados** en `pipeline/` para poder correr el A/B en los Tier A? Toca `process_*.py` y `detection_context.py`: **A45, tag y tu confirmación** | (a) sí, con tag y tests; (b) no | **(a)**, después de la auditoría S138 (eje 5 entrega el pre registro). Es la única forma de saber si esto vale fuera de nueve escenas |
| 2 | ¿Qué conectiva lleva ese A/B? | (a) prosa `max`; (b) fórmula `min`; (c) los dos brazos | **(c) los dos**, pero la prosa es la única que curó los tres negativos; la fórmula da un "conforme" espurio en A2 y sigue con Dubbi |
| 3 | La batería evalúa A2 dentro de 5 km y el autor detecta a 9,6 km. ¿Se corrige la evaluación con la posición de la figura? | (a) sí, desde la próxima serie; (b) no | **(a)**, desde la próxima serie y sólo tras medir las 9 figuras (eje 5), para no mover el criterio sobre resultados ya vistos |
| 4 | D1 de S134 (`keep_peak`): el A/B ya corrió y **ningún brazo cumple** | (a) adoptar B aceptando la paridad por dos centésimas; (b) no adoptar y mover el frente al Test 1 integrado; (c) dejar | **(b)**: adoptar B exige mover un criterio después de ver el dato |
| 5 | D4 de S134 (coordenada de Isluga): reformulada. `vent_lat` es el centroide a 2 decimales y el `mirova_center` del KMZ está 0,37 km al SW, hacia donde está el foco | (a) usar el `mirova_center` como ancla (es D17); (b) dejar | **(a)** dentro de D17, no como refinamiento con DEM (eso sería divergir del paper) |
| 6 | La auditoría S138 ¿se lanza antes de tocar nada? | (a) sí; (b) primero el A/B | **(a)**: el eje 1 revisa justamente las afirmaciones que dirían si el A/B tiene sentido |

Las decisiones de S134 §D (D2, D3, D6, D7, D8), S135 y S136 (#1 a #5) siguen abiertas; el eje 6 de la
auditoría las junta en una sola tabla con estado real.

## c. Lo aprendido

**Regla del proyecto, A95.** *Un corolario que cierra frentes hereda las premisas de la lectura con
que se derivó; si esa lectura se refuta en la misma sesión, el cierre cae con ella.* S136 refutó `min`
con la batería y cerró tres frentes con un corolario que sólo valía bajo `min`. Y `CLAUDE.md` decía
"NO quedan gaps de fidelidad literal" mientras faltaban la banda primaria, el remuestreo, el bow tie y
una compuerta que el paper no tiene. Cómo aplicarla: ante toda afirmación "cerrado", preguntar bajo
qué lectura del paper vale y comprobar esa lectura contra el PDF, no contra el `.txt` ni contra docs
previos. Va a `CLAUDE.md`.

**Regla general del workspace, A96.** `git stash -u` con el árbol limpio no crea entrada, y `git stash
pop` reaplica el stash MÁS RECIENTE de la lista, que puede ser ajeno. En S137 reaplicó "WIP audit
fresh" de S78 sobre `data/` (conflicto en Tupungatito.json). Nunca `stash pop` sin `git stash list`.
Memoria: `feedback_s137_stash_pop_ajeno.md`.

**Regla general del workspace.** `git cherry` da falsos "sin integrar" con squash merges. Verificar
por contenido (`git diff <rama> main -- <archivos>`), no por identificador de commit.

**Trampa de medición, la de la sesión.** La primera versión de `medir_figuras_apendice.py` armaba la
tabla color valor con los extremos de la barra y leía su marco negro como escala. La delató el control
pre registrado (mediana del dNTI, que es cero por construcción, salió en −0,0007). Sin ese control
el sigma del autor habría salido mal y nadie lo habría notado. Confirma la regla S128: control de
instrumento antes del veredicto.

**Trampa de método, A8 otra vez.** Recomendé un A/B ya corrido porque el traspaso listaba decisiones
sin marcar cuáles ya se ejecutaron. Síntoma: una decisión "de flags" que lleva tres sesiones abierta
rara vez sigue sin medirse. Antes de recomendar correr algo, `ls experiments/ docs/` por el nombre.

**Método que rindió.** El probe por etapa (A75) sobre UNA pasada, la de la figura del paper, convirtió
"Villarrica se pierde" en "cae por la compuerta, por 7 K, con dNTI 0,0121 pasando incluso `max`". Una
escena bien elegida vale más que 84 mal preguntadas.

**Sobre el modelo.** La sesión corrió en Opus y cerró en Fable 5.1. Si la próxima lanza agentes en
Fable, leer `GUIA_PROMPTING_prompting-claude-fable-5-1.md` antes (el hook lo recuerda).

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en esta sesión)

- Con B21, 55 a 60 píxeles por escena nocturna pasan los Tests 2 y 3 en Láscar y Villarrica; con B22,
  cero en 80 de 84 escenas (run 34706563697).
- En la pasada de la figura A6 (Villarrica 2009-06-24 05:55), con B22 el cráter tiene dNTI 0,0121 y
  dETI 0,0140, pasa los Tests 2 y 3 incluso con `max`, y cae sólo por `bt > t_bg + 3 K` (268,3 contra
  275,3 K). Sin la compuerta detecta; con el fondo del anillo su VRP es 0,0; con fondo local, 0,539 MW.
- La compuerta nació el 2026-04-08 (`59846e897`) para el camino del NTI absoluto, cuyo comentario decía
  "We don't implement dNTI/dETI"; hoy está en unos 13 lugares de los tres sensores.
- El remuestreo a 1 km NO baja el sigma del dNTI (lo sube 13 a 15 %); no es palanca de ruido.
- El A/B de D1/D2 (keep_peak, segundo pase) corrió en S135 con ventana completa: ningún brazo cumple.
- El fondo local ya está encendido en producción para 5 volcanes (opt-in: PCC, Villarrica, Chaitén,
  Planchón-Peteroa, Lastarria); la batería corría sin él.
- Isluga: `vent_lat` = `lat` a dos decimales; `get_grid_center()` no la llama nadie en producción
  (D17 sigue viva).

### SOSPECHA (no verificado)

- Que el sigma del dNTI de MIROVA sea ~0,0008: es una medición sobre un raster de imprenta, con sesgo
  hacia abajo por el suavizado. El orden de magnitud es firme; el número no.
- Que la anomalía de A2 a 9,6 km sea la erupción de flanco de Fimmvörðuháls (empezó el 20 de marzo de
  2010). Consistente con la figura, no verificado con una fuente externa.
- Que en VIIRS 375 la compuerta cueste lo mismo que en MODIS. No se midió nada en VIIRS.
- Que las tres correcciones juntas no sobreajusten: nueve escenas no lo descartan. Lo decide el A/B
  Tier A con holdout de noches MIROVA.
- Que el sigma excepcional de A2 04:40 con B22 (0,0165, el remuestreo lo baja a 0,0029) sea geometría
  de esa pasada. No afecta el veredicto de A2.

## e. Cerrado en esta sesión, no rehacer

1. **El A/B de `keep_peak` (D1/D2).** Corrido en S135, dos chunks verdes, 260 noches. No correrlo.
2. **El remuestreo como palanca del ruido del dNTI.** Medido: sube sigma. (Sigue abierto como fidelidad
   literal, D17/D18, y como reparto de un foco sub píxel; no como reductor de ruido.)
3. **"La banda 22 no puede mover la detección"** (S136). Refutado: la mueve incluso bajo `min`.
4. **"El 6 de 6 de hoy es sólido."** No: en A2 el conforme de hoy es un cúmulo a 3 km al SE de la
   cumbre, no el objeto del autor a 9,6 km al E.
5. **El tag `pre-s137-keeppeak-ab`.** Borrado a propósito; no hubo A/B que respaldar.
6. Y de antes sigue vigente lo cerrado en S136 (nueve caminos), con la salvedad de que los tres frentes
   apoyados en el corolario de sigma **vuelven a estar vivos bajo `max`**: pool de mu y sigma, retiro de
   los Test 1 del pool, y C2. Bajo `min` siguen cerrados.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S138. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line | tail -3        # esperado: 1325 passed
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"   # A86
  gh run list --workflow=nrt.yml --limit 3                          # el NRT sigue vivo?

Lee en este orden, comprobando contra el codigo de hoy lo que cada uno afirme:
  1. tasks/BLOQUE_ARRANQUE_S138.md          <- este archivo, con las 6 decisiones de Nicolas
  2. docs/PLAN_AUDITORIA_S138.md            <- el plan de la auditoria, seis ejes + verificador
  3. ../../GUIA_MAESTRA_AUDITORIAS.md       <- ENTERA, antes de escribir un solo prompt de auditor
  4. docs/_prompts/PREAMBULO-AUDITOR.md     <- se pega ENTERO en cada prompt
  5. ../../GUIA_PROMPTING_prompting-claude-fable-5-1.md   <- si los agentes corren en Fable
  6. experiments/_s137/RESULTADO_FONDO_LOCAL.md  <- el resultado que ordena el frente (5/6 y 3/3)
  7. docs/MIROVA_DIVERGENCES.md, D21 y D22   <- lo nuevo del catalogo

EL TRABAJO: la auditoria S138, en este orden.

  1. Confirmar con Nicolas la decision 6 (lanzar la auditoria antes de tocar nada). Si dice que si:
  2. Lanzar los SEIS agentes del plan EN UN SOLO MENSAJE (paralelo real), uno por eje, read-only,
     cada uno escribe docs/audit_s138/EJE_<n>_<nombre>.md y devuelve un resumen < 400 palabras.
     Sin worktrees (no escriben en git; y el disco tiene 5,9 GB libres). Maximo dos con red
     externa a la vez. Ninguno dispara CI. Prompt de cada uno = preambulo canonico + su seccion del
     plan + "cobertura primero, CONFIANZA y GRAVEDAD por hallazgo, no filtres".
       Eje 1: afirmaciones "cerrado/agotado/fiel" contra el PDF y pipeline.profile (T6)
       Eje 2: matriz de conformidad construida DESDE el PDF, 3 sensores, file:line, valor efectivo
       Eje 3: verificador limpio de los 5 instrumentos de S137 (recibe SOLO titulos, rutas, scripts)
       Eje 4: D21/D22 y el fondo en VIIRS, sobre data/ read-only, con denominador y ventana (A90)
       Eje 5: la bateria como instrumento: las 9 figuras medidas, sensibilidad, pre-registro A/B
       Eje 6: tabla unica de decisiones S134-S137 con estado real + NRT + higiene (ramas, stashes)
  3. Verificar TU los hallazgos criticos antes de aceptarlos (A48, A89). Luego lanzar el
     verificador limpio (agente 7) con SOLO los seis archivos y los scripts que citan.
  4. Escribir docs/AUDIT_S138.md con la regla de salida: >3 contradicciones entre fuentes = se
     pausa el frente y se consolida (A51). Actualizar docs/INDEX.md.
  5. Recien entonces, si Nicolas aprueba la decision 1: tag defensivo, flags apagados con tests, y el
     A/B Tier A con el pre-registro del eje 5. Eso ya es probablemente S139.

REGLAS DURAS QUE NO SE NEGOCIAN:
  - Tocar pipeline/process_*.py, detection_context.py, store.py o mirova_equivalent.yaml exige
    tag defensivo Y confirmacion explicita de Nicolas (A45). El tag va ANTES del primer edit.
  - Antes de recomendar correr un experimento, buscar si ya corrio: ls experiments/ docs/ por el
    nombre (A8/A50). En S137 casi se repite el A/B de keep_peak.
  - Ante toda afirmacion "cerrado": bajo que lectura del paper vale, y comprobarla en el PDF con
    PyMuPDF, nunca en documentacion/sp426_5.txt (corrompe los operadores) ni en docs previos (A95).
  - Ningun numero transcrito a mano: el script que lo persiste es la fuente (S91). Todo conteo
    lleva denominador y ventana (A90) y sale de la definicion del conjunto que nombra (A93).
  - Flags: leer pipeline.profile, nunca el YAML (A89). Dos llaves (flag + campo por volcan) para el
    fondo local: si solo se enciende una, el brazo corre igual al control sin avisar.
  - git: nunca `stash pop` sin `git stash list` (A96); `git cherry` miente con squash: verificar por
    contenido. Los 4 stashes viejos (S72-S78) no son tuyos: no los toques.
  - NADA de guiones largos ni medios en ningun archivo, mensaje o commit. Verificar con Python.
  - Espanol de Chile, formas de tu, nunca voseo. Fenomeno fisico primero, numeros al final.
  - Subagentes son volumen, no fuente de verdad (A48): cruza cualquier "esto esta muerto" con A89.

SI LA SESION NO ALCANZA: cierra con /cierre. Los seis archivos de docs/audit_s138/ se commitean
aunque el verificador no haya corrido; se anota cual falta. Nada queda solo en la conversacion.
```
