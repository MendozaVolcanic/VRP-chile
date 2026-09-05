# S134 · F4 — El solape del barrido VIIRS y la ley de área intermedia

**Veredicto en una línea: la hipótesis del solape queda CONFIRMADA en su predicción central
—descontar el terreno duplicado lleva el borde del barrido de 1,360 a 1,007 y deja los dos
bins de cenital en banda— pero la ley intermedia NO pasa el criterio pre-registrado completo,
porque la cola de razones > 2 se queda en 13,8 % contra el 10 % exigido.**

Auditoría read-only. No se tocó `pipeline/`, ni ningún perfil, ni `data/`. Esto **no adopta
nada**: si se quiere llevar adelante, es una propuesta de A/B para S135 con tag defensivo y
confirmación de Nicolás (A45).

Números en `experiments/_s134_audit/f4/resultados.json` y `cola_composicion.json` (regla S91:
ningún número de este documento fue transcrito a mano; salen de esos JSON).

---

## 1. El fenómeno, antes que el código

El espejo de VIIRS barre de lado a lado y en cada barrido apoya en el terreno una franja de
32 filas I-band. En el nadir esa franja mide **11,87 km** a lo largo de la órbita; en el borde
del barrido, **25,60 km**. Pero el satélite avanza siempre lo mismo entre barrido y barrido
—esos mismos 11,87 km—, porque eso lo fija la órbita y el período del espejo, no el ángulo.
De modo que hacia el borde cada barrido vuelve a mirar terreno que el anterior ya miró. Es el
efecto *bow tie*, y el propio ATBD lo cuantifica: *"maximum overlap over 50 percent at 56.063
degrees"*.

Para la magnitud eso significa algo concreto y físico: **un foco caliente cerca del borde del
barrido aparece en píxeles de dos barridos distintos, y al sumar el cúmulo su energía se cuenta
dos veces.** El área geolocalizada —el producto de las distancias entre centros vecinos— describe
bien el terreno que cada detector integra, pero no descuenta esa duplicación. Por eso el brazo
`geoloc` de S133 corrigió el gradiente y se pasó de largo.

## 2. La derivación de f(θ), con las citas

Todo lo que sigue está leído en los PDF de `documentacion/`. Ninguna cifra viene de memoria.

| id | dato | fuente |
|---|---|---|
| G1 | I-band: nadir 0,371 km (vuelo) × 0,388 km (barrido); fin de barrido 0,80 × 0,789 | `VIIRS_Geolocation_ATBD_2014.pdf`, Tabla 2.2-1, pág. 13 |
| G2 | franja de un barrido a lo largo del vuelo: *"from 11.87 kilometers at nadir to 25.60 kilometers at a scan angle of 56.063 degrees"* | ídem, §3.4.2.1, pág. 95 |
| G3 | *"This overlap is unaffected by the VIIRS pixel aggregation strategy which applies only in the cross-track direction"* | ídem, §3.4.2.1, pág. 95 |
| G4 | zonas de agregación: 3:1 hasta 31,589°, 2:1 hasta 44,680°, 1:1 hasta 56,063° | ídem, §2.2.1 pág. 12 y §3.3.2.1.2 |
| G5 | borrado bow-tie, verbatim: *"deleting 4 of the 32 detectors from the output data steam for the middle (Aggregate 2) part of the scan and 8 of the 32 detectors for the edge (No aggregation) part of the scan"* | `JPSS_ATBD_VIIRS_Imagery_RevE.pdf`, §3.2.4, pág. 22-23 |

G1 y G2 se validan entre sí: 32 × 0,371 = 11,87 y 32 × 0,80 = 25,60. G3 es lo que autoriza a
descontar en **un solo eje** (el del vuelo). G5 es lo que impide contar el solape crudo: el
instrumento **ya borra a bordo** parte de los píxeles duplicados, así que de las 32 filas llegan
al suelo **32 / 28 / 24** según la zona, y ese borrado entra en la cuenta.

La fracción del área entregada que corresponde a terreno **nuevo**:

    D(θ) = 11,87 · r(θ) · k(θ)/32          (extensión efectivamente entregada)
    f(θ) = min(1 , 11,87 / D(θ)) = min(1 , 32 / (k(θ)·r(θ)))

con k = 32/28/24 (G5) y r(θ) = S(θ)/S(0), el crecimiento del píxel **a lo largo del vuelo**, que
es el cociente de distancia oblicua. En este eje **no hay sec(cenital)**: el eje de vuelo es
perpendicular al plano de barrido y no se proyecta. Eso es exactamente lo que explica que a lo
largo del vuelo el píxel crezca 2,16× mientras a lo ancho crecería 6× sin agregación (ATBD pág. 12),
y es la comprobación interna de que la derivación va por el eje correcto.

**f(θ) resultante** (`resultados.json` → `geometria_atbd.f_en_angulos_notables`; el eje de entrada
es el cenital de superficie, que es lo que trae el record):

| cenital | θ barrido | r | filas | **f** |
|---:|---:|---:|---:|---:|
| 0° | 0,00° | 1,000 | 32 | **1,000** |
| 20° | 17,69° | 1,056 | 32 | 0,947 |
| 30° | 26,37° | 1,134 | 32 | 0,882 |
| 40° | 34,82° | 1,258 | 28 | 0,909 |
| 50° | 42,88° | 1,448 | 28 | 0,789 |
| 55° | 46,69° | 1,579 | 24 | 0,844 |
| 70° | 56,06° | 2,157 | 24 | **0,618** |

Los dos saltos hacia arriba (40° y 55°) no son un error: son el borrado bow-tie entrando en
acción justo en las fronteras de zona. La curva es **serrucho**, no monótona, y eso deja huella
en los resultados (§5).

**Simplificaciones declaradas.** (S1) f se aplica como factor multiplicativo a la magnitud del
record: es exacto sólo si todos los píxeles del cúmulo comparten ángulo y zona. El área por píxel
**no está persistida** en los JSON del brazo `geoloc` —verificado leyendo las claves del record—,
y bajar granules está prohibido en esta sesión, así que el factor es la única vía. (S2) La altura
efectiva se **calibra** (801,6 km) para que r(56,063°) reproduzca el 2,1567 = 25,60/11,87 del ATBD,
en vez de fijar de memoria un valor de órbita; se reporta además la versión con H = 829 km nominal
como sensibilidad, y **no cambia nada** (1,010 contra 1,007 en el borde). (S3) el record trae el
cenital de superficie, no el ángulo de barrido: se convierte con sin θ = Re/(Re+H)·sin ζ.
(S4) **tensión declarada y no resuelta**: el ATBD §2.2.2 dice que el solape empieza *"a partir de
unos 19 grados"*, y esta derivación lo hace empezar apenas θ > 0. Si eso está mal, está mal en el
sentido de descontar de más cerca del nadir — que es justo lo que el control negativo vigila.

## 3. Los dos controles del instrumento

**Control positivo — reproducir S133 antes de creerle nada a f.** Los siete números publicados
en `docs/s133/AB_AREA_VEREDICTO_CHUNK1.md` se reproducen **exactos a 3 decimales** (control
0,879 / 0,619 / cola 4,2 %; geoloc 0,958 / 1,360 / cola 20,1 %; corona 1,303), sobre 643 pares,
el mismo denominador que S133 declaró. `resultados.json` → `control_positivo_reproduce_S133.pasa
= true`. El instrumento está vivo y mide lo mismo que midió S133.

**Control negativo — f no debe tocar el nadir.** f mueve el bin 0-15° un **1,88 %** (0,958 → 0,940),
por debajo del 3 % tolerado. `control_negativo_f_no_toca_el_nadir.pasa = true`.

**Si el instrumento estuviera muerto se vería distinto.** Cada bin declara su n y un bin con
n < 15 se marca *no evaluable* en vez de contarse como cero. Los dos bins juzgados tienen n = 111
y n = 210, así que ninguno es un cero ambiguo.

## 4. Las tres leyes, lado a lado

Razón mediana de nuestra magnitud contra la de MIROVA, **por pasada** (≤ 20 min, ALERTA nocturna
03-09 UTC, CONS ∪ OCR), VIIRS375, 8 volcanes, ventana **2026-04-01 → 2026-05-31**, **643 pares**.
IC 95 % por bootstrap de 5000 con semilla fija.

| ley | nadir 0-15° (n=111) | borde 50°+ (n=210) | cola > 2 |
|---|---:|---:|---:|
| **control** (área nadir fija, lo actual) | 0,879 [0,836–0,953] | **0,619** [0,540–0,762] | **4,2 %** |
| **geoloc** (área medida, brazo S133) | 0,958 [0,881–1,025] | **1,360** [1,170–1,508] | 20,1 % |
| **geoloc × f(θ)** (ley intermedia, este trabajo) | **0,940** [0,878–1,019] | **1,007** [0,891–1,187] | 13,8 % |
| geoloc × f(θ), H=829 km (sensibilidad) | 0,940 | 1,010 | 13,7 % |

Los cinco bins de la ley intermedia: 0,940 · 0,986 · 0,896 · **0,786** · 1,007.

**Veredicto contra el criterio pre-registrado** (congelado en el encabezado del script antes de
correr, y no se movió):

| | criterio | resultado |
|---|---|---|
| C1 | los dos bins juzgados con mediana en 0,90–1,10 | ✅ **PASA** (0,940 y 1,007) |
| C4 | pares con razón > 2 en ≤ 10 % | ❌ **NO PASA** (13,8 %) |

**No adoptar.** La ley intermedia es claramente mejor que las dos anteriores en el centro de la
distribución, y sigue siendo insuficiente en la cola.

---

## 5. Hallazgos

### H1 · La cola de razones > 2 no es el gradiente cenital: es la ground truth sub-MW
- **SCRIPT:SALIDA** — `experiments/_s134_audit/f4/f4_cola_composicion.py` → `cola_composicion.json`
- **QUÉ PASA** — De los 89 pares en cola bajo la ley intermedia, la fracción es **17,1 % en los
  514 pares donde MIROVA publicó < 0,5 MW**, contra **0,8 % en los 118 pares de 0,5-2 MW** y
  **0 % en los 11 pares de 2-10 MW**. Físicamente: cuando MIROVA reporta 0,1 MW, cualquier
  diferencia de recorte del cúmulo o de píxel de más produce una razón de 3 o 5 sin que la
  magnitud absoluta cambie nada relevante. La cola es aritmética de denominadores chicos sobre
  señal sub-umbral (marco A54/A68), no un defecto de la ley de área. Por volcán: Chaitén 33,3 %
  (n=27) y PCC 28,3 % (n=99) concentran la cola — los dos regímenes difusos.
- **CÓMO SE VE EN EL DASHBOARD** — Invisible como "error": son detecciones de fracciones de MW
  que el operador ve como actividad de fondo. Lo que sí cambia con la ley de área es la altura de
  la barra en las pasadas oblicuas.
- **CÓMO REPRODUCIRLO** — `python experiments/_s134_audit/f4/f4_cola_composicion.py`
- **CONFIANZA** — CONFIRMADO (medido)
- **GRAVEDAD 2** — no tuerce una alerta; pero **sí invalida el criterio C4 como instrumento para
  juzgar leyes de área**: C4 está midiendo el régimen sub-MW, no la geometría del barrido.

### H2 · La ley intermedia deja un pozo en el bin 35-50°, y es el borrado bow-tie
- **SCRIPT:SALIDA** — `resultados.json` → `leyes.geoloc_x_f_solape.por_bin`
- **QUÉ PASA** — Los cinco bins quedan 0,940 · 0,986 · 0,896 · **0,786** · 1,007: no es monótono.
  El motivo es físico y está en la derivación: f tiene dos **saltos hacia arriba** en las fronteras
  de zona (θ = 31,589° y 44,680°), donde el instrumento empieza a borrar filas y de golpe deja de
  haber tanto terreno duplicado. El bin 35-50° de cenital cae en el tramo donde f ya bajó pero el
  borrado todavía no compensa. El criterio pre-registrado sólo juzga los extremos, así que esto
  **no cambia el veredicto** — pero deja ver que la corrección no es un simple reescalado suave.
- **CÓMO SE VE EN EL DASHBOARD** — invisible (el flag está apagado; esto es análisis off-line).
- **CÓMO REPRODUCIRLO** — `python experiments/_s134_audit/f4/f4_solape_ley_intermedia.py`
- **CONFIANZA** — CONFIRMADO (medido); la atribución al borrado bow-tie es CONFIRMADA por la
  tabla de f (los saltos están en 40° y 55° de cenital, exactamente en las fronteras).
- **GRAVEDAD 2**

### H3 · La hipótesis del solape predijo la dirección Y el tamaño del error, sin ajustar nada
- **SCRIPT:SALIDA** — `resultados.json` → `leyes` (borde: control 0,619 → geoloc 1,360 → ×f 1,007)
- **QUÉ PASA** — f(θ) se derivó **sólo** de los cuatro números del ATBD (11,87 / 25,60 / las dos
  fronteras de zona / las 32-28-24 filas). No hay ni un parámetro ajustado contra el resultado. Y
  lleva el borde de 1,360 a 1,007, o sea al 1,0 dentro de un 1 %. Un mecanismo que acierta la
  magnitud sin parámetros libres es evidencia fuerte de que el solape **es** lo que sobraba.
- **CÓMO SE VE EN EL DASHBOARD** — hoy nada: el flag `ENABLE_GEOLOCATED_PIXEL_AREA` está apagado y
  el operador sigue viendo el control, que sub-reporta ~38 % en las pasadas oblicuas.
- **CÓMO REPRODUCIRLO** — `python experiments/_s134_audit/f4/f4_solape_ley_intermedia.py`
- **CONFIANZA** — CONFIRMADO para el número; SOSPECHA para la interpretación causal (un
  A/B con reproceso real, aplicando f **por píxel** dentro del pipeline, es lo que lo probaría —
  A18: el filtrado off-line no re-corre la selección de cúmulo).
- **GRAVEDAD 3** — es la ruta más prometedora para cerrar el déficit del borde, que hoy hace que
  una anomalía vista de reojo se publique con ~60 % de su magnitud.

### H4 · El área por píxel del brazo geoloc no está persistida en el record
- **ARCHIVO:LÍNEA** — claves del record en `~/ab_area/s133area-_s133_area_geoloc-Lascar/Lascar.json`;
  productor en `pipeline/scan_geometry.py:319` (`resolve_viirs_pixel_areas`)
- **QUÉ PASA** — El brazo `geoloc` calcula un área por píxel y la usa para la magnitud, pero no
  guarda ni el área ni un agregado de ella. Cualquier auditoría posterior de la ley de área queda
  obligada a re-derivar la geometría desde el ángulo (como acá, simplificación S1) o a volver a
  bajar granules. Es una asimetría de esquema del tipo que A46 describe: el pipeline calcula la
  variable y no la retorna (A7).
- **CÓMO SE VE EN EL DASHBOARD** — invisible.
- **CÓMO REPRODUCIRLO** — `python -c "import json,io;d=json.load(io.open(r'<ruta>'));print(sorted(d['records'][0].keys()))"`
- **CONFIANZA** — CONFIRMADO
- **GRAVEDAD 1** — no afecta la alerta; encarece toda auditoría futura de este frente.

---

## 6. VERIFICADO LIMPIO

Lo que se miró en esta sesión y está sano, con el comando que lo confirma. Que no haga falta
volver a mirarlo vale tanto como los hallazgos.

| qué | estado | cómo se confirmó |
|---|---|---|
| Los 7 números publicados de S133 (control 0,879/0,619/4,2 %; geoloc 0,958/1,360/20,1 %; corona 1,303) | **exactos a 3 decimales** | `f4_solape_ley_intermedia.py` → `control_positivo_reproduce_S133.pasa=true` |
| `sensor_zenith_deg` en los records VIIRS375 de los tres brazos | **2040/2040 en cada brazo (100 %)** | `python -c` sobre `~/ab_area/*/*.json` (§verificación de sustrato) |
| `f5_core_vrp_mw` en los mismos records | **1873/2040 = 91,8 %** (control y geoloc), 1872 en corona; el fallback A46 a `primary_cluster.vrp_mw` cubre el resto y está declarado en el script | mismo comando |
| Denominador de pares y ventana | **643 pares, 2026-04-01 → 2026-05-31**, coincide con lo que S133 declaró | `resultados.json` → `_ventana_utc`, `leyes.*.n_pares` |
| `pixel_areas_from_geolocation` mide paso entre centros en los dos ejes por diferencias centradas, invalidando el borde del granule (no extrapola) y devolviendo NaN donde la geolocalización viene corrupta | **coherente con su docstring**; el NaN cae de vuelta al área modelada en `resolve_viirs_pixel_areas`, no se propaga | lectura de `pipeline/scan_geometry.py:248-365` |
| Sensibilidad al valor de la altura orbital (801,6 km calibrada vs 829 km nominal) | **irrelevante**: 1,007 vs 1,010 en el borde | `resultados.json` → `leyes.geoloc_x_f_solape_H_nominal_829km` |
| Coherencia interna del ATBD (Tabla 2.2-1 × 32 filas = extensión del barrido de §3.4.2.1) | **cierra**: 32×0,371 = 11,87 y 32×0,80 = 25,60 | lectura de los PDF, citas en §2 |
| No se modificó ningún archivo del repositorio fuera de `experiments/_s134_audit/f4/` | **confirmado** | los tres archivos creados están todos bajo esa ruta |

**Lo que NO se pudo verificar y queda como SOSPECHA declarada**: que f aplicado **por píxel dentro
del pipeline** dé lo mismo que el factor multiplicativo por record (S1); y la tensión del "19 grados"
del ATBD §2.2.2 contra una f que empieza a descontar apenas θ > 0 (S4). Las dos requieren granules,
y bajar granules estaba prohibido en esta sesión.

## 7. Lo que corresponde hacer, si alguien decide seguir

1. **No adoptar** nada. El criterio pre-registrado no se cumple entero y no se mueve el poste.
2. Si se abre un A/B en S135, que el brazo aplique f **por píxel** dentro de
   `resolve_viirs_pixel_areas` (no como factor por record), con tag defensivo y confirmación de
   Nicolás (A45), y que se valide con reproceso real, no con filtrado off-line (A18).
3. **Revisar el criterio C4 antes de reusarlo** — no como una concesión, sino porque H1 muestra
   que está midiendo el régimen sub-MW y no la ley de área. Cambiar un criterio *después* de que
   falla exige justificarlo por el mecanismo y con el número que lo demuestra; ese número está en
   `cola_composicion.json`. La decisión es de Nicolás, no de este informe.
