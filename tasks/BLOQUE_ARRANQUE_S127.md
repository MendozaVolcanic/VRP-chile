# Bloque de arranque S127

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S126. Esa sesión encontró la causa raíz común de casi
todo el frente de magnitud, cerró tres divergencias, y dejó UN experimento sin
concluir por dos bugs de cableado míos.

Leé en este orden:
  1. docs/S126_COSTO_FILTRO_CONTEXTUAL.md      (la causa raíz + el artefacto vivo)
  2. docs/S126_LASCAR_ES_UN_PIXEL.md           (qué le falta a Láscar, medido 2 veces)
  3. docs/superpowers/plans/2026-08-30-auditoria-s127.md   (el plan de auditoría)
  4. tasks/BLOQUE_ARRANQUE_S127.md             (las tareas, en orden)

═══════════════════════════════════════════════════════════════════════════
EL HALLAZGO CENTRAL — el fondo autorreferente
═══════════════════════════════════════════════════════════════════════════

`TEST1_ROI_KM = 3.0` y `TEST1_INTERMEDIATE_BG_RING_KM = (1.5, 3.0)`: el anillo
que hace de fondo es el **75 % del área del mismo disco que se mide**. En
process_viirs.py:1729 cada píxel se compara contra la media de sus propios tres
cuartos exteriores y el clip a cero se queda con la mitad de arriba. Eso fabrica
una VRP que crece con la CANTIDAD de píxeles, no con la energía del volcán.

Tiene CUATRO confirmaciones independientes, dos de ellas sobre la imagen propia
de MIROVA:
  1. la geometría del código (75 % del área);
  2. los 24.235 píxeles que destapa el brazo E se reparten como el ÁREA de cada
     corona (obs/esp 0,71 · 0,74 · 0,75 · 0,96 · 1,10 · 1,16), con el cráter
     SUB-representado y rumbo uniforme — es terreno, no foco;
  3. σ del anillo > 1,88 K: ni el pico REAL de Láscar (+5,65 K) cruza 3σ,
     medido sobre el campo I04 de MIROVA;
  4. el 37 % de lo que la cerca del frontend apaga tiene esa misma firma.

TODO lo demás cuelga de acá.

═══════════════════════════════════════════════════════════════════════════
TAREA 1 — terminar el A/B de la corona (quedó INCONCLUSO 2 veces)
═══════════════════════════════════════════════════════════════════════════

NO es "no adoptar": es que el experimento nunca llegó a medir la corona. Dos
bugs de cableado míos, encadenados:

  (a) La cablée sólo en el bloque Test 1 → de las 80 noches que se comparan
      contra MIROVA, 77 vienen del path CONTEXTUAL. MODIS la tiene justamente
      ahí (process_modis.py:1049); repliqué el bloque equivocado.
      ARREGLADO en #543 (guard estructural incluido).

  (b) Con (a) arreglado, la corona corre en 1.179 records pero sólo cambia 15.
      Diagnóstico sin ambigüedad:
          los que NO cambiaron -> single_pixel_mode: {True: 1157}
          los que SÍ cambiaron -> single_pixel_mode: {False: 15}
      `apply_single_pixel_mode` corre DESPUÉS del recompute y recibe los VRP por
      píxel calculados con el fondo VIEJO (`vrp_per_pixel_2d`). Para clústeres
      sub-MW de ≤3 px reemplaza el valor y descarta la corona.
      SIN ARREGLAR.

FIX: recomputar los VRP por píxel con el fondo de la corona antes de pasarlos a
`apply_single_pixel_mode`, o saltear el modo cuando la corona aplicó. Toca
`pipeline/process_viirs.py` → ciclo A45 (el tag `pre-s126-corona-viirs` ya está
puesto; pedir confirmación a Nicolás igual).

⚠️ El mismo orden existe en `process_modis.py` (corona → focal → cap → dict →
single_pixel_mode), así que el defecto está LATENTE ahí; no se nota porque su
flag de corona está OFF. Arreglar los dos.

Después: relanzar `_s126_corona_on` y `_s126_corona_ctxoff` (el 4º brazo del 2×2,
perfil ya creado y verificado). El control `_s126_corona_off` YA está en disco y
no hay que recomputarlo. El veredicto está pre-escrito:
`experiments/_s126_corona/01_veredicto.py` — se corre y se lee, los 7 criterios
ya están codificados.

⚠️ El job `merge` se cancela cuando dos A/B terminan juntos (grupo `push-main`).
Pasó en S125 y volvió a pasar en S126. NO se pierde el cómputo: recuperarlo con
`gh run download <id>` + el loop de `merge_chunk_stores.py --ventanas` (receta
probada dos veces). Considerar arreglar el workflow ANTES de relanzar.

═══════════════════════════════════════════════════════════════════════════
TAREA 2 — la auditoría (plan completo ya escrito)
═══════════════════════════════════════════════════════════════════════════

docs/superpowers/plans/2026-08-30-auditoria-s127.md, dos fases, 9 tareas.

NO es la auditoría general de siempre: hubo TRES en cuatro sesiones (S123, S124,
S125), repetirla es anti-A8. Lo que se barre es un eje que ninguna cubrió —
"lo declarado no coincide con lo efectivo"— del que S126 encontró DOCE
instancias sin buscarlas, ocho persiguiendo otra cosa.

Fase 1: cuatro barridos mecanizados, cada uno cerrado con un guard.
Fase 2: A51 acotada a lo no cubierto — D17/geometría, matriz sensor×tratamiento,
        higiene de experiments/.

═══════════════════════════════════════════════════════════════════════════
DECISIONES QUE ESPERAN A NICOLÁS
═══════════════════════════════════════════════════════════════════════════

  1. Máscara de nube: sostener el apagado (recomendado, A/B hecho) o revertir y
     re-encender formalmente con el resultado en la mano (A45).
  2. Piso VRP: quitarlo (recomendado — hoy es un no-op que además miente) y NO
     aplicarlo a pc.vrp_mw, porque cortaría el cráter de Láscar e Isluga.
  3. Docstring de `single_pixel_mode`: dice "Volcanes NO afectados … Lascar" y
     está activo en 110/110 de sus records.
  4. Claves duplicadas en `mirova_equivalent.yaml` (A45).

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA
═══════════════════════════════════════════════════════════════════════════

  · ESTRATIFICAR POR VOLCÁN, no sólo por sensor. Una mediana agrupada invirtió
    el veredicto del brazo E en S125 (PP 0,957 → 6,636 escondido en el promedio).
  · Verificar el EFECTO sobre los datos, no confiar en que el cambio hizo lo que
    dice. Tres veces en S126 un cambio mío se aplicó y algo aguas abajo lo anuló.
  · Un par por NOCHE, máximo de ambos lados. Comparar cada pasada contra el
    máximo de MIROVA infla el objetivo 2,5×.
  · Verificar flags leyendo `pipeline.profile`, NUNCA el YAML — y ojo con las
    claves duplicadas: YAML se queda con la última en silencio.
  · Los helpers comunes están en `experiments/_s126_lib.py` (intersección de
    pasadas, ground truth CONS∪OCR con alias completo, descarte de diurnas A76,
    IC bootstrap). Reusarlo en vez de reescribir la metodología.
  · El archivo de TIFs de MIROVA (`mirova-tif-archive`) es la vía de evidencia
    EXÓGENA. El checkout local está atrasado y pesa 12 GB con el disco al 99 % —
    bajar por API sólo lo necesario (21 KB por TIF).
```

---

## Estado al cerrar S126

**Suite**: 986 tests verdes. **NRT**: sano (commits automáticos cada 2 h).
**Operacional intacto**: `corona375=False · ctx_filter=True · cloud_mask=0.0 · piso=0.02`.

**PRs mergeados**: #536, #537, #538, #539, #540, #541, #542, #543.
**PR abierto**: #544 (validez del control + re-verificación de Láscar). Rama con
trabajo sin PR: `claude/s126-d13` (D13 + plan de auditoría + recuperación del brazo).

**Tags defensivos**: `pre-s126-corona-viirs`.

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| **El fondo del Test 1 es autorreferente** | el anillo es el 75 % del área del ROI; 4 confirmaciones independientes |
| El brazo E **no se adopta** | desagregado por volcán: PP 0,957 → 6,636; en banda 3/4 → 2/4 |
| El veredicto de S125 estaba **invertido por agrupar** | la mediana agrupada escondía que un volcán se disparaba ×6,9 |
| A Láscar **le falta el segundo píxel** | fondo necesario 238 K vs 273 K disponible (imposible 100 %) **y** 2 px contados en la imagen de MIROVA contra 1 nuestro |
| **VIIRS 375 no ve el lava lake de Villarrica** | contraste al cráter −0,09 K nuestro y **−0,73 K en el campo de MIROVA**, con Láscar de control positivo (+1,34 K) |
| El punto que publicamos a 2,8 km **no es un rasgo** | +0,05 K en el campo de MIROVA: es el argmax de un campo plano |
| La máscara de nube: **sostener el apagado** | recupera 176 de 181 noches ciegas; magnitud mejora; fondo baja sólo 0,5-2 K |
| **D13 deja de ser palanca** | 37 % de lo que apaga es el artefacto, 1,5 % corroborado por MIROVA |
| `single_pixel_mode`: **dejar, corregir docstring** | quitarlo saca a Chaitén de banda (7/9 → 6/9); en Tupungatito ya no toca ninguna noche |
| El piso VRP **es un no-op** | 100 % de los records "suprimidos" siguen con pc.vrp>0; MODIS 0 de 2.906 |

### Lo REFUTADO (no reabrir sin evidencia nueva)

- **El halo geotermal no explica Láscar**: predije que su anillo estaría más
  caliente; está más **frío** (−2,47 K), igual que los nevados.
- **`audit_metrics.mirova_eq_vrp()` no está muerta ni divergida**: la importan 3
  dirs de `experiments/`, y 0 desacuerdos sobre 60.315 records contra las 3
  copias del frontend.
- **El anillo intermedio no hace nada solo** (F ≡ control byte a byte); sólo
  aparece en interacción con el filtro contextual apagado.

### Bugs de infra: arreglados y pendientes

**Arreglados en S126**: canal OCR partido (844 → 903 fechas ALERTA, con 2 guards) ·
cap de 50.000 MW faltante en `audit_metrics` (no-op probado sobre 60.315 records) ·
claves duplicadas en perfiles (guard sobre los 51).

**Pendientes**: el job `merge` que se cancela en silencio (pasó 2 veces; receta de
recuperación probada) · `modis_vent_threshold_k` y `modis_vent_vrp_floor_mw`
declarados en `paths:` y muertos, en 31 perfiles · **el disco C está al 99 % con
5,4 GB libres**.

### El patrón que ordena la sesión

Doce instancias de **"lo declarado no coincide con lo efectivo"**, ocho encontradas
persiguiendo otra cosa. Tres de ellas fueron de mi propio trabajo en esta sesión.
Es el eje de la auditoría S127 y la nueva técnica T9 del protocolo. La regla que
lo resume: **una afirmación sobre el estado del sistema necesita un test detrás, o
no es una afirmación — es una intención.**
