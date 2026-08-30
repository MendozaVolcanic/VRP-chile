# Pre-registro del A/B de la corona Eq.6 en VIIRS 375 (S126)

> Fijado **antes** de correr. Cualquier criterio agregado después no cuenta.
> Escrito el 2026-08-29 (hora del servidor, A86). Tag defensivo:
> `pre-s126-corona-viirs`.

## Qué se compara

| brazo | perfil | qué cambia |
|---|---|---|
| control | `_s126_corona_off` | nada — clon exacto del operacional |
| tratamiento | `_s126_corona_on` | `enable_local_cluster_magnitude_viirs375: true` |

Verificado leyendo `pipeline.profile` (nunca el YAML): entre los dos brazos hay
**exactamente 2 diferencias**, el flag y `data_subdir`; y entre el control y
`mirova_equivalent`, **ninguna** fuera de `data_subdir`. El control es válido.

**Ventana**: 2026-06-25 a 2026-08-24, la misma de los brazos de S125, sobre la
**intersección de pasadas** (`datetime_utc` + `sensor`).

**Volcanes**: Villarrica, Planchón-Peteroa, Láscar, Puyehue-Cordón Caulle y
**Nevados de Chillán**. NdC entra como **canario de A79**: el anillo `[1,5–3] km`
se adoptó en S112 porque `[2,4]` perdía el trigger del evento del 16-jun. Aunque
el recompute va post-selección y no debería tocar la detección, hay que
comprobarlo, no suponerlo.

## Por qué el control no puede ser `mirova_equivalent` a secas

Esa data es el acumulado operacional, reprocesado en momentos distintos y con
versiones de código distintas, así que introduce diferencias espurias ajenas al
A/B. En S125 se vio en concreto: MODIS se movía +4,03 con piezas que ni lo tocan.

## Criterios de adopción — estratificados POR VOLCÁN

La lección central de S126 es que **una mediana agrupada invierte el veredicto**:
el "0,600 → 1,043" de S125 escondía que Planchón-Peteroa pasaba de 0,957 a 6,636.
Ningún criterio de acá se evalúa sobre el conjunto.

1. **Volcanes en banda [0,7 – 1,4]**, contados uno por uno en VIIRS 375. Adoptar
   exige **≥ el número del control** y que **ningún volcán que estaba en banda se
   salga**.
2. **Villarrica: la magnitud tiene que BAJAR.** Es el caso donde está probado que
   medimos una fluctuación a 2,74 km del cráter con contraste −4,74 K, y que no
   distingue noche activa de noche quieta. Si su magnitud no baja, la corona no
   está haciendo lo que la hipótesis dice.
3. **Láscar es el canario de falso negativo**: cero detecciones perdidas y su
   magnitud no puede caer más de un **20 %**. Ahí el foco es real —a 0,18 km del
   cráter y +7,8 K sobre el fondo— y la corona debe conservarlo.
4. **NdC 06-16 sigue disparando** (A79). Si se pierde: NO ADOPTAR, sin discusión.
5. **Cero detecciones perdidas** en total sobre la intersección.
6. **Control interno**: MODIS y VIIRS 750 no deben moverse **ni un dígito**. El
   flag no los toca; si se mueven, el A/B está mal montado y el resultado no vale.
7. **`corona_degraded`** se reporta como diagnóstico: en qué fracción de records la
   corona no juntó los 4 píxeles mínimos y hubo que caer al fondo regional. No es
   criterio de adopción, pero si supera ~30 % el resultado mide una mezcla de dos
   métodos y hay que decirlo.

## Qué NO decide

- **La mediana agrupada** de los 5 volcanes. Se reporta; no decide.
- **Las noches diurnas** de MIROVA: se descartan (A76, artefacto de reflexión solar,
  y nuestro pipeline es night-only).
- **El ratio contra MIROVA en volcanes con n < 3 pares**: se reporta con su n, no
  se usa para contar banda.

## Antes de leer cualquier número

```bash
python experiments/_s124_ndc_focus/05_verificar_reproceso.py data/_s126_corona_on/<Vol>.json
```

Un reproceso puede cerrar **en verde sin haber tocado nada** (bug de merge de S124),
y el job `merge` puede quedar **cancelado en silencio** por el grupo de concurrencia
`push-main` cuando dos A/B terminan juntos (S125). Si el run figura `cancelled` pero
sus trozos están verdes, el cómputo está hecho: recuperarlo con `gh run download <id>`
+ `merge_chunk_stores.py --ventanas`, sin re-computar.

## Si el veredicto es NO ADOPTAR

El flag queda en `False` y no se toca `mirova_equivalent`. El hallazgo del fondo
autorreferente sigue en pie —está probado independientemente del A/B— y habría que
buscar otra forma de sacarle el rol de fondo al anillo, por ejemplo moviéndolo
fuera del ROI en vez de reemplazarlo por la corona.

---

## Verificación de validez del control (hecha con el control ya en disco)

El brazo control **no** reproduce la data operacional de la misma ventana, y eso está
bien — es justamente la razón por la que el control tiene que ser un clon reprocesado.
Verificado el porqué, para descartar que fuera ruido:

| volcán | grupo | n | mismo `n_bg` | Δ `n_bg` (control − operacional) |
|---|---|---|---|---|
| Villarrica | VRP idéntico | 592 | 74 % | 0 |
| | VRP difiere | 90 | **0 %** | **+10.984** |
| Láscar | VRP idéntico | 349 | 94 % | 0 |
| | VRP difiere | 205 | **2 %** | **+4.514** |
| Nevados de Chillán | VRP idéntico | 462 | 90 % | 0 |
| | VRP difiere | 204 | **1 %** | **+7.520** |

Los records que difieren son **exactamente** aquellos donde el control usó miles de
píxeles de fondo más: son las pasadas en que la máscara de nube filtraba en la data
operacional (producida **antes** del PR #535) y ya no filtra en el reproceso de hoy.

**Consecuencia para este A/B**: los dos brazos de la corona se reprocesaron ahora, con
el mismo código y la misma máscara, difiriendo sólo en el flag. Su comparación es
limpia. Comparar cualquiera de los dos contra `mirova_equivalent` estaría contaminado
por el cambio de máscara — que es precisamente el error que la regla del control-clon
previene, acá cuantificado.
