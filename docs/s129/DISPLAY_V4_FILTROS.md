# S129 · V4 — Los filtros que ocultan dato

**Medición**: `experiments/_s129_display/medir_filtros.py` → `resultados.json`. Replica cada
condición del frontend con sus defaults (`includeFarDistance=false`, `USE_F5_CORE=true`,
`onlyPrimaryPixel=true`, sensores todos encendidos) sobre los 57.696 records de los 11 Tier A
en `data/mirova_equivalent/*.json`. Ningún número transcrito a mano (S91).

## El titular

**De los 57.696 records, 23.697 (41,1 %) llegan al gráfico.** Y el reparto no es parejo:
VIIRS 375 m pasa el 73,5 %, VIIRS 750 m el 23,7 % y **MODIS el 11,0 %**.

El filtro que más suprime señal es **el default «Solo cráter»** (`index.html:985`), y
**no está ocultando un artefacto**: de los 10.155 records MODIS que apaga, **8.992 (88,6 %)
tienen su `primary_cluster` dentro del inner_radius**, con `geo_class: "summit"` y mediana
de 1,4–2,8 km del centro según el volcán. Son 13.978 MW de magnitud crateriana que el
dashboard pone en cero **por la etiqueta de otro campo**.

## Cuánto oculta cada filtro

| # | filtro | `archivo:línea` | records a 0 | MW ocultos | en noches con alerta MIROVA |
|---|---|---|---|---|---|
| F2 | `distance_class !== "summit"` (default «Solo cráter») | `index.html:985` | **10.640** (MODIS 10.155 · V750 395 · V375 90) | 17.070 | 108 |
| F2b | └ de esos, con el **cluster dentro del inner** | — | **8.996** (MODIS 8.992) | 13.978 | 84 |
| F1 | `isValidDetection` — `vrp_mw=0` y sin `triggered_test1` | `index.html:1371-1375` | 21.186 (36,7 %) | 1.003 | 723 |
| F1b | └ los que **diario y mosaico sí dibujan** | — | 562 (547 por piso VRP) | 114 | 28 |
| F3 | `pc.centroid_dist_km > innerKm` | `index.html:989` | **0** | 0 | 0 |
| F4 | cap de sanidad 50.000 MW | `index.html:981, 992, 1090` | **0** | 0 | 0 |
| F5 | `isThermalArtifact` (cirrus S90 + campo difuso S93) | `index.html:1141-1143` | **0** | 0 | 0 |
| F6 | cluster presente pero `pc.vrp_mw = 0` | `index.html:992` | 2.173 | 0 | 215 |
| F8 | filtro de lejanas del **mapa** | `index.html:2539` | 10.836 sin marcador | — | 108 |
| F9 | «sólo el píxel primario» | `index.html:2546-2549` | **162.608 de 185.809 px (87,5 %)** | — | — |
| F9b | └ aún ocultos con «Todos los píxeles» (cap 10) | `index.html:2545` | 101.478 px (54,6 %) | — | — |
| F10 | ventana `_recent.json` de 100 días | `index.html:901` | 46.004 records (79,7 %) no se descargan | — | — |

---

## F2 — «Solo cráter»: el más grande, y es un error de etiqueta

**Qué suprime.** `mirovaEqVrp` devuelve 0 en cuanto `r.distance_class` no dice `"summit"`
(`index.html:985`), **antes de mirar el cluster**. Y `distance_class` la fija el
`final_hotspot`, que en MODIS viene del path de MIR absoluto: el gradiente topográfico lo
lleva al salar o al valle (A69/A82). El cluster —de donde sale la magnitud— se queda en el
cráter. Es A46 en su forma pura, con la magnitud y la clase discrepando.

Cuatro noches de Láscar, verificadas una a una en el JSON:

```
2026-02-09 01:40 MODIS_TERRA  final_hotspot 27,07 km → "far"   pc: 0,893 MW, 7 px, 3,52 km, geo_class summit
2026-02-09 07:20 MODIS_AQUA   final_hotspot 26,61 km → "far"   pc: 1,179 MW, 10 px, 2,00 km, summit
2026-02-12 02:00 MODIS_TERRA  final_hotspot 27,79 km → "far"   pc: 1,786 MW, 4 px, 2,95 km, summit
2026-02-12 07:35 MODIS_AQUA   final_hotspot 33,33 km → "far"   pc: 0,393 MW, 9 px, 0,80 km, summit
```

**El costo medido**: cruzando contra las alertas MIROVA (CONS ∪ OCR, nocturnas, alias
completo) hay **72 noches-sensor** con un record `far` oculto y alerta publicada; **47 quedan
huérfanas** — ninguna detección visible ese día en ese sensor. **46 son Láscar MODIS**, la
única serie con ground truth MODIS real.

**Categoría A72.** Hay que partir el conjunto en dos, y esto es lo importante:

- Los **1.163 MODIS con el cluster fuera del inner** (mediana 19–24 km del centro,
  0 % de confirmación MIROVA en diez de once volcanes) son el **artefacto** A69/A82: el
  campo difuso topográfico. Ocultarlos en el frontend es exactamente el parche que A72
  prohíbe — la raíz es no generarlos.
- Los **8.992 con el cluster en el cráter** no son artefacto ni señal sub-umbral: son
  **detecciones correctas mal etiquetadas**. En Láscar la confirmación de MIROVA lo prueba
  (84 noches). En los otros diez el ground truth MODIS **no existe** (88 de 96 alertas
  MODIS de referencia son de Láscar), así que su realidad es **indefinida**, no «débil» —
  pero la etiqueta `far` sigue siendo incorrecta por construcción, independientemente de
  si la señal es real.

En VIIRS el problema casi no existe: sólo 2 de 90 records `far` de V375 y 2 de 395 de V750
tienen el cluster intra-inner. **Es un defecto específico de MODIS.**

**¿Las tres vistas?** El filtro está en las tres. Pero **`mosaico.html` no tiene toggle de
lejanas**: llama `mirovaEqVrp(r, innerKm, false)` siempre (`mosaico.html:366`), así que ahí
la supresión es permanente y sin escape. `index` (3506/3515) y `diario` (699) sí la ofrecen.

**¿Se avisa?** No hay contador. El botón «Incluir lejanas» existe, pero nada dice que
apagado esconde 10.640 records. En el mapa la supresión es total (`return` en
`index.html:2539`) y el comentario de `index.html:809-811` **todavía afirma lo contrario**
— desactualizado desde S26 B.

## F1 — `isValidDetection`: 562 records que diario y mosaico sí dibujan

`index.html:1371-1375` exige `vrp_mw > 0` o `triggered_test1`. 21.186 records no lo cumplen
— casi todos son ceros legítimos del pipeline. Pero **807 traen `primary_cluster.vrp_mw > 0`**
y, de esos, **562 tienen el cluster summit dentro del inner**: 547 caen por el **piso de VRP**
(`diag_vrp_raw_mw` 0,138 < `diag_vrp_floor_mw` 0,15, cluster a 0,76 km del cráter) y 21 por
`discarded_reason` (210 de Villarrica MODIS son `cluster_too_large_for_volcano`; esos sí son
descartes correctos y quedan fuera de los 562 por su distancia).

**Ni `diario.html` ni `mosaico.html` tienen este predicado** — cero apariciones de
`isValidDetection`, `triggered_test1` o `discarded_reason` en ambos archivos. Su
`eqVrpDisplay` (`diario:372`, `mosaico:364`) va directo a `mirovaEqVrp`. **Los 562 records
aparecen en diario y mosaico y no en index**, 114 MW, 28 en noches con alerta MIROVA. El fix
H3 de S77 (PR #170) nunca se replicó a las otras dos vistas.

**Categoría A72**: señal real sub-umbral (cat-b). Cluster crateriano, mediana 0,45–4 km. El
piso de VRP es una decisión del pipeline, defendible; lo que no es defendible es que tres
vistas del mismo dato den tres respuestas distintas.

## F9 — «sólo el píxel primario»: 87,5 % de los píxeles no se dibujan

`index.html:2546-2549`. Con el default se dibuja 1 píxel por record: **162.608 de 185.809
píxeles quedan fuera**. El toggle «Todos los píxeles» no los recupera: el cap
`PIXEL_CAP_PER_RECORD = 10` (`index.html:2545`) deja **101.478 (54,6 %) permanentemente
invisibles**. Es una decisión de legibilidad razonable — 86 mil marcadores en PCC no se
pueden leer — pero **no hay ningún aviso de cuántos píxeles tiene el record**. `diario` y
`mosaico` no dibujan mapa, así que no aplica.

## Los tres filtros inertes (declarado ≠ efectivo)

Verificados con un barrido independiente sobre los JSON, no con el script principal:

- **Cap de 50.000 MW**: **0 records** en todo el dataset lo superan. El cap del pipeline
  funciona; la defensa del frontend nunca dispara.
- **`isCirrusArtifact`** (S90): **0 records**. Hay 13.626 con `t_max_k` bajo 0 °C, pero el
  `mirovaEqVrp` **máximo** entre ellos es 5,0 MW y el gate pide **> 10 MW**. El comentario de
  `index.html:1105-1107` dice que oculta 26 records «incl. PCC 1362/892 MW» — **hoy oculta
  cero**. La magnitud focal adoptada en S107-S112 (`focal_magnitude`, `single_pixel_mode`)
  bajó `pc.vrp_mw` por debajo del umbral contra el que se calibró el filtro.
- **`isDiffuseFieldArtifact`** (S93): **0 records**. Sólo 293 tienen `pc.n_pixels ≥ 100`, y
  ninguno llega a los 50 MW que exige.
- **`pc.centroid_dist_km > innerKm`** (el guard de S33): **0 records**.

Esto es A87 al revés: los filtros dejaron de marcar, y eso no prueba que el fenómeno se
haya ido — prueba que la magnitud contra la que se calibraron cambió de escala.

## Divergencias menores verificadas

- `diario.html:242` — la rama sin `primary_cluster` devuelve `r.vrp_mw` **sin cap**, mientras
  `index.html:981` sí capea; el comentario de `diario:254` dice «Coherente con index.html».
  Hoy no afecta a nadie (F4 = 0 records), pero la afirmación es falsa.
- El cinturón `_mirova_confirmed` que protege a los filtros de artefacto **sólo existe en
  `index`** (`index.html:1346-1359`); `diario:334` y `mosaico:326` lo admiten. Con F5 inerte
  no cuesta nada hoy.
- El mapa tiene **universo propio**: `(vrp_mw ?? vrp_mir_mw) > 0` (`index.html:2456`), sin
  `isValidDetection` ni filtro de artefacto. 22 records se dibujan en el mapa y no aparecen
  en el gráfico.
- **`_recent.json` (100 días)**: el 79,7 % de los records no se descarga al abrir. No se
  pierde nada —la ventana por defecto es de 30 días y el completo se baja a los >90 d— pero
  ninguna vista dice que está mirando una ventana recortada.

## Lo que no se puede decidir con lo que hay

La categoría A72 de los **8.992 MODIS mal etiquetados fuera de Láscar** es **indefinida**:
sin ground truth MODIS en esos diez volcanes no se puede separar el foco crateriano real del
gradiente topográfico a 1 km (A82/A83). Lo que sí queda establecido, y no depende del ground
truth, es que **la etiqueta que los apaga se calcula desde un campo que no es el que produce
la magnitud**.

## Nota fuera de dominio

El Núcleo F5' ya no reduce: baja la magnitud en 6.441 records de VIIRS375, pero el total
visible **sube** de 9.767 a 10.203 MW. Mismo mecanismo que los filtros inertes: se calibró
contra un `pc.vrp_mw` que la magnitud focal cambió. Es eje de magnitud, no de supresión.
