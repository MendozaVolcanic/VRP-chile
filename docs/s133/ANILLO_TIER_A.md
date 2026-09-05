# S133 · El anillo de Villarrica está en 9 de los 11 Tier A

**Lo que el mapa de Villarrica mostró no es de Villarrica.** Medido en los 11 volcanes con
serie continua: la distancia mediana del cúmulo que publicamos al cráter es de **2,3 a 2,8 km
en VIIRS 375 m** en nueve de ellos. Sólo dos se pegan al cráter, y son los dos con el foco
más fuerte y más aislado. La pregunta de Nicolás —«¿esto podría estar pasando en todos los
volcanes?»— tiene respuesta medida: sí.

Números en `experiments/_s133_villarrica_focus/anillo_tier_a.json`, script
`anillo_tier_a.py`. Records publicados (magnitud > 0, clase *summit*) desde 2026-06-01.
Ancla: `vent_lat/lon` de `volcanoes.yaml` en los 11.

## La medición

Distancia mediana del centroide del cúmulo al cráter, y fracción a menos de 500 m:

| volcán | VIIRS 375 m | VIIRS 750 m | MODIS |
|---|---|---|---|
| **Láscar** | **0,22 km · 79 %** (n=208) | 0,30 · 66 % (97) | 0,97 · 0 % (4) |
| Isluga | 0,96 · 0 % (313) | 1,52 · 3 % (106) | 1,72 · 0 % (2) |
| Puyehue-C. Caulle | 1,08 · 44 % (313) | 4,56 · 20 % (237) | 2,23 · 5 % (158) |
| Tupungatito | 2,27 · 37 % (223) | 1,34 · 5 % (107) | 1,29 · 7 % (14) |
| Lastarria | 2,28 · 0 % (144) | 1,76 · 3 % (63) | 1,33 · 0 % (11) |
| Planchón-Peteroa | 2,45 · 21 % (251) | 1,32 · 11 % (70) | 0,94 · 19 % (16) |
| Chaitén | 2,49 · 21 % (323) | 1,20 · 14 % (95) | 1,43 · 9 % (23) |
| Nevados de Chillán | 2,61 · 10 % (189) | 1,31 · 4 % (45) | 1,01 · 14 % (14) |
| Villarrica | 2,79 · 5 % (289) | 1,34 · 7 % (94) | 1,69 · 5 % (19) |
| Copahue | 2,80 · 0 % (305) | 1,51 · 4 % (85) | 0,83 · 25 % (8) |
| Llaima | 2,84 · 0 % (277) | 1,30 · 0 % (75) | 1,24 · 11 % (9) |

## Cómo leerlo, y qué no leer

**Láscar es el control positivo.** Es el volcán más caliente (ΔT ~17 K) y su cráter es un
foco aislado sobre roca seca: ahí el cúmulo cae en el cráter en el 79 % de las pasadas. O sea,
el instrumento **puede** poner el cúmulo donde está el calor cuando el calor es fuerte y focal.
Que no lo haga en los otros nueve no es un defecto de la medición: es el fenómeno.

**Lastarria es la excepción que no es defecto**: su offset es el campo fumarólico Lazufre,
real y conocido en terreno (A84). Los otros ocho son nevados con señal débil: el régimen donde
A69 predice que el MIR absoluto sigue la frontera nieve-roca y no el cráter.

**El estrato MODIS casi no existe** (n de 2 a 23, salvo PCC): no porque MODIS no detecte, sino
porque casi todo MODIS queda clasificado *far* por el `final_hotspot` de MIR absoluto (A46,
A82) y este corte pide *summit*. Es la misma cara del problema vista desde la etiqueta.

**Lo que esta tabla NO dice**: no dice que MIROVA ponga su cúmulo en el cráter. MIROVA
reporta una celda de su grilla (D15) y su `Distancia_km` viene cuantizada; en Villarrica dio
1,41 km para la pasada de las 07:50 mientras nosotros dimos 0,85 desde el catálogo. Comparar
posiciones exige la misma ancla y la misma pasada: eso es trabajo de la auditoría S134, no de
esta tabla.

## Por qué importa para la paridad

Si el cúmulo que integramos está en el flanco a 2,5 km y MIROVA integra la celda del cráter,
las dos magnitudes son de **dos objetos distintos**, y la razón entre ellas mide eso antes que
cualquier coeficiente. Es una explicación candidata —no probada— de por qué el déficit en
régimen débil (Lastarria 0,415, Láscar 0,465, Isluga 0,603 en el auto-audit) no se cierra con
correcciones de área ni de banda: las correcciones escalan una magnitud que ya viene del
lugar equivocado. Láscar contradice esa lectura simple (cúmulo en el cráter y aun así
sub-estima), así que la hipótesis tiene un contraejemplo que hay que explicar, no ignorar.


---

> **⚠️ Lectura corregida en S134 (`docs/AUDIT_S134.md`).** Los números de esta tabla se
> reproducen exactos (F1, F2 y F3 lo verificaron), pero la interpretación no: (1) el anillo
> **no explica el déficit de paridad** — en las pasadas que MIROVA confirma nuestro cúmulo ya
> está en el cráter (Villarrica 0,15 km, PCC 0,22, Tupungatito 0,23) y la razón ours/MIROVA es
> plana en distancia (F1, criterio pre-registrado NO CUMPLE); (2) el anillo vive en los records
> débiles que MIROVA no publica (85 % con < 0,1 MW) y **está en los 11, Láscar incluido**
> (2,63 km en sus `test1_roi`): «Láscar 0,22 vs Villarrica 2,79» es la mezcla de fuentes
> `ctx_cluster`/`test1_roi`, no un volcán que el mecanismo respete; (3) el mecanismo es
> `keep_peak` (D19). Esta tabla midió `pc.centroid`, que para los records `ctx_cluster` con
> `_test1_wins` no es lo que el dashboard dibuja (F3 H3).
