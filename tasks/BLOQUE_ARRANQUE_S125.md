# Bloque de arranque S125

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S124. Esa sesión terminó con tres auditorías
adversariales que encontraron que MI PROPIO veredicto estaba mal en dos puntos.
Eso cambia cómo arrancamos: primero auditamos, después construimos.

Leé en este orden:
  1. docs/PROTOCOLO_AUDITORIA_PROFUNDA.md   (las 8 técnicas y las 4 fases)
  2. docs/S124_CIERRE.md                    (§3-bis: qué tumbaron las auditorías)
  3. tasks/BLOQUE_ARRANQUE_S125.md          (las tareas, en orden)

CONTEXTO EN TRES LÍNEAS. El A/B de 4 brazos de F70 dio NO ADOPTAR, y con
PuyehueCordonCaulle —que estaba escondido de la tabla por un alias faltante— el
brazo B además lo saca de banda. D17 (grillas desalineadas) tiene la premisa
probada pero perdió su respaldo: la correlación era r=+0,054 con la variable
correcta, y PCC la contradice. El hueco real sigue sin explicación: los brazos
mueven 0,11 cuando el hueco es 0,53, y eso es un factor 2 de sesgo en la
magnitud que reportamos.

═══════════════════════════════════════════════════════════════════════════
TAREA 0 — AUDITORÍA PROFUNDA DE TODO LO CONSTRUIDO (antes que nada)
═══════════════════════════════════════════════════════════════════════════

Nicolás pidió revisar sistemáticamente TODO lo hecho estos meses, buscando
errores arrastrados. El terreno: 71 reglas A, 32 auditorías previas, 8
divergencias catalogadas, 114 archivos de test, 102 experimentos, 39 perfiles.

El protocolo tiene 8 técnicas VALIDADAS —cada una encontró un error real en
S124— y 4 fases ordenadas por rendimiento. No inventes técnicas nuevas antes de
aplicar ésas; su tasa de acierto ya está medida.

Cómo ejecutarla, en concreto:

  · Despachá subagentes EN PARALELO, uno por eje, con contexto autocontenido
    (sin historial de conversación: el sesgo del autor es lo que se quiere
    evitar). En S124 tres agentes en paralelo encontraron 16 hallazgos, 4 de
    severidad alta.
  · VERIFICÁ vos los hallazgos críticos antes de aceptarlos. En S124 un
    subagente inventó un regex plausible que rompía la convención real del
    proyecto (regla A48). Los subagentes no son fuente de verdad metodológica.
  · Prioridad de la fase 1: las ~12 reglas que dicen "cerrado", "agotado" o
    "no reabrir". Ésas apagan trabajo futuro; si una está mal, cuesta sesiones.
  · Clasificá cada hallazgo como FALSO / OBSOLETO / SIN RESPALDO / CONFIRMADO y
    actuá distinto según la clase (ver la regla de salida del protocolo). No
    borres una conclusión por sonar mal, ni rehagas un experimento cuyo
    resultado ya es reproducible.

Entregable: un doc con los hallazgos clasificados, las correcciones aplicadas
a CLAUDE.md / MISSION.md / MIROVA_DIVERGENCES.md citando evidencia, y la lista
de lo que quedó marcado "sin respaldo, pendiente de prueba".

═══════════════════════════════════════════════════════════════════════════
DESPUÉS de la auditoría, en este orden
═══════════════════════════════════════════════════════════════════════════

  1. Regenerar las figuras de Nevados de Chillán (serie + mapa) con los datos
     v2 y las mejoras anotadas, y correrles el audit adversarial (T7) antes de
     darlas por buenas. Pedido explícito de Nicolás.
  2. Rehacer el veredicto F70 con PCC incluido y con scripts que persistan cada
     número (varios del veredicto S124 eran ad-hoc y hubo que retirarlos).
  3. Decidir con Nicolás si el brazo D vale las ~9 h de CI, sabiendo que su
     respaldo empírico se cayó.
  4. La auditoría file:line de la cadena de MAGNITUD contra Coppola Eq. 6-8 —
     nunca se hizo, y ahí vive el factor 2.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA (pedidas por Nicolás)
═══════════════════════════════════════════════════════════════════════════

  · Todo debe estar probado. Si una afirmación no tiene script reproducible
    detrás, decilo o volvé a hacerla.
  · Una mediana de 0,000 puede ser "sin efecto" o "efectos que se cancelan".
    Reportá siempre la distribución.
  · Antes de lanzar cualquier A/B:
        VRP_PROFILE=<perfil> python -c "import pipeline.profile as p; print(p.<FLAG>)"
  · Antes de leer cualquier reproceso sobre datos existentes:
        python experiments/_s124_ndc_focus/05_verificar_reproceso.py <json>
  · Toda comparación entre corridas va sobre la INTERSECCIÓN de pasadas
    (datetime_utc + sensor), nunca sobre conteos de series completas.
  · Los seis patrones de error de S124 están en la memoria del agente
    (feedback_s124_verificar_antes_de_concluir).
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

### 2. ⚠️ ANTES del brazo D — rehacer el veredicto con PCC

Las auditorías de cierre encontraron que **PCC estaba escondido** de la tabla
por un bug de alias (ya corregido en `04_tabla_brazos.py`) y que **el brazo B lo
saca de banda** (0,75 ✓ → 0,64). También que varios números del veredicto no
tienen script detrás.

- [ ] Recorrer los criterios pre-registrados **con PCC incluido**.
- [ ] Escribir scripts que persistan recall por sensor y eventos ancla — hoy
      esos números fueron ad-hoc (viola S91).
- [ ] `03_leer_brazo.py` **no filtra sensor**: mezcla MODIS y V750 en una
      conclusión sobre VIIRS375. Arreglar antes de reusarlo.
- [ ] Reportar la **distribución**, no solo la mediana (190 de 274 pasadas de
      Láscar tienen ratio ≠ 1).

### 3. Brazo D — con la advertencia de que su respaldo se cayó

**Ojo**: la correlación que motivaba D17 se evaporó al usar la variable correcta
(r = +0,054, y PCC contradice la hipótesis). La desalineación es real
(Tupungatito 2996 m, PP 1873 m) y `get_grid_center()` sigue sin cablear — pero
**no hay evidencia de que sea la causa del sub-reporte**. Decidir con Nicolás si
vale las ~9 h de CI o si conviene ir directo a la auditoría de magnitud.

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

### 4. El 80 % del hueco (sin CI, en paralelo) — SUBE DE PRIORIDAD

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
