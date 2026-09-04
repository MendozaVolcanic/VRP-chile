# Bloque de arranque S134

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S133. Esa sesión midió los tres flags que S132 dejó apagados,
encontró que el A/B del área no se podía correr, lo cableó, y dejó LOS DOS A/B DESPACHADOS
(PR #583, mergeado, squash bc7f3f2d).

═══════════════════════════════════════════════════════════════════
PRIMERO DE TODO: BAJAR LOS RESULTADOS DE LOS DOS A/B.
No commitean nada. Los artefactos se borran a los 14 días.
═══════════════════════════════════════════════════════════════════

  gh run view 33872821788    # A/B B22        (4 jobs: 2 volcanes × 2 brazos)
  gh run view 33872836355    # A/B área chunk 1 (24 jobs: 8 volcanes × 3 brazos)

  gh run download 33872821788 --dir data/
  gh run download 33872836355 --dir data/   # ⚠️ chunk 1 INCOMPLETO: 13 de 24 jobs
                                            # murieron por timeout. Ver abajo.

⚠️ EL A/B DEL AREA HAY QUE RELANZARLO ENTERO. El chunk 1 fallo 13 de 24 jobs: el
`timeout-minutes` era 150 y los jobs tardan 128-133 min los que terminan. Peor: los 3 que
sobrevivieron son TODOS del brazo de control, asi que no hay un solo par comparable.
Ya esta subido a 300 min (medido, A15). Relanzar los 3 chunks desde cero:
  gh workflow run reproc-s133-area-ab.yml --ref main -f start=2026-04-01 -f end=2026-05-31 -f overwrite=true

  python experiments/_s133/analizar_ab_b22.py    # criterios C1-C4, congelados
  python experiments/_s133/analizar_ab_area.py   # los 4 criterios, congelados

Si el área terminó bien, faltan sus chunks 2 y 3 (el criterio necesita los 152 días):
  gh workflow run reproc-s133-area-ab.yml --ref main -f start=2026-06-01 -f end=2026-07-31 -f overwrite=false
  gh workflow run reproc-s133-area-ab.yml --ref main -f start=2026-08-01 -f end=2026-08-31 -f overwrite=false

Leé, en este orden:
  1. tasks/BLOQUE_ARRANQUE_S134.md        (este bloque)
  2. docs/s133/SUSTRATO_AREA_GEOLOCALIZADA.md
  3. docs/s133/B22_EVIDENCIA.md           (criterios C1-C4 pre-registrados)
  4. docs/s132/AB_AREA_GEOLOCALIZADA.md   (criterio del área, NO se toca)

⚠️ LOS CRITERIOS ESTÁN CONGELADOS. Si uno falla, se reporta y la decisión pasa a Nicolás.
No se mueve el poste después de ver el dato (A91, A66).

NADA MÁS CORRIENDO. Suite 1124 passed · 3 skipped · 0 xfail. Los 3 flags APAGADOS.
```

---

## Lo que hizo S133

**El hallazgo que cambió el plan.** `ENABLE_GEOLOCATED_PIXEL_AREA` estaba en el perfil desde
S132 y **no lo leía ningún módulo de producción**; `pixel_areas_from_geolocation`, probada
contra el ATBD y con siete tests verdes, no tenía una sola llamada fuera de esos tests. El
brazo «área» del A/B habría sido idéntico al control. La prueba verde de la pieza aislada
convivía con que nadie la llamara. Cableado en `scan_geometry.resolve_viirs_pixel_areas`,
que concentra los tres modos de área en un lugar porque I-band y M-band los calculan por
separado y cablear uno solo dejaría el otro mudo.

**B22 es menos riesgoso de lo que decía el bloque anterior.** Satura en 2 de 644.835
píxeles, o sea divergimos del paper en ~100 % de los records. Pero el efecto sobre el fondo
es de 0,0036 K: `diag_sigma_bg_k` mide heterogeneidad del terreno, no ruido del sensor, y su
mínimo histórico ya es 5,4× el NEΔT de B21. La métrica que S131 propuso vigilar **no puede
mostrar el cambio** (A87). Lo que falta medir, y es el motivo real del A/B, es el sesgo de
calibración entre bandas sobre la magnitud (C3).

**El C2 del A/B de `distance_class` era tautológico**, verificado: normalizado por
`inner_radius` da 1,000000 exacto, porque es la definición del flip. C2' propuesto en
`docs/s133/C2_NORMALIZADO_INNER_RADIUS.md`, no adoptado ni pre-registrado.

## La regla nueva: A92

Al cablear el área, la llamada `viirs_pixel_areas` pasó a ser `resolve_viirs_pixel_areas` y
**el tripwire de S103 siguió en verde**, porque el nombre viejo es subcadena del nuevo. Se
barrió la suite entera: de 19 asserts por subcadena, 2 vulnerables, ninguno roto todavía,
los dos endurecidos; ahora el barrido da 0. El script queda en
`experiments/_s133/auditar_guards_por_subcadena.py` para volver a correrlo al agregar guards.

Nació de una advertencia de Nicolás a mitad de sesión: «muchas veces arreglos que hacíamos
rompían otras funciones, revisa bien ese tipo de comprobaciones». La advertencia encontró
algo real, y era mío.

## Cómo se verificó que el cableado no rompió nada

La suite verde prueba que lo que tiene test sigue andando, no que el camino operacional
devuelva lo mismo. Además:
- **Prueba diferencial contra `origin/main`** (`experiments/_s133/regresion_diferencial_area.py`):
  se carga el `scan_geometry.py` de main y se corre al lado del actual. 48 comparaciones,
  dos bandas × doce casos × dos modos, incluidos los bordes. Las 48 idénticas bit a bit.
- **Test de no-op** con el flag apagado, en los dos modos (S126).
- Ningún consumidor externo; `lat`/`lon` ligadas antes de la llamada.

## Dos correcciones a suposiciones de la propia sesión

- `enable_local_cluster_magnitude_viirs375` **no es top-level**: se lee de `_cfg["paths"]`
  (`profile.py:469`). Puesto arriba habría sido no-op silencioso y el tercer brazo habría
  sido el segundo. A89 otra vez, y la atrapó verificar cargando el perfil, no leyéndolo.
- El `max-parallel: 1` del A/B del área se justificaba por la cuota de Earthdata, no por la
  carrera de A47. Subido a 8 con el precedente medido: `nrt.yml` corre 8 sobre 45 volcanes
  contra la misma cuota, 12 veces al día. Y MODIS apagado en los tres brazos, porque por AST
  ninguno de los dos flags llega a `process_modis.py`.

## Limitación del criterio del área, dicha antes de correrlo

Pide «≥6 de 8 volcanes en banda», pero con el piso de pares de S131 sólo **6 de los 8**
tienen población en ambos bins de cenital (Chaitén 12 en el oblicuo, Villarrica 1). El «6 de
8» se puede cumplir, pero los 6 evaluables tendrían que pasar todos. No hay noveno volcán
con sustrato. El criterio **no se tocó**.

## Lo operacional que S133 arregló al final

**La cadencia del cron cayó 51 % el 2026-08-27 y estuvimos ocho días sin verlo.** GitHub dejó
de entregar la mitad de los eventos `schedule` del repo, uniformemente sobre los cuatro
workflows con cron. Es externo: cero corridas canceladas (no es la concurrencia), los `cron`
declarados no cambiaron, y golpea por igual a los cuatro. **No se perdió un solo record** —
116 records/día antes contra 121 después, 11/11 volcanes todos los días — porque cada corrida
procesa el día completo. Se degrada la latencia, de ~3-4 h a ~7 h. Ningún monitor falló:
ninguno mide la AUSENCIA de corridas, y una corrida que no ocurre no deja rastro. Se agregó
`scripts/medir_cadencia_cron.py` al healthcheck diario. Doc: `docs/s133/CADENCIA_DEL_CRON.md`.

**El watchdog llevaba 22 comentarios sobre un workflow borrado hace tres meses** (issue #567).
Consultaba la API, que sigue devolviendo los borrados con `state: "active"`. Arreglado: la
fuente de verdad de «existe» es el repo. **La #567 sigue abierta: cerrarla es decisión tuya.**

## Issue #506 (Villarrica 35×): RESUELTA, verificado con data fresca

El auto-audit del 31-ago da **Villarrica 0,804× con n=13 noches**, dentro de banda. Se
verificó además noche por noche contra las pasadas exactas que MIROVA publicó en agosto:

| noche | MIROVA | nuestro | razón |
|---|---:|---:|---:|
| 08-18 05:48 | 1,86 | 1,62 | 0,87 |
| 08-21 05:48 | 1,82 | 1,65 | 0,91 |
| 08-23 05:54 | 1,33 | 0,92 | 0,69 |
| 08-24 05:36 | 2,21 | 1,90 | 0,86 |

Villarrica tuvo una escalada real en agosto (12 alertas contra 0-5 de los meses previos) y la
seguimos bien. **Se puede cerrar la #506**, es decisión tuya.

⚠️ Dos trampas en las que caí al verificar esto, por si alguien repite el camino: comparar
nuestra mediana sobre TODAS las pasadas contra la mediana de MIROVA sobre sus ALERTAS da un
falso «sub-reportamos 24×» — son poblaciones distintas (A90). Y truncar el diccionario del
audit en un `print` propio se lee como «el audit está ciego». Las dos las atrapó mirar los
eventos concretos en vez del agregado (A79).

Lo que SÍ está fuera de banda hoy, y es el frente conocido de déficit en régimen débil de
S124/S125: **Lastarria 0,415 · Láscar 0,465 · Isluga 0,603**, los tres sub-estimando.

## El incidente del 2026-09-04: la alerta que no vimos (leer `docs/s133/AUDITORIA_DEL_INCIDENTE.md`)

Nicolás preguntó por qué MIROVA tenía una anomalía MODIS de **4,75 MW en Villarrica**
(07:50 UTC) y nosotros no. Debajo había **cinco defectos**, cuatro silenciosos. Ya la
tenemos: **3,859 MW a 0,85 km, summit, razón 0,81×**. No hubo que tocar detección ni
magnitud — el dato nunca había llegado.

| # | defecto | PR |
|---|---|---|
| 1 | El NRT de MODIS pedía `MYD021KM_NRT` v61, que **no existe** (LANCE usa `MYD021KM` v`6.1NRT`) | #587 |
| 2 | Los granules NRT de MODIS se guardaban como `standard` (marca `.NRT.`, no `_NRT`) | #588 |
| 3 | La cadencia del cron cayó 51 % y ningún monitor mira la AUSENCIA de corridas | #585 |
| 4 | El poller de TIF: `timeout-minutes: 10` contra 12,3 min de mediana | archive #2 + commit |
| 5 | VegStress-v1 caído desde el 13-ago: faltan los secrets de Sentinel Hub | **pendiente de Nicolás** |

**Verificado en vivo**: el poller volvió a correr (231 snapshots, primera corrida exitosa
desde el 27-ago). El TIF de las 07:50 se perdió igual: MIROVA sobrescribe su imagen «Last»,
así que lo capturado ya es el de las 13:15. Eso es irreversible y es la razón por la que el
poller importa.

**Ojo con el patrón**: ninguno de los cinco produjo un error. Produjeron un cero, una
etiqueta plausible, una métrica verde y una palabra ambigua (`cancelled` sirve para timeout
y para concurrencia — me despistó y mi primer diagnóstico del poller estuvo incompleto).

## Sigue esperando a Nicolás

- Los tres flips: `ENABLE_MODIS_B22_PRIMARY`, `ENABLE_GEOLOCATED_PIXEL_AREA`,
  `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`.
- El marcador «extensión» de PCC. Pregunta volcanológica, no de código.
- Rotar el PAT de `~/.claude/settings.json`.
- **Cargar los secrets `SH_CLIENT_ID` y `SH_CLIENT_SECRET` en VegStress-v1** (caído hace 3 semanas).
- Cerrar las issues #506 (Villarrica, resuelta) y #567 (watchdog, arreglado) si estás de acuerdo.
- Persistir `diag_d9_capped` en el pipeline (hoy el tope de 5 MW se reconoce por el valor
  en el frontend, que funciona pero es frágil; A72 pide el flag en el algoritmo).

## Estado al cerrar S133

**PR**: #583 (squash a main, `bc7f3f2d`). **Suite**: 1124 passed · 3 skipped · 0 xfail.
**Tag defensivo**: `pre-s133-cableado-area`.
**Docs nuevos**: `docs/s133/{SUSTRATO_AREA_GEOLOCALIZADA,B22_EVIDENCIA,C2_NORMALIZADO_INNER_RADIUS}.md`.
**Código nuevo**: `pipeline/scan_geometry.py::resolve_viirs_pixel_areas`.
**Perfiles A/B**: `_s133_b22_{control,enabled}`, `_s133_area_{control,geoloc,corona}`.
**Workflows**: `reproc-s133-b22-ab.yml`, `reproc-s133-area-ab.yml`.
**Tests nuevos**: `test_area_geolocalizada_cableada_s133.py` (9), más el endurecimiento de
`test_nadir_fixed_vrp_integration_s103.py` y `test_cluster_corona_magnitude.py`.
