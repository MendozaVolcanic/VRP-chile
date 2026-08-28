# Bloque de arranque S125

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S124, que cerró con un frente refutado y una
hipótesis viva.

Antes de proponer nada, leé en este orden:
  1. docs/S124_CIERRE.md               (estado completo: probado / refutado / pendiente)
  2. docs/superpowers/plans/2026-08-28-plan-s125-brecha-de-magnitud.md
  3. docs/MIROVA_DIVERGENCES.md        secciones D14 a D17 (al final)

Contexto en una línea: el A/B de 4 brazos de F70 REFUTÓ que la grilla UTM
explique nuestro sub-reporte de magnitud. Queda D17 como única hipótesis viva
—nuestra grilla se centró en volcano["lat"/"lon"] y MIROVA centra en
mirova_center, con 6 de 11 volcanes desalineados más de media celda— y queda el
replanteo de prioridad: los brazos mueven 0,11 cuando el hueco es 0,53.

Tres cosas antes de tocar nada:

a) Al final de S124 despaché 3 auditorías en paralelo (afirmaciones de S124 /
   código huérfano no cableado / reglas A históricas verificables). Si sus
   resultados quedaron sin revisar, revisalos PRIMERO: pueden invalidar algo de
   lo que doy por cerrado.

b) Regla de la sesión, pedida por Nicolás: todo debe estar probado. Si una
   afirmación no tiene script reproducible detrás, decilo o volvé a hacerla.
   Los seis patrones de error de S124 están en la memoria
   (feedback_s124_verificar_antes_de_concluir): mediana ≠ efecto, nivel del
   YAML, pasadas comunes, y el reproceso que cierra en verde sin tocar nada.

c) Antes de lanzar cualquier A/B, verificá que el flag realmente llegue:
       VRP_PROFILE=<perfil> python -c "import pipeline.profile as p; print(p.<FLAG>)"
   En S124 un flag leído del nivel equivocado del YAML casi deja 22 jobs en nulo
   sin ningún síntoma.

Arrancá por la tarea 8.1 del cierre: regenerar las figuras de Nevados de Chillán
(serie + mapa) con los datos v2 ya reprocesados y las mejoras de visualización
anotadas. Es tarea explícita de Nicolás. Después seguimos con el brazo D.
```

---

## Estado al cerrar S124

**Repo**: limpio, suite en **906 tests verdes**, todo pusheado a `main`.

**Flags operacionales** (verificados al cierre):

| flag | valor |
|---|---|
| `ENABLE_UTM_REGRID` | `False` (F70 refutada, no se promovió) |
| `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS` | `True` |
| `ENABLE_LOCAL_KERNEL_BG` | `True` (pero aplica solo en los 5 de `volcanoes.yaml`) |
| `MIN_VRP_MW_VIIRS375` | `0.02` |

**Datos disponibles**: `mirova_equivalent` (45) · `_f70_a` (11) · `_f70_b` (11) ·
`_s124_kernelbg_ab` (6) · `experimental_ndc_focus` (1, v2 verificado).

**Nada corriendo en CI.** Los tres runs de la noche cerraron verdes.

---

## Las tres tareas de S125, en orden

### 1. Figuras de Chillán (pedido explícito)

Regenerar serie y mapa con los datos v2 **y** las mejoras anotadas:

- El panel de observabilidad usa σ del fondo, que es un **proxy**: una nube
  estratiforme pareja y el pipeline ciego se parecen. Anotarlo como limitación
  en la figura, o reemplazarlo por `CLDMSK_L2_VIIRS` (verificada disponible con
  versión NRT).
- El mapa dibuja la grilla de MIROVA desde sus GeoTIFF (reproyección lat/lon).
  Con `get_grid_center()` cableado se podría marcar la celda de referencia.
- Revisar que las etiquetas queden coherentes tras cambiar datos — en S124
  quedaron **tres veces** textos que decían «1 km» con radio de 500 m.
- **Correr el audit adversarial de figuras antes de darlas por buenas.** La vez
  anterior encontró 9 problemas, 3 graves (entre ellos una conclusión mía que
  era espuria).

### 2. Brazo D — la hipótesis viva (D17)

- Cablear `geo_utils.get_grid_center()` en `run_pipeline.py` tras un flag nuevo,
  con test que falle si se desconecta (patrón A63).
- Perfiles `_f70_d.yaml` + `_f70_control_4m.yaml` (el workflow rehúsa correr
  contra `mirova_equivalent`, hace falta un clon con `data_subdir` aislado).
- **Criterio pre-registrado ANTES de correr**, con el control interno que al
  brazo B le faltó: los de offset chico (Lastarria 115 m, Copahue 140 m,
  Llaima 142 m) **no deben cambiar**. Jueces: Tupungatito y Planchón-Peteroa.
- Ventana **4 meses** (2026-04-25..08-24): la muestra pasa de 178 a **432**
  noches-alerta. Los dos brazos **en paralelo** (~9 h) — la concurrencia por
  perfil ya lo permite.
- Veredicto con **IC bootstrap que no se solapen**.

### 3. El 80 % del hueco (sin CI, en paralelo con la 2)

- Descomponer la brecha por régimen (`n_anomalous_pixels`) en los 4
  sub-reportadores.
- Cruce **pixel-level contra el TIF de MIROVA** en noches donde ambos detectan.
- **Auditoría file:line de la cadena de MAGNITUD** contra Coppola Eq. 6-8 — la
  detección se auditó así en S114, la magnitud **nunca**. Principal sospecha.

---

## Herramientas nuevas de S124 (usarlas)

| script | para qué |
|---|---|
| `experiments/_s124_ndc_focus/05_verificar_reproceso.py` | **tras TODO reproceso** sobre subdir con data previa; sale 1 si hay meses sin reprocesar |
| `experiments/_s124_f70/03_leer_brazo.py` | lectura apareada de un brazo vs control |
| `experiments/_s124_f70/04_tabla_brazos.py` | tabla de brazos vs MIROVA |
| `experiments/_s124_f70/05_poder_estadistico.py` | IC bootstrap — **antes de afirmar diferencias** |
| `experiments/_s124_cuantizacion/02_origen_grilla_por_volcan.py` | centros de grilla desde GeoTIFF |

## No reabrir sin evidencia nueva (anti-A8)

D16 (la grilla UTM no explica el sub-reporte) · el halo de MIROVA (Npix mediano
1) · atribución de cluster · second-run · piso VRP · fondo del anillo solo · la
ceguera como causa de pérdida de recall (2 % vs 23 % base).
