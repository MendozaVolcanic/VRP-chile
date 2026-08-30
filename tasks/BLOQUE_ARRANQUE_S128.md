# Bloque de arranque S128

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S127. Esa sesión desbloqueó el A/B de la corona —que
había salido inconcluso dos veces por un bug de cableado— y barrió un eje de
auditoría que ninguna de las tres anteriores había tocado.

Leé en este orden:
  1. docs/AUDIT_S127.md                (los 8 hallazgos, con sus guards)
  2. docs/S126_COSTO_FILTRO_CONTEXTUAL.md   (la causa raíz: el fondo autorreferente)
  3. docs/S126_LASCAR_ES_UN_PIXEL.md   (por qué el 2×2 y no un A/B simple)
  4. tasks/BLOQUE_ARRANQUE_S128.md     (esto)

═══════════════════════════════════════════════════════════════════════════
LO PRIMERO: LEER EL VEREDICTO DEL 2×2 (los datos ya están o casi)
═══════════════════════════════════════════════════════════════════════════

Los dos brazos que faltaban se relanzaron en S127 SOBRE EL CÓDIGO ARREGLADO:

    _s126_corona_on      corona ON  + filtro contextual ON
    _s126_corona_ctxoff  corona ON  + filtro contextual OFF   <- la celda que nadie corrió

El control `_s126_corona_off` YA está en disco y NO se recomputa (ahí la corona
nunca corrió, así que el bug no lo alcanza). El cuarto brazo del 2×2 —corona OFF
+ filtro OFF— es el brazo E de S125, también en disco (`_s125_viirs_e`).

Runs: 33299553238 (on) y 33299555453 (ctxoff), lanzados 2026-08-30 07:35 UTC.

    git pull --ff-only
    ls -d data/_s126_corona_on data/_s126_corona_ctxoff   # ¿llegaron?
    python experiments/_s126_corona/01_veredicto.py

El veredicto está PRE-ESCRITO con los 7 criterios codificados: se corre y se lee,
no se interpreta. NO tocarle los criterios después de ver los números.

Si los directorios no están: el job `merge` de `reproc-chunked` ya NO comparte el
grupo `push-main` (se arregló en #546), así que no debería haberse cancelado. Si
igual falta, recuperar con `gh run download <id>` + el loop de
`scripts/merge_chunk_stores.py --ventanas`.

⚠️ La hipótesis que el 2×2 pone a prueba, para leer el resultado con sentido:
bajo un fondo LOCAL un píxel de terreno tiene vecinos a su misma temperatura, así
que aporta ΔL ≈ 0 aunque se lo incluya. Es decir, la corona volvería seguro
incluir más píxeles — y a Láscar le falta justamente el segundo píxel, mientras
Villarrica y Planchón explotan cuando el filtro se apaga porque los píxeles extra
son terreno. Ninguno de los dos ejes solo resuelve las dos cosas; la combinación
podría. Es hipótesis, no resultado.

⚠️ Y el aviso del pre-registro: la corona SOLA probablemente falle su propio
canario (Láscar cae ~20 %), y eso NO refuta la corona — refuta la corona SIN el
segundo píxel.

═══════════════════════════════════════════════════════════════════════════
LO QUE ESPERA AL VEREDICTO (no antes, a propósito)
═══════════════════════════════════════════════════════════════════════════

  · **Piso VRP**: S126 recomienda quitarlo (hoy es un no-op que además miente) y
    NO aplicarlo a `pc.vrp_mw`, porque cortaría el cráter de Láscar e Isluga.
    Condicionado por escrito a leer antes el A/B de la corona.
  · **Villarrica**: mide a 2,8 km del cráter incluso con actividad confirmada, y
    VIIRS 375 no ve su lava lake (contraste −0,73 K en el campo de MIROVA). Es
    artefacto, no señal → por A72 se arregla en el algoritmo. Si la corona
    funciona, buena parte debería caerse sola.
  · **D12** (FN MODIS): congelada, cierre formal pendiente de Nicolás.

═══════════════════════════════════════════════════════════════════════════
DECISIONES QUE ESPERAN A NICOLÁS
═══════════════════════════════════════════════════════════════════════════

  1. **~112 MB del probe S104** (`experiments/_s104_roi_probe/{anchor_a,anchor_b,
     baseline_mir,local_k*,nti_integral}`) siguen sin trackear. Son RESULTADO —
     respaldan A69— no intermedio. Commitear, dejar, o borrar para recuperar
     disco. ⚠️ Un tag defensivo A38 **no los protege**: para eso tendrían que
     estar en git primero.
  2. **Disco C al 98 %** (15 GB libres). La higiene de S127 dejó de ensuciar
     `git status` pero no liberó espacio — no se borró nada a propósito.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA (las de S126 siguen, más una)
═══════════════════════════════════════════════════════════════════════════

  · **A89 (nueva)**: «no aparece en ningún lado» casi nunca significa que no esté.
    Un `grep` que no encuentra no falla: devuelve CERO, y el cero se lee como
    ausencia. Cinco falsos negativos en S127 por esto, en tres formas — parámetro
    vs clave del YAML, clave heredada por `extends:`, llamada calificada o
    renombrada en el import. **Las cinco veces el error fue de quien auditaba.**
  · Verificar flags leyendo `pipeline.profile`, NUNCA el YAML. Resuelve `extends:`,
    la sección correcta y los duplicados de una sola vez.
  · ESTRATIFICAR POR VOLCÁN, no sólo por sensor (una mediana agrupada invirtió el
    veredicto del brazo E en S125).
  · Un par por NOCHE, máximo de ambos lados.
  · Verificar el EFECTO sobre los datos, no confiar en que el cambio hizo lo que dice.
  · Helpers comunes en `experiments/_s126_lib.py`. Reusarlo.
```

---

## Estado al cerrar S127

**Suite**: 998 tests verdes. **NRT**: sano. **Operacional intacto**:
`corona375=False · corona_modis=False · ctx_filter=True · cloud_mask=0.0 · focal=True`.

**PRs mergeados**: #546 … #555 (diez).
**Tags defensivos**: `pre-s126-corona-viirs` (ya existía) · `pre-s127-wipe-corona-arms`.

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| **La corona se calculaba y se tiraba** | corrió en 1.179 de 1.278 records y sólo movió 15; los 1.164 restantes tenían `single_pixel_mode=True` |
| El invariante que lo demuestra | para un clúster de UN píxel, suma ≡ máximo; que el modo lo mueva sólo puede ser dos fondos distintos |
| **En MODIS era peor y latente** | `cluster_focal_vrp_mw` (ENCENDIDO) reasigna sin condición justo después → anulación del 100 %, sin marca |
| `sum()` de Python 3.12 no es el acumulador viejo | suma compensada de Neumaier, 1 ULP; se agregó `sum_cluster_vrp` naive para poder probar el no-op estricto |
| `single_pixel_mode` «NO afectados» | **falso para los 7**; Láscar 33,9 % es el más afectado, Tupungatito 7,5 % el menos |
| «el kernel nunca corre en producción» | falso: corre en 5 de los 11 Tier A |
| 2 claves bajo `paths:` que el código no lee | 31 de 51 perfiles; limpieza probada no-op sobre los 51 |
| El schema no tiene campos muertos | los 84 campos de producción tienen lector |
| 9 de 13 mecanismos asimétricos entre sensores | matriz nueva; nadie la había hecho |
| **D17 confirmada** | `get_grid_center()` sin llamador, regrid centrado en `volcano_lat/lon`, `ENABLE_UTM_REGRID` OFF |
| El job `merge` que se cancelaba | `group: push-main` a nivel job + GitHub mantiene 1 run pendiente por grupo |

### Guards nuevos

- `test_corona_single_pixel_coherencia_s127` — el invariante del clúster de un píxel,
  la contra-prueba del bug, y el no-op bit a bit sobre 50 escenas con NaN.
- `test_guard_afirmaciones_de_alcance_s127` — prohíbe **declarar** una lista de volcanes
  afectados, permite **citarla** como historia (distingue por contexto).
- `test_guard_claves_fantasma_s127` — genérico: deriva de `profile.py` de qué sección se
  lee cada clave. Incluye un test que verifica que **el guard sigue mirando**, porque un
  guard que pasa por no encontrar nada da confianza falsa.

### Divergencias que cambiaron de estado

- **D14 CERRADA**: se sostiene el apagado de la máscara de nube, ratificado con el A/B en
  la mano. Recupera 176 de 181 noches ciegas. **No cierra el frente del artefacto**: de
  las 286 detecciones que destapó sólo 21 caen en noches que MIROVA confirma, a 2,4-2,7 km.

### Transparencia algorítmica (Res. CPLT N°372)

La cabecera FICHA de `single_pixel_mode.py` declaraba bajo **Limitaciones** que el ajuste
«no aplica a Villarrica». Villarrica tiene 3.025 records con el modo activo y 442
modificados. Era la copia más consecuente de las 14, porque «Limitaciones» es el campo que
un regulador lee para saber qué hace el sistema con un volcán dado. Corregida; ficha
publicable a **v1.4**.

### El patrón que ordena la sesión

**A89**: el cero de una búsqueda se lee como ausencia. Cinco instancias, tres formas, y
las cinco del lado de quien auditaba — dos de ellas con el texto correcto ya escrito en el
repo desde S72. La técnica se equivoca en la misma dirección que el defecto que busca, así
que un hallazgo de la forma «esto está muerto» exige verificación cruzada **antes** de
reportarse, no después.
