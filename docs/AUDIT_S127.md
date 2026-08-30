# Auditoría S127 — «lo declarado no coincide con lo efectivo»

> Todos los números salen de scripts que los persisten (S91). Ninguno transcrito a mano:
> `experiments/_s127_declarado/0{1,2,3}_*.py` → sus `.json` de al lado.
>
> **Fase 1 completa.** La Fase 2 (eje geométrico D17, matriz sensor × tratamiento,
> higiene de `experiments/`) queda pendiente — ver «Lo que falta» al final.

## Por qué esta auditoría, y por qué no es la general

A51 pide auditoría cada 20 sesiones y hubo **tres en cuatro** (`AUDIT_S123`, `AUDIT_S124`,
`AUDIT_S125_PROFUNDA`). Repetir el barrido completo sería el anti-patrón A8.

Lo que ninguna cubrió es el eje que S126 encontró por accidente **doce veces**: afirmaciones
que el sistema hace sobre sí mismo y que nadie contrastó contra su comportamiento. Ocho de
las doce aparecieron persiguiendo otra cosa. Un eje con esa tasa de acierto, nunca barrido,
es la mejor inversión disponible — y es ahora la técnica **T9** del protocolo.

## El inventario

`experiments/_s127_declarado/01_afirmaciones_de_estado.py` barre comentarios y docstrings
buscando ocho clases de afirmación (*«esto es no-op»*, *«esto ya no se usa»*, *«sólo afecta
a X»*, *«idéntico»*, …). No verifica —eso no se puede automatizar— pero **inventaría**, que
es lo que nunca se había hecho:

| | |
|---|---|
| afirmaciones de estado en el repo | **221** |
| en `pipeline/` y `.github/` (donde dirigen decisiones) | **123** |
| clase más frecuente | «afirma equivalencia» (56) |
| clase más peligrosa por historial | «afirma que algo no tiene efecto» (85) |

De ahí salen los hallazgos que siguen. Cada uno se verificó contra datos y **cada uno
terminó en un guard**, no en una corrección: corregir el texto lo deja envejecer de nuevo.

---

## Hallazgo 1 — `single_pixel_mode`: **FALSO** para los siete volcanes que nombra

**Lo declarado.** *«Volcanes NO afectados (régimen alto-MW o sin path D dominante):
Villarrica (es F52-A), Copahue, Isluga, Lascar, Lastarria, Llaima, NdC.»* Estaba en el
docstring **y copiada en 13 perfiles, incluido el operacional**.

**Lo efectivo** (`02_single_pixel_mode_alcance.py`, sobre `data/mirova_equivalent/`,
60.358 records). Se cuenta lo que el modo **realmente cambia**: los clústeres multi-píxel,
donde `max ≠ suma`. Para un clúster de un solo píxel el modo se activa pero no mueve nada,
así que contar activaciones exageraría el alcance.

| volcán | records modificados | % | lo declarado |
|---|---|---|---|
| **Láscar** | 1.279 | **33,9 %** | «NO afectado» |
| Puyehue-Cordón Caulle | 989 | 23,2 % | se construyó para él (0,48×) |
| Isluga | 553 | 15,9 % | «NO afectado» |
| Chaitén | 550 | 15,7 % | se construyó para él (2,53×) |
| Planchón-Peteroa | 418 | 12,5 % | se construyó para él (2,10×) |
| Lastarria | 388 | 11,9 % | «NO afectado» |
| Villarrica | 442 | 10,9 % | «NO afectado» |
| Copahue | 339 | 10,5 % | «NO afectado» |
| Nevados de Chillán | 309 | 9,6 % | «NO afectado» |
| Llaima | 309 | 9,3 % | «NO afectado» |
| **Tupungatito** | 275 | **7,5 %** | se construyó para él (**30,15×**) |

Falso para **los siete**. Y no marginalmente: **el volcán más afectado de la flota es
Láscar**, que figura como no afectado, y **el menos afectado es Tupungatito**, que es la
razón por la que el modo existe. El orden está invertido respecto de su propia justificación.

**Por qué importa más allá del texto.** S126 gastó trabajo en entender por qué a Láscar le
faltaba magnitud; el docstring decía que este mecanismo no lo tocaba. Lo toca más que a
ningún otro.

**Cómo se cerró.** No reescribiendo la lista —volvería a envejecer sola, que es exactamente
cómo nació el problema— sino **borrándola** y apuntando al script que la mide. El guard
`tests/test_guard_afirmaciones_de_alcance_s127.py` prohíbe **declararla** y permite
**citarla** como historia, distinguiendo por contexto. PR #548.

---

## Hallazgo 2 — el kernel de vecinos: «nunca corre en producción» es **FALSO**

**Lo declarado** (`_s124_kernelbg_ab.yaml`): *«el campo per-volcán
`local_kernel_bg_compatible` está en FALSE para LOS 11. O sea: la rama del kernel nunca
corre en producción.»*

**Lo efectivo**: corre en **5 de los 11 Tier A**.

| | volcanes |
|---|---|
| kernel **ON** | PCC, Villarrica, Chaitén, Planchón-Peteroa, Lastarria |
| kernel **OFF** explícito | Copahue, Llaima |
| sin el campo (→ default `False`) | Isluga, Láscar, NdC, Tupungatito |

**La causa, y es la parte que hay que recordar.** El parámetro de la función se llama
`local_kernel_bg_compatible`; la clave de `volcanoes.yaml` se llama `local_kernel_bg`.
`run_pipeline.py:244` hace el puente. Buscar el nombre del parámetro en el YAML **no da
error: da cero resultados**, que se lee como «no está en ninguno».

S124 ya había identificado esta clase de error —la anotó como A48— pero el texto falso
sobrevivió en la cabecera del perfil, donde una sesión futura lo lee como dato. **Y volvió
a inducir el mismo error en S127**, en mí, antes de trazar cómo lo lee el código (A6). Esa
reincidencia es la mejor evidencia de que el sub-patrón es estructural, y por eso quedó
escrito dentro de T9.

**Consecuencia práctica**: cualquier lectura del A/B de S124 que asuma «el control es
todo-anillo» está mal — 5 de sus volcanes ya venían con el kernel puesto.

---

## Hallazgo 3 — dos claves declaradas donde el código no las lee, en **31 de 51** perfiles

`modis_vent_threshold_k: 2.5` y `modis_vent_vrp_floor_mw: 0.3` estaban bajo `paths:`. El
código las lee de `thresholds:` (`profile.py:106-107`, `_t.get`), donde valen **1.0 y 0.0**.

No hacían daño porque `enable_vent_path_modis` está en `false` — o sea **la trampa esperaba
justo al que encendiera ese path**, que es el momento en que menos se la busca. Misma familia
que `enable_utm_regrid` en S124: se escribía en el nivel superior y se leía de `thresholds:`,
así que un perfil de laboratorio con el flag en `true` arrancaba apagado y su A/B habría
corrido cuatro brazos idénticos.

**El barrido fue genérico**, no dirigido: deriva de `profile.py` de qué sección se lee cada
una de las ~70 claves y busca cualquier declaración en otra. Resultado: **exactamente estas
dos, en 31 perfiles, y nada más**. La clase quedó enumerada, así que cerrarla la cierra.

**Probado como no-op**: se comparó el valor **resuelto** de cuatro atributos en **los 51
perfiles**, cargando cada uno en su propio proceso, antes y después. Cero cambios. PR #550.

---

## Hallazgo 4 — la corona Eq.6 se calculaba y se tiraba (**el que bloqueaba la sesión**)

El A/B de la corona salió inconcluso dos veces. La segunda, la corona **sí corrió** —1.179
records de 1.278— pero sólo cambió el número publicado en **15**:

```
los que NO cambiaron -> single_pixel_mode: {True: 1164}
los que SI cambiaron -> single_pixel_mode: {False: 15}
```

`apply_single_pixel_mode` corre después del recompute y recibía los VRP por píxel del fondo
**viejo**. Para un clúster sub-MW de ≤3 px reemplaza el total por `max(per_pixel)`, y ese
máximo venía del anillo regional.

El caso límite lo dice todo: **para un clúster de un píxel, la suma y el máximo son el mismo
número por definición**. Que el modo mueva el valor sólo puede significar dos fondos
distintos. El 98 % de los clústeres de Villarrica son de un píxel.

**La variante latente de MODIS era peor.** Ahí `cluster_focal_vrp_mw` está **encendido** y
reasigna el VRP sin condición desde el array regional, justo después de la corona. Con los
dos flags encendidos la corona no se anulaba en el 98 % de los casos: se anulaba en el
**100 %**, siempre, y sin dejar marca (`corona_degraded: false` se lee como «corrió bien»).
No se notaba porque su flag está OFF — era el desenlace de #539 y #543 esperando a repetirse.

**Un no-op probado.** Los flags están OFF, así que el fix no debía mover producción. El test
que lo **exige** encontró una diferencia real: desde Python 3.12 `sum()` usa suma compensada
de Neumaier y no da bit a bit lo que daba el acumulador histórico (1 ULP). Se agregó
`sum_cluster_vrp` con acumulación naive **a propósito**. PR #546.

---

## Hallazgo 5 — el schema está íntegramente consumido (**CONFIRMADO**, buena noticia)

`03_escrito_vs_leido.py` cruza los **84 campos** que aparecen en los 60.358 records de
producción contra las tres vistas del frontend, `audit_metrics`, `store` y `scripts/`:
**ningún campo escrito carece de lector**. No hay schema muerto.

Es la dirección barata del cruce. La cara peligrosa —campos que un consumidor lee y ningún
record escribe, que en Python y en JS no dan error sino `None`/`undefined`— no se pudo
cerrar con esta heurística: se ahoga en nombres de JavaScript (`filter`, `length`, `style`).
Queda como trabajo con una heurística mejor.

**Hallazgo colateral**: `frontend/` tiene **cuatro** vistas desplegadas, no tres.
`comparacion.html` se identifica a sí misma como *«PREVIEW S115 · no es el dashboard live»*,
está enlazada desde `index.html` y **no lleva el helper `mirovaEqVrp`** que las otras tres
replican (index 25 usos, diario 8, mosaico 8; comparación 0). No es una inconsistencia
oculta —está rotulada— pero CLAUDE.md dice «3 vistas standalone» y la regla S92 L5 manda
replicar los cambios de display «en las 3». Corregir el conteo en CLAUDE.md.

---

## Infra: el job `merge` que se cancelaba en silencio

Pasó en S125 y volvió a pasar en S126: cuando dos A/B terminan juntos, un job `merge` se
cancela y su reproceso —horas de CI— queda sólo en artefactos.

**Causa**: `reproc-chunked.yml` declaraba `group: push-main` a nivel **job**. GitHub mantiene
un solo run pendiente por grupo, y `nrt.yml` ocupa ese lock ~50 min de cada 2 h, así que el
primer merge se encola detrás y el segundo lo desplaza. Es el mismo mecanismo que CLAUDE.md
ya documenta para la matrix de `nrt.yml` («a nivel job se perderían 9 volcanes»).

**Fix**: grupo propio por perfil. Es seguro porque el paso `Commit` ya reintenta
`pull --rebase` + `push` cinco veces con backoff —esa es la defensa real contra la carrera
de refs del PR #502— y el grupo compartido sólo agregaba el riesgo de perder runs encolados.
Mismo criterio ya aplicado en los dos workflows de S124. PR #546.

> ⚠️ **Para revisar**: CLAUDE.md dice que todo yml que pushee a main **debe** declarar
> `push-main`. Con este cambio son **tres** los workflows que deliberadamente no lo hacen,
> cada uno con su razón escrita. La regla, como está redactada, ya no describe el repo.

---

## Guards nuevos

| guard | qué impide |
|---|---|
| `test_corona_single_pixel_coherencia_s127.py` | que un recompute de fondo se pierda aguas abajo; incluye el invariante del clúster de un píxel y la prueba de no-op bit a bit |
| `test_guard_afirmaciones_de_alcance_s127.py` | que vuelva a escribirse una lista de volcanes afectados; distingue declarar de citar |
| `test_guard_claves_fantasma_s127.py` | que una clave se declare en una sección donde el código no la lee — genérico, y con un test que verifica que **el guard sigue mirando** |

Ese último detalle es deliberado: un guard que pasa porque dejó de encontrar nada da
confianza falsa, que es peor que no tenerlo.

## Divergencias que cambian de estado

- **D14** (máscara de nube BT<260 K) → **CERRADA**. Se sostiene el apagado, ratificado con
  el A/B en la mano (decisión de Nicolás, S127). Recupera 176 de 181 noches ciegas, es lo
  clon-literal (`MISSION.md` la declara removida desde S27, el perfil desde S29) y su costo
  medido es de medio grado a dos de fondo. **No cierra el frente del artefacto**: de las 286
  detecciones que destapó, sólo 21 caen en noches que MIROVA confirma, con distancia mediana
  2,4-2,7 km — la firma del anillo autorreferente. Eso se cierra por el fondo, no por la
  máscara. PR #549.

## Lo que falta

**Fase 2**, sin empezar: eje geométrico (D17, el único drift sin barrer — y A82 fue rebajada
en S125 justamente porque S114 nunca lo miró), matriz sensor × tratamiento, higiene de
`experiments/` (37 directorios sin trackear al abrir S126).

**El frente científico** no es trabajo de auditoría y sigue abierto: el veredicto del 2×2
corona × filtro contextual (los dos brazos relanzados en S127 sobre el código arreglado) y
el segundo píxel de Láscar.

## La regla que deja

> Una afirmación sobre el estado del sistema necesita un test detrás, o no es una afirmación
> — es una intención.
