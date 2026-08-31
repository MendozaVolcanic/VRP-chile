# S129 · Auditoría de visualización — índice y estado

Seis dominios independientes sobre las cuatro vistas del dashboard. Contexto común en
`_CONTEXTO_DISPLAY.md`.

| # | dominio | informe | estado |
|---|---|---|---|
| V1 | coherencia entre vistas | `DISPLAY_V1_COHERENCIA.md` | ✅ |
| V2 | trazabilidad de cada número | `DISPLAY_V2_TRAZABILIDAD.md` | ✅ |
| V3 | toggles y sus promesas | `DISPLAY_V3_TOGGLES.md` | ✅ |
| V4 | filtros que ocultan dato | `DISPLAY_V4_FILTROS.md` | ✅ |
| V5 | carga y rendimiento | `DISPLAY_V5_CARGA.md` | ✅ |
| V6 | transparencia CPLT 372 | `DISPLAY_V6_TRANSPARENCIA.md` | ✅ |

Anteriores del mismo frente: `AUDITORIA_TARJETAS.md` (las tarjetas de `index`) y
`AUDITORIA_MAPAS.md` (el eje espacial de los 11 mapas).

---

## Los tres hallazgos que un operador puede sufrir hoy

Ordenados por lo que le pasa a quien mira la pantalla, no por elegancia técnica.

### 0 · El mismo volcán, dos niveles de alerta distintos — V1

`index` muestra la **última** detección de 48 h (`:1387`, cambiado en S90 a pedido de
Nicolás) y `mosaico` el **máximo** (`:370`). Medido con un barrido rodante de 2.640
ventanas de 48 h: **73 % con número distinto y 19 % con NIVEL DE ALERTA distinto**. PCC
discrepa de nivel el **50 %** del tiempo, Villarrica 34 %, Chaitén 29 %.

Y lo que lo vuelve operacional: la tarjeta de `mosaico` **es un enlace a `index`**
(`:605`). El operador hace clic en «Bajo» y aterriza en «Muy Bajo». En el instante de la
auditoría, PCC se leía *0,43 MW · Muy Bajo* en una vista y *4,58 MW · Bajo* en la otra.

Causa raíz: **S90 cambió `index` y `mosaico` nunca se actualizó** — su comentario
`:369` todavía afirma estar sincronizado con la función que `index` dejó de usar.

### 1 · La barra «Estado actual» se congela — V3

`buildAlertSummary()` (`index.html:3043`) cuenta cuántos volcanes hay en cada nivel de
alerta. Está **arriba de los controles** y es lo primero que se lee.

Depende de los dos toggles principales, y **ninguno de los dos handlers la llama**.
Verificado: aparece en cuatro líneas y sus únicos llamadores son la leyenda de sensores
(`:3026`), el arranque (`:3642`) y el poll de cinco minutos (`:3677`) — que además sólo
re-renderiza si llegó dato nuevo.

**Qué le pasa al operador**: cambia de método de magnitud, la de un volcán de halo
glaciar sube ~10×, cruza el umbral de nivel, **las tarjetas cambian de color y el
contador de arriba no**. Puede quedar mal durante horas.

### 2 · La misma magnitud, dos veces en la misma pantalla, hasta 220× de diferencia — V2

| | |
|---|---|
| caja de estadística «VRE» | `index.html:1964` → `eqVrp(r)` — clúster summit |
| curva «VRE acumulada» | `index.html:2786` → `r.vrp_mw` — suma cruda de escena |

Difieren de **8× (Láscar) a 220× (Nevados de Chillán)**. Y el comentario de la caja
(`:1959-1962`) **documenta la razón para no usar ese campo**: *«S32 P2: usa mirovaEqVrp
… Con `vrp_mw` global la VRE quedaba inflada por anomalías térmicas no-volcánicas»*.
S32 arregló la caja y dejó la curva.

Misma familia: el popup «VRP final» del overview (21,4 % muestra más del doble; en PCC
el 55,9 %) y el tooltip del scatter de distancia.

### 3 · «Actualizado HH:MM UTC» es el reloj del navegador — V2

En `mosaico`, esa etiqueta no muestra `d.updated` sino la hora de carga de la página.
**Un JSON congelado se lee fresco.** Es la señal que uno mira para saber si el sistema
sigue vivo, y no sabe nada del dato.

Y en la misma vista, «Últ. detección» muestra el timestamp del **máximo**, no de la
última pasada: el **87,8 %** de 24.187 ventanas de 48 h.

---

## El texto obsoleto que ya apareció tres veces

*«Las detecciones lejanas siguen visibles en el mapa»* es **falso desde S26 B**
(`index.html:2539` las filtra). Aparece en:

1. el comentario de `index.html:809-811`,
2. el **tooltip visible** del grupo Distancia (`:557`) — o sea, en pantalla,
3. citado en informes previos como si fuera el comportamiento actual.

Un guard que prohíba esa frase mientras el filtro exista es el cierre correcto (regla B).

---

## Negativos limpios — lo que está bien y no hay que tocar

Valen tanto como los hallazgos, porque evitan trabajo inventado:

- **La persistencia está sana.** Todas las claves de las cuatro vistas parean; ninguna
  descalza. El estado inicial se sincroniza bien en las tres.
- **La carga ya se arregló en S120.** Las tres vistas live usan el JSON liviano (37,2 MB
  los once contra 267,2 completos, −86 %) con fallback. La creencia de que seguía rota
  sobrevivió al arreglo y yo mismo la propagué.
- **La tabla del detalle coincide con la tarjeta** desde el fix de S106.
- **`_mirova_confirmed` sí se muestra** — anillo verde y popup. Yo dije lo contrario.
- **`diario` es inmune a las promesas rotas** porque recarga la página en cada toggle.

---

## Nota de método: dos premisas falsas mías

En los briefs de esta tanda pasé **dos afirmaciones falsas** que heredé de informes
previos sin trazarlas: que `mosaico` bajaba 267 MB por carga, y que `_mirova_confirmed`
nunca se mostraba. Las dos las corrigieron los agentes.

Es el mismo modo de olvido que esta sesión viene persiguiendo, ahora del lado del que
escribe el encargo: **una afirmación de un informe anterior se cita como hecho sin
volver a medirla.** Lo anoto acá porque el próximo que arme briefs a partir de estos
informes corre el mismo riesgo.
