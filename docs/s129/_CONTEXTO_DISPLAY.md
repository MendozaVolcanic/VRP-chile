# Contexto común para las auditorías de visualización (S129)

## Qué es este sistema

**VRP Chile** — clon literal del sistema MIROVA para 11 volcanes chilenos Tier A. Mide
**potencia radiativa volcánica (VRP, en MW)** desde satélite, de noche, con tres sensores.
El usuario es **Nicolás, geólogo de SERNAGEOMIN**, y **el dashboard es el entregable
final**: una auditoría en stdout no cuenta como resultado hasta que es visible ahí.

## Las cuatro vistas

| archivo | qué es |
|---|---|
| `frontend/index.html` | dashboard principal — tarjetas, mapa Leaflet, gráficos Chart.js, tabla |
| `frontend/diario.html` | tendencia de 90 días por volcán |
| `frontend/mosaico.html` | vista general 48 h / 30 d de los once |
| `frontend/comparacion.html` | ⚠️ **PREVIEW deliberado.** Se rotula a sí misma «PREVIEW S115 · no es el dashboard live» y **no usa `mirovaEqVrp` a propósito** (0 usos contra 25/8/8). **No es un olvido — no propongas «arreglarlo».** Verificado S127. |

**Regla del proyecto**: un cambio de display se replica en las **tres vistas live**
(`index`, `diario`, `mosaico`), y **cada una tiene su propia copia de los helpers** — no
hay módulo compartido. Eso hace que una vista pueda quedar atrás sin que nadie lo note.

## Los tres sensores no son intercambiables

- **VIIRS I-band 375 m** — el más sensible, ve anomalías sub-MW, domina el volumen.
- **VIIRS M-band 750 m** — resolución intermedia.
- **MODIS 1 km** — el píxel grande diluye el foco sub-píxel. A esa resolución el foco
  débil real y el gradiente topográfico **son indistinguibles** (regla A82). Y el ground
  truth de MIROVA para MODIS **sólo existe en Láscar**: de 96 alertas MODIS de
  referencia, 88 son de Láscar y seis volcanes tienen cero. Cualquier lectura MODIS
  fuera de Láscar es **indefinida**, no «débil».

## Trampas conocidas que ya costaron sesiones

- **A10**: `record.vrp_mw` es la suma de toda la escena; `primary_cluster.vrp_mw` es el
  clúster principal. **Son cosas distintas** y confundirlas ocultó problemas reales.
- **A46**: `final_hotspot_*` (el punto que dibuja el mapa) y `primary_cluster.centroid`
  (de donde sale la magnitud) son **dos representaciones del mismo objeto** y pueden
  discrepar. Ya produjo un bug que hizo invisibles ~400 records durante meses.
- **A89**: buscar un identificador y no encontrarlo **no da error, da cero**, y el cero se
  lee como ausencia. Antes de escribir «esto no existe / no se usa», trazá **cómo lo lee
  el código**, no cómo se llama donde está definido.
- **«Declarado ≠ efectivo»**: el comentario de `index.html:809-811` dice que las
  detecciones lejanas siguen visibles en el mapa. **Es falso desde S26 B**, que las filtra
  en la línea 2539. Asumí que cualquier comentario puede estar desactualizado y verificá
  contra el código.

## Hallazgos de S129 que ya están medidos (no re-descubrir)

- El mapa dibuja `final_hotspot_lat/lon` (`index.html:2220-2221`).
- **El 57-78 % de las detecciones VIIRS375 tienen `final_hotspot_source = "test1_roi"`**,
  que hereda la coordenada exacta del cráter — el Test 1 es una integral sobre el ROI y
  no tiene posición propia. Por eso en Llaima 673 puntos ocupan 138 posiciones.
- **MODIS aporta ~450 puntos por volcán a 15-25 km de mediana, con 0 % de confirmación
  de MIROVA** en diez de once. El toggle por defecto los filtra como `far`, **salvo en
  PCC**, cuyo `inner_radius_km = 20` los reclasifica como `summit` y los pinta de rojo.
- `primary_cluster.geo_class === "extension"` tiene tratamiento visual propio desde S88
  (`index.html:2532`) y **nunca se pobló**: en PCC, 1.054 de 1.062 records dicen `summit`.
- **La fórmula depende del sensor**: `mirovaEqVrpCore` (`index.html:1082`) aplica el
  Núcleo F5' **sólo a VIIRS I-band**; MODIS y VIIRS 750 usan `pc.vrp_mw` crudo.
- La `sensor-legend` **ya es un filtro clickeable** que propaga a cinco paneles
  (`index.html:3018-3028`), pero no se lee como control.
- `index` muestra la **última** detección de 48 h; `mosaico` el **máximo**.
- Los JSON completos por volcán son de **19-32 MB** (255 MB los once), no los 13-17 que
  dice el comentario de `build_recent_json.py:6` desde S120.

## Reglas de tu informe

- **Español de Chile.** Nada de voseo rioplatense: «puedes», «mira», «fíjate», «revisa».
- **Citá `archivo:línea`** en toda afirmación sobre el código.
- **A48**: verificá vos mismo con un `grep`/`sed` propio cualquier conclusión de alto
  impacto, y decí con qué la verificaste.
- **NO implementes nada.** Esto es auditoría; la decisión de diseño es de Nicolás.
- **Read-only sobre todo el repo salvo tu propio archivo** en `docs/s129/`.
- Distinguí siempre **lo que medís** de **lo que inferís**. Si algo no se puede medir con
  lo que hay, decilo — un negativo bien establecido vale.
