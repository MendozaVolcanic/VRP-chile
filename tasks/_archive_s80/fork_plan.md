# Fork Plan — Mainline operacional + Laboratorio experimental

**Fecha**: 2026-04-09 (sesión 9, post-F1 cleanup)
**Contexto**: Decisión estratégica de separar el producto VRP-Chile en dos
modos: un "MIROVA-equivalent" operacional y estable para uso SERNAGEOMIN, y
un laboratorio experimental donde probar thresholds más bajos, detección
sub-pixel, nuevos sensores, etc. Motivación: ver discusión de sesión 9
después de que el mapa de Puyehue siguiera mostrando enjambre de 432 FPs
vent-path post-F1 que no se podía limpiar sin arriesgar falsos negativos.

## El problema que esto resuelve

El pipeline actual tiene tres objetivos mezclados que son contradictorios
entre sí:

1. **Producto operacional**: reemplazar `mirovaweb.it` para el uso diario
   del geólogo de turno. Requiere: bajo FP, predecible, visualmente limpio,
   consistente con lo que MIROVA reportaría.
2. **Laboratorio experimental**: detectar señales débiles sub-pixel, probar
   sensores nuevos, explorar detección por cluster, etc. Requiere: bajo FN,
   permisivo, tolera FPs para no cegarse a nada nuevo.
3. **Monitoreo independiente**: capturar cosas que MIROVA pierde.
   Requiere: un lugar donde las detecciones nuevas son visibles antes de
   ser promocionadas al operacional.

Los tres no pueden convivir en un solo set de thresholds. F2 (tightening
del vent_path) beneficia al objetivo 1 y perjudica a los objetivos 2 y 3.

## Principio físico detrás de la decisión

**Un pixel VIIRS de 375 m sobre un cráter volcánico es una mezcla**: roca
caliente del conducto, hielo, nieve vieja, fumarolas, atmósfera, radiación
solar reflejada al atardecer, calor residual del terreno. El brillo total
que mide el sensor es el promedio ponderado de todo eso dentro del pixel.

Cuando un volcán tiene un hotspot fuerte (lava fresca, lago de lava activo),
domina la mezcla y el pixel salta claramente sobre el background. Cuando el
hotspot es débil (fumarola de unas pocas decenas de watts por metro cuadrado),
el pixel apenas se levanta 1-3 grados sobre el background — y a esa escala
cualquier cosa puede producir una fluctuación similar: nube cirrus, borde
de sombra, variación estacional de humedad del suelo.

**MIROVA resolvió esta ambigüedad hace 10 años**: aceptó no ver señales más
débiles que ~0.05 MW a cambio de confiabilidad operacional. Ese es el
trade-off que mantiene a MIROVA siendo usable: prefiere perder una fumarola
débil que llenar el mapa de artefactos. El producto que salió de esa
decisión es lo que el geólogo chileno lleva años leyendo.

Nosotros, al intentar *mejorar* ese trade-off en un solo pipeline, rompemos
la consistencia con la intuición acumulada del usuario. El fork plan
acepta que el trade-off correcto depende del objetivo, y separa los dos.

## Estructura propuesta

### Mainline — `profile: mirova_equivalent` (rama `main`, dashboard principal)

**Lo que hace**: reproduce MIROVA con los sensores MIROVA y los umbrales
MIROVA. Nada experimental. Si MIROVA no lo detecta, nosotros tampoco.

**Sensores**:
- **VIIRS375 (VNP02IMG / VJ102IMG)** — primario en todos los volcanes
  (MIROVA usa este en el 66% de sus detecciones chilenas).
- **VIIRS-M 750m (VNP02MOD / VJ102MOD)** — secundario, solo para señales
  que VIIRS375 no alcanza (MIROVA lo usa en 21% de detecciones, casi todas
  Lascar / Villarrica / PCC en señales específicas).
- **MODIS (MOD021KM / MYD021KM)** — **solo en Lascar**. En los otros 10
  volcanes MIROVA reporta cero detecciones MODIS, es decir MODIS a 1km no
  captura nada real en volcanes chilenos de actividad moderada. Toda
  "detección MODIS" nuestra en los otros volcanes es ruido terrenal por
  diseño de la resolución espacial, no por bug.

**Paths de detección**:
- Eruption-scale path (ROI completo, radius_km=15km por volcán) — **SÍ**.
- Vent-scale path (radio 3-4km del cráter, threshold 1K sobre bg) — **NO**
  en este perfil. Ese path existe para capturar fumarolas sub-pixel que
  MIROVA tampoco ve, así que fuera del operacional.

**Thresholds**:
- Eruption-scale BT floor: `max(5K, 3·σ_bg)` — como está ahora.
- NTI path: `nti > NTI_K1_NIGHT (-0.8)` con BT sanity `t_bg + 3K` — como F1.
- Lógica: OR entre BT y NTI paths, como F1.

**Métrica de éxito**: ratio mediano 0.8-1.2 contra MIROVA, recall ≥ 0.85,
precision ≥ 0.5 (esperable con sensores limitados y datos MIROVA como
ground truth).

**Data**: `data/mirova_equivalent/<volcano>.json`

**Dashboard**: `https://mendozavolcanic.github.io/VRP-chile/` (el actual,
sin cambio de URL). Muestra solo el perfil operacional por default.

### Laboratorio — `profile: experimental` (rama `main`, subdirectorio separado)

**Lo que hace**: lo mismo que haría un paper de investigación. Permisivo,
experimental, diseñado para descubrir cosas antes que MIROVA, no para
tranquilizar al volcanólogo de turno.

**Sensores**: todos los del operacional **más**:
- MODIS en todos los volcanes (para medir cuánto ruido contribuye y si
  hay eventos fuertes que justifiquen agregarlo al operacional en el
  futuro).
- Placeholder para futuros: Sentinel-2 SWIR, GOES-16 ABI, Landsat 8/9.

**Paths de detección**:
- Eruption-scale — igual que operacional.
- **Vent-scale path — ACTIVO** con threshold permisivo (t_bg + 1K).
- En el futuro: cluster-based detection, integración multi-pasada, etc.

**Thresholds**: más bajos, parametrizables, con capacidad de sweep en
experimentos.

**Métrica de éxito**: recall contra MIROVA + capacidad de detectar
señales débiles que MIROVA pierde (documentadas caso por caso).

**Data**: `data/experimental/<volcano>.json`

**Dashboard**: `https://mendozavolcanic.github.io/VRP-chile/experimental/`
O un toggle en el dashboard principal: "Modo operacional / Modo laboratorio".

### Código compartido

**NO vamos a duplicar el pipeline**. El código de `pipeline/` es el mismo,
se parametriza con un perfil cargado desde YAML al arranque.

```
pipeline/
  profiles/
    mirova_equivalent.yaml   # thresholds + sensors + paths
    experimental.yaml
  fetch.py
  process_viirs.py           # lee constantes del perfil activo
  process_viirs_mod.py
  process_modis.py
  store.py
  ...
```

`run_pipeline.py` acepta `--profile mirova_equivalent` (default) o
`--profile experimental`. El profile elegido define qué sensores correr,
qué paths activar, y qué valores usar para `ANOMALY_THRESHOLD_K`,
`VENT_THRESHOLD_K`, `NTI_K1_NIGHT`, etc.

## Workflows de GitHub Actions

Dos archivos en `.github/workflows/`:

1. **`nrt_mirova.yml`** — cron 6h, profile=mirova_equivalent, publica al
   dashboard principal.
2. **`nrt_experimental.yml`** — cron 6h desfasado (por ejemplo cron 3h),
   profile=experimental, publica al dashboard experimental.

Ambos usan los mismos secrets (EARTHDATA_USERNAME/PASSWORD) y el mismo
runner ubuntu-latest. Siguen siendo gratis para repo público (minutos
Actions ilimitados en repos públicos).

## Frontend

Opción A (más limpia): dos páginas separadas. `frontend/index.html` lee
de `data/mirova_equivalent/`, `frontend/experimental/index.html` lee de
`data/experimental/`. Link cruzado en el header.

Opción B: una sola página con un toggle de perfil en la UI que cambia el
path de fetch. Más conveniente para el usuario pero requiere más trabajo
JS. **Recomendación**: empezar con A por simplicidad, migrar a B cuando
el laboratorio esté maduro.

## Tamaño en GitHub

Cifras actuales:
- `data/` con 11 volcanes con historia: 5.7 MB
- Si duplicamos en dos perfiles: ~11 MB
- Con el experimental esperando más detecciones: ~17 MB worst case
- Total repo: ~25-30 MB
- Límite suave de GitHub: 1 GB
- Límite de GitHub Pages: 1 GB
- Minutos de Actions en repo público: ilimitados

**Conclusión**: no hay constraint de almacenamiento. Podemos crecer 30×
sin tocar los límites.

## Migración (orden de pasos)

1. Cerrar el cleanup actual: audit de los 4 volcanes restantes con F1,
   commit de pre-snapshots y post-audits, documentar estado.
2. Crear `pipeline/profiles/mirova_equivalent.yaml` y `experimental.yaml`
   con la configuración actual extraída.
3. Modificar `run_pipeline.py` para leer el perfil activo.
4. Modificar `process_viirs.py`, `process_viirs_mod.py`, `process_modis.py`
   para aceptar constantes del perfil en vez de hardcodearlas.
5. Mover la data actual a `data/mirova_equivalent/` (con `git mv` para
   preservar historia).
6. Generar `data/experimental/` vacío. Primer run con profile=experimental
   lo pobla.
7. Desactivar el `vent_path` en `mirova_equivalent.yaml` y validar que el
   operacional queda limpio visualmente.
8. Duplicar el workflow de GitHub Actions.
9. Duplicar el frontend (opción A).
10. Actualizar README, memoria, y STATUS para reflejar la nueva arquitectura.

## Qué NO hace este fork

- **No hace F2 como estaba planeado** (vent_path tightening). El vent_path
  simplemente no corre en el operacional y corre igual en el experimental.
  F2 deja de ser necesario.
- **No resuelve el problema Villarrica** (señales sub-pixel). Villarrica
  queda sin calibrar en el operacional (Tier C), y en el experimental se
  explora con thresholds más bajos.
- **No toca el ROOT_CAUSE_S9 RF5** (ratio bias en low-activity). Esa es
  una cosa real a investigar después de que el fork esté en pie.
- **No reemplaza el audit estricto**. `experiments/11_strict_audit.py`
  sigue siendo el juez: corre contra ambos perfiles y emite métricas
  separadas.

## Riesgos y mitigaciones

**Riesgo 1**: duplicación de código accidental si el perfil no está bien
parametrizado. Mitigación: tests que corren ambos perfiles sobre un
granule de referencia y comparan outputs — cualquier diferencia sin
motivo explícito rompe el test.

**Riesgo 2**: los dos dashboards se desincronizan (uno queda mostrando
data vieja). Mitigación: los dos workflows corren en el mismo cron
y cada uno reporta última actualización en el header del dashboard.

**Riesgo 3**: el usuario se confunde entre los dos modos y cita data
experimental como operacional. Mitigación: banner visible en el dashboard
experimental diciendo "MODO LABORATORIO - NO OPERACIONAL" + el link
cruzado.

**Riesgo 4**: las 3 horas de trabajo de migración no valen la pena si
F2 con umbral 3K hubiera sido suficiente. Contra-argumento: F2 no resuelve
el objetivo 3 (detección independiente) ni el 2 (laboratorio), y en el
tiempo que tardás en calibrar F2 podés tener el fork funcionando. Además
el fork es reversible (un git revert) mientras que F2 calibrado malo
es invisible y costoso.

## Decisión pendiente de Nicolás

1. **¿Arrancamos la migración ya mismo o esperamos a terminar algún otro
   pendiente?**
2. **¿Opción A (dos páginas) u opción B (toggle en una)?**
3. **¿Lascar MODIS queda también en experimental, o solo en operacional?**
   (MIROVA lo usa, así que podría quedar solo en mainline. Mi recomendación:
   en ambos, para poder comparar.)
4. **¿El perfil experimental corre con el mismo cron 6h o con uno más
   espaciado (12h, diario)?** Más espaciado = menos ruido en el dashboard
   experimental pero también menos data para jugar.
