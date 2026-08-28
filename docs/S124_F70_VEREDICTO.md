# F70 — veredicto de los 4 brazos

> Ventana 2026-06-25..2026-08-24, 11 Tier A, VIIRS 375 m. Lectura APAREADA por
> pasada. Criterios **escritos antes de correr** en `pipeline/profiles/_f70_b.yaml`
> §CRITERIO PRE-REGISTRADO (A66) — releídos antes de mirar resultados.
> Scripts: `experiments/_s124_f70/03_leer_brazo.py` · `04_tabla_brazos.py`.

## Los cuatro brazos

| | grilla UTM | kernel-bg | qué aislaba |
|---|---|---|---|
| control | OFF | per-volcán | la serie operacional |
| **A** | **ON** | per-volcán | la grilla sola |
| **B** | **ON** | **global** | la hipótesis central |
| C | OFF | global | el kernel solo (corrido S124) |

## Ratio mediano vs MIROVA (banda de la MEDIANA 0,7–1,4)

| volcán | n | control | A | B | C |
|---|---|---|---|---|---|
| Láscar | 32 | 0,47 | 0,46 | **0,58** | 0,58 |
| Isluga | 40 | 0,70 ✓ | 0,69 | **0,81** ✓ | 0,81 ✓ |
| Lastarria | 27 | 0,36 | 0,34 | 0,34 | — |
| Copahue | 1 | 1,02 ✓ | 1,07 ✓ | 1,07 ✓ | 1,02 ✓ |
| **Tupungatito** | 17 | 0,81 ✓ | 0,82 ✓ | **0,81** ✓ | 0,81 ✓ |
| NevadosDeChillán | 2 | 1,31 ✓ | 1,31 ✓ | 1,31 ✓ | 1,31 ✓ |
| Villarrica | 9 | 0,72 ✓ | 0,72 ✓ | 0,72 ✓ | — |
| Chaitén | 11 | 1,29 ✓ | 1,26 ✓ | 1,26 ✓ | — |
| Planchón-Peteroa | 11 | 0,96 ✓ | 0,96 ✓ | 0,96 ✓ | — |

## Verificación previa: ¿la grilla se aplicó de verdad?

Sí, y la prueba es geométrica. Las coordenadas de los píxeles anómalos:

| perfil | separaciones más comunes entre latitudes |
|---|---|
| control | 6 · 12 · 16 · 37 m → **swath crudo** |
| A y B | **375 · 374 · 750 m** → **grilla cuantizada** |

## Criterio por criterio

| criterio | resultado |
|---|---|
| **JUEZ — Tupungatito**: B debe curarlo donde C no | ❌ **0,81 → 0,81**. Sin cambio. Ya estaba en banda y sigue igual; B no lo mueve |
| **PRIMARIO** — los sub-reportadores entran en banda | ❌ Láscar 0,47→**0,58** (fuera) · Lastarria 0,36→**0,34** (fuera) · Isluga 0,70→0,81 (ya estaba dentro) |
| **GUARDA 1** — Lastarria no se rompe | ⚠️ 0,36 → 0,34. No se rompe *más*, pero el criterio suponía que estaba en banda y **no lo estaba** (premisa equivocada al escribirlo) |
| **GUARDA 2** — los sobre-reportadores no pasan 1,4 | ✅ Chaitén 1,26 · NdC 1,31 · Copahue 1,07 |
| **GUARDA 3** — el cluster no migra | ✅ desplazamiento mediano −0,08 a +0,04 km, muy por debajo del umbral |
| **GUARDA 4** — recall sin caídas >2 pp | ✅ VIIRS375 **96 % → 96 %**; MODIS 0 % → 33 % (n=6, mejora) |
| **A79** — los eventos ancla sobreviven | ✅ **0 perdidos** sobre las 19 alertas más fuertes de la ventana |

## ⚠️ ADENDA (28-ago) — el poder estadístico, a pedido de Nicolás

Preguntó si estos reprocesos bastaban para sostener el veredicto. **No para todo
lo que afirmé.** Bootstrap (5000 remuestreos) + test de signos pareado:

**Lo que NO se sostiene y queda corregido:**

1. **«B ≡ C exacto» era falso.** Solo 3 volcanes tienen n≥3 en ambos brazos, y
   las diferencias no son cero: |B−C| = 0,00068 (Láscar) · 0,00042 (Isluga) ·
   0,000000 (Tupungatito) · 0,05 (Copahue, n=1). Son **indistinguibles**, no
   idénticos. La «identidad exacta» era un artefacto de redondear a 2 decimales.
2. **«La grilla no hace nada» era falso — el resultado es MIXTO.** El test
   pareado da diferencia mediana +0,000 con p=1,00, pero eso *promedia efectos
   opuestos*: Láscar **+0,11** e Isluga **+0,11** mejoran, PCC **−0,10** empeora.
3. **Los veredictos por volcán no son concluyentes.** Los IC 95 % de control y B
   **se solapan en los 10** volcanes, y en **6 de 10** el IC cruza el borde de la
   banda. El juez Tupungatito: 0,81 **[0,65–0,92]** — el intervalo cruza el 0,7,
   así que ni siquiera podemos afirmar con confianza que esté «dentro».

**Lo que SÍ se sostiene** (son conteos y geometría, no medianas):

- El regrid corrió: coordenadas cuantizadas a 375 m vs dispersas en el control.
- Sin daño colateral: recall 96 %→96 %, sin migración de cluster, 0/19 eventos
  ancla perdidos.
- Los sub-reportadores siguen fuera de banda (aunque con IC anchos).

**Hallazgo NUEVO que sale de la revisión — apoya D17:** el efecto de la grilla
correlaciona con su desalineación. Ordenado por offset:

| volcán | offset | B − control |
|---|---|---|
| PuyehueCordonCaulle | 7618 m | **−0,104** |
| Tupungatito | 4796 m | 0,000 |
| Planchón-Peteroa | 2013 m | 0,000 |
| Láscar | 841 m | **+0,110** |
| Chaitén | 607 m | −0,033 |
| Isluga | 61 m | **+0,110** |
| Lastarria | 45 m | −0,020 |

**r = −0,47** (n=8): la grilla **daña donde está mal alineada y ayuda donde está
alineada**, que es exactamente lo que D17 predice. Pero con n=8 eso no es
significativo (p ≈ 0,24) — **sugestivo, no probado**.

## Veredicto revisado

**«NO ADOPTAR» se mantiene** — ningún criterio pre-registrado se cumple, y no
hay caso para promover. Pero la razón cambia: no es que la grilla *no haga
nada*, es que **ayuda o daña según esté alineada**, y con la ventana actual no
podemos separar las dos cosas con confianza.

---

## Veredicto: **NO ADOPTAR** — la hipótesis central queda refutada

El diseño lo dejó escrito de antemano: *"Si B también lo deja roto, la hipótesis
se refuta y se documenta en MIROVA_DIVERGENCES"*. Eso es lo que pasó.

**Lo que aprendimos, que es más que un no:**

1. **La grilla sola no hace nada.** El brazo A es indistinguible del control
   (0,46 vs 0,47 · 0,69 vs 0,70 · 0,34 vs 0,36). Cambiar el sustrato geométrico
   no mueve la magnitud.
2. **B ≡ C.** El brazo B da exactamente lo mismo que el kernel solo (Láscar
   0,58 en ambos; Isluga 0,81 en ambos). O sea: **todo el efecto viene del
   kernel de vecinos, y la grilla no aporta nada encima**. La hipótesis era que
   la grilla haría funcionar al kernel; la grilla resultó irrelevante.
3. **Y el kernel tampoco alcanza.** Láscar se mueve de 0,47 a 0,58 —dirección
   correcta— pero no entra en banda, y Lastarria empeora un poco.

**Sin daño colateral**: recall estable, sin migración de cluster, sin eventos
ancla perdidos. El cambio es inocuo, pero no cura.

## Qué queda en pie — el sub-reporte sigue sin explicación

Los cuatro que sub-reportan (Láscar 0,47 · Lastarria 0,36 · Isluga 0,70 ·
Llaima) siguen fuera de banda, y ya descartamos con datos:

- ❌ que MIROVA integre un halo (su Npix mediano es 1)
- ❌ que sea atribución de cluster (sumar la escena entera no cierra la brecha)
- ❌ que sea el second-run mal implementado (es fiel al paper)
- ❌ que sea el piso VRP (toca otro campo del que lee el dashboard)
- ❌ que sea el fondo del anillo lejano *solo* (brazo C: insuficiente)
- ❌ que sea el sustrato geométrico (brazos A y B: nulo)

**El candidato vivo, y sale de esta misma noche**: las grillas de MIROVA están
**desalineadas de nuestra ancla** — PCC 7,6 km · Tupungatito 4,8 km ·
Planchón-Peteroa 2,0 km · Láscar 841 m · Villarrica 705 m · Chaitén 607 m (de
sus propios GeoTIFF, tarea 3d). Nosotros centramos la grilla en *nuestro* ancla;
ellos en otro punto. Mismo tamaño de celda, **distinta partición del terreno**:
los ocho vecinos promedian vecindarios distintos, y el fondo del VRP sale
distinto.

Eso explicaría por qué la grilla "no sirvió": **la implementamos alineada al
lugar equivocado**. Es una hipótesis nueva, no una excusa — y es testeable
reusando toda la infraestructura de F70.2, cambiando solo el centro de la
grilla al que publican sus GeoTIFF.

## Recomendación

1. **No promover nada.** El flag `enable_utm_regrid` queda en `False`.
2. **Documentar el resultado negativo** en `MIROVA_DIVERGENCES.md` — un brazo
   que refuta su propia hipótesis con criterios pre-registrados es un resultado
   válido, no un fracaso.
3. **Brazo D (nuevo)**: grilla ON + kernel global + **centro de grilla tomado de
   los GeoTIFF de MIROVA**, en los 6 volcanes con offset >500 m. Es la única
   hipótesis viva y ya está la infraestructura. Requiere confirmación de Nicolás.
