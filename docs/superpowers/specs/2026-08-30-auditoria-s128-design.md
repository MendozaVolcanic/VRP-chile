# Auditoría S128 — evidencia exógena, y el arreglo del propio protocolo

> Diseño. Las decisiones de alcance las tomó Nicolás en S127: **eje exógeno sin NHI**,
> **la deuda primero**, **D14 reabierta**.

## El diagnóstico que ordena todo: el rendimiento es del eje, no de la profundidad

Medido sobre las once auditorías del proyecto (fracción de hallazgos provenientes de un eje
de comparación **nunca usado antes**):

| auditoría | eje nuevo | hallazgos que movieron el pipeline |
|---|---|---|
| S105 | **0 %** | ninguno |
| S122 | ~8 % | ninguno |
| S116 | ~17 % | ninguno |
| S123 | ~20 % | ninguno |
| S125 | ~35 % | factor 2 en magnitud |
| S119 | ~50 % | mapa de gaps |
| S114 | ~58 % | cierre de D11 |
| S121 | ~63 % | poda, backlog |
| S124 | ~70 % | grilla UTM |
| **S127** | **~75 %** | corona anulada, 3 guards |

Las tres que repitieron el barrido general de 6-8 ejes produjeron **sólo deuda documental**.
La correlación no deja lugar a dudas: **repetir el barrido general es tiempo perdido**.

Y hay dos fugas que explican por qué siempre queda inventario:

**Fuga 1 — cerrar con prosa en vez de guard.** Nueve hallazgos se redescubrieron en más de
una auditoría. El cap de 50.000 MW en `diario.html` apareció en **cuatro**. Un hallazgo
*explícitamente refutado* en S121 volvió como hallazgo nuevo en S125 — la refutación
tampoco dejó guard. S127 fue la única que cerró con tests (3 guards) y es la única sin
reincidencias.

**Fuga 2 — declarar sin verificar.** S121 cerró con **19 hallazgos sin verificación
individual**; S125 con **9 «sin respaldo»**. Ese inventario es exactamente la materia prima
que la auditoría siguiente reporta como «nueva».

## Las tres correcciones al protocolo (vinculantes desde S128)

1. **Cierre por guard, obligatorio.** Ningún hallazgo pasa a CONFIRMADO / FALSO / OBSOLETO
   sin un test que lo mida, o una razón escrita de por qué no se puede medir. La regla
   actual («corregir el doc citando la evidencia») produjo los nueve redescubrimientos.

2. **Registro de ejes con cuota de novedad.** El protocolo lista nueve *técnicas* (T1-T9)
   y ningún *eje de comparación*. Se agrega la tabla de ejes con fecha de último uso, y
   cada auditoría debe estrenar **al menos uno nunca usado**. Queda **prohibido** repetir
   el barrido general de 6-8 ejes: rindió 0 % en S105 y ~8 % en S122.

3. **Los pendientes no cuentan, y son la puerta de entrada.** Cada auditoría cierra
   publicando tres números —confirmados / refutados / pendientes— y la siguiente **empieza**
   por la lista de pendientes antes de abrir eje nuevo.

## El eje que ninguna auditoría usó: evidencia exógena

Las once auditorías midieron contra MIROVA (su CSV) o contra los papers de MIROVA leídos a
través de nuestras propias síntesis. **Toda la evidencia de calidad del sistema descansa en
una sola fuente que sabemos incompleta.**

Existen tres ventanas al exterior. Nicolás excluyó la tercera para esta sesión:

| ventana | qué es | historial |
|---|---|---|
| **A. El archivo de TIF/KMZ** | el campo de radiancia que MIROVA publica por pasada | usada 2 veces (S126), **dio vuelta una creencia las 2** |
| **B. Los papers, verbatim** | los PDF, no nuestras síntesis | usada 1 vez (A35), encontró una cita mal leída |
| ~~C. Otro sensor (NHI-v1)~~ | ~~SWIR 20 m independiente~~ | **excluida por Nicolás para S128** |

### Lo que el archivo de TIF permite y lo que no

**Permite** (verificado): 1.966 TIF, 11 volcanes × 3 sensores, todos poblados. Una banda
`float64`, EPSG:4326, radiancia espectral MIR. Tamaño fijo por sensor: MODIS 51×51 (~1 km),
VIIRS750 67×67, VIIRS375 134×134. **Un solo geotransform por volcán×sensor** en todo el
archivo.

**No permite**, y hay que decirlo antes de diseñar nada encima: **sólo 11,6 días**
(2026-05-08 a 05-20). No hay VRP numérico, ni banda TIR (así que no se puede reconstruir el
NTI), ni la máscara de píxeles que MIROVA alertó, ni ángulos de vista. Es una ventana sin
actividad fuerte: máximo global 1,909 (≈339 K), cero píxeles saturados.

Con esa restricción, las preguntas que **sí** contesta son geométricas y de cobertura — que
resulta ser justo donde está la deuda (D17).

## Las cinco sondas de la Fase 2, en orden de rendimiento esperado

**P1 · La grilla real de MIROVA.** Los tres sensores comparten el **borde oeste idéntico**
pero no el norte: MIROVA **fija una esquina, no el centro**. Si nuestro regrid asume
centrado simétrico, está mal por construcción. Y el `LatLonBox` del KMZ —de donde salió
nuestro `mirova_center` en S80— **no coincide con los bounds del TIF** (~1,6 km en
Villarrica VIIRS375). Esto ataca D17 desde la única evidencia externa que existe, y D17
está abierta con «premisa probada, consecuencia NO».

**P2 · Contraste al cráter donde no debería haberlo.** En la ventana del archivo,
**Copahue, Lastarria y Tupungatito no tienen ninguna escena con contraste al cráter** sobre
~175 cada uno. Cualquier detección nuestra ahí, en esos 11,6 días, es candidata a falso
positivo **con evidencia externa**, no con nuestro propio juicio. Es la primera vez que se
podría decir eso.

**P3 · Cuánto pierde `latest.php`.** El README del archivo afirma que la fuente de nuestra
ground truth pierde **~80 % de las pasadas**. **D2 —«el CSV cubre ~70 % de VIIRS»— nunca se
midió** y es la creencia más load-bearing del catálogo: toda métrica de recall se corrige
mentalmente con ese número. El archivo tiene 1.966 pasadas con timestamp; cruzarlas contra
el CSV lo convierte en un número duro.

**P4 · Radiancia contra radiancia.** Muestrear nuestra radiancia MIR en el centroide de
MIROVA para cada par que empate en tiempo, y reportar sesgo, RMSE y R². Detecta errores de
banda, de calibración o de unidades que ninguna auditoría interna puede ver.

**P5 · Verificación verbatim de las citas que gobiernan decisiones.** Empezando por las dos
de D14: la de Laiolo 2026 (que resultó ser una retraducción de una nota `ai_generated`) y
**el corte de 0,1 MW** que la misma nota atribuye a MIROVA. Si el corte es real, reencuadra
el piso VRP y la mitad del frente de «sobre-detección». Se extiende a toda cita en itálicas
de `MISSION.md` y `MIROVA_DIVERGENCES.md`: ¿existe el PDF? ¿dice eso?

## Fase 1 — la deuda, que es la puerta de entrada

Antes de tocar el eje nuevo: los **28 hallazgos sin verificar** (19 de S121, 9 de S125).
Para cada uno, uno de tres destinos: **confirmado con script**, **refutado con script**, o
**imposible de verificar y por qué**. Sin destino intermedio.

Se suman las contradicciones internas ya localizadas, que son deuda de la misma clase:

- la tabla roadmap de `MIROVA_DIVERGENCES.md:562` **congelada en S35** (lista D8 como
  «NUEVO pendiente» cuando está resuelta, y D5 como cerrada cuando S125 la rebajó);
- **A82 rebajada en S124, pero A83 y A84 heredan la versión fuerte** sin caveat, en el mismo
  archivo que sí quedó parchado más abajo;
- **colisión de identificadores**: «D2» nombra dos cosas distintas y «D8» también. Un `grep`
  de «D2 resuelto» arrastra un cierre falso — el modo de falla de A89.

## Lo que esta auditoría NO hace

- **No repite el barrido general** de 6-8 ejes (0 % de rendimiento en S105, ~8 % en S122).
- **No usa NHI-v1** (excluido por Nicolás para esta sesión).
- **No reabre** lo cerrado con guard en S127.
- **No actúa sobre el corte de 0,1 MW** hasta tener el PDF: la fuente es la misma nota no
  verificada que originó el problema. Verificarla es la tarea; usarla, no.
- **No toca `pipeline/`** sin ciclo A45 completo. Todas las sondas son read-only.

## Criterio de salida

Tres números publicados —confirmados / refutados / pendientes— y **cada hallazgo con un
guard o con la razón escrita de por qué no lo lleva**. Si al cerrar quedan pendientes sin
destino, son la puerta de entrada de S129, no material para reportar como nuevo.
