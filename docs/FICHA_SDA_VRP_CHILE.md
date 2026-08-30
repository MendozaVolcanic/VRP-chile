# Ficha de Transparencia Algorítmica — VRP Chile

> Ficha modelo según Recomendaciones CPLT (Resolución Exenta N°372). Borrador técnico
> generado por el equipo; los campos legales/institucionales marcados `<completar>` los
> debe validar SERNAGEOMIN antes de cualquier publicación. Plantilla: `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`.

**Identificador interno:** VRP-CL  ·  **Versión:** v1.3 — 2026-08-09  ·  **Estado:** producción (NRT)

---

## Subítem 1 — Sistemas de decisiones (CPLT 6.5)
- **Canal de consulta/reclamación:** `<completar: sí/no; vía OVDAS u otra>`
- **¿Permite oposición a decisión automatizada?:** No aplica — el SDA no decide sobre personas (no perfila individuos).
- **Titularidad:** Organismo / Estado (desarrollo propio, código en repositorio MendozaVolcanic/VRP-chile). `<confirmar titularidad institucional>`
- **Proveedor:** No aplica (desarrollo propio).
- **Más información:** `<enlace institucional>`

## Subítem 2 — Servicios/procedimientos (CPLT 6.6)
- **Servicio/procedimiento donde se usa:** Monitoreo de actividad volcánica / insumo a la evaluación de alerta técnica volcánica.
- **Unidad que lo usa:** OVDAS (Observatorio Volcanológico de los Andes del Sur), SERNAGEOMIN.
- **Acto que lo estableció:** `<tipo, número, fecha, enlace>` — Información no disponible.

## Subítem 3 — Especificaciones del SDA (CPLT 6.7)
- **Objetivo:** Detectar y cuantificar anomalías térmicas en volcanes chilenos a partir de imágenes satelitales (MODIS/VIIRS), replicando de forma independiente la metodología MIROVA, para apoyar la vigilancia volcánica.
- **Funcionamiento/lógica:** Sobre cada escena satelital se identifican píxeles "calientes", se estima la temperatura de fondo local y se calcula la Potencia Radiada Volcánica (VRP) con ecuaciones físicas (Planck/Wooster). El VRP se compara con umbrales para clasificar el nivel de actividad térmica. La cuantificación de magnitud suma únicamente los píxeles del foco térmico contextualmente anómalo, separándolos del campo difuso de gran escala (gradiente topográfico nocturno sobre terreno nival), de modo que la magnitud refleje la energía del rasgo volcánico y no el calor ambiental residual. En el régimen de muy baja energía se recuperan focos sub-píxel débiles que el sensor de mayor resolución (VIIRS 375 m) cuantifica, mediante un anillo de fondo intermedio condicionado a la compatibilidad del fondo regional. Una verificación de coherencia espacial garantiza que la etiqueta "cumbre" (anomalía al cráter) sea consistente con la ubicación real del cúmulo térmico reportado.
- **¿Categoriza/perfila individuos?:** **No.** Opera exclusivamente sobre datos físicos satelitales.
- **Método/modelo:** **Reglas físicas determinísticas** (Wooster MIR; ecuaciones Coppola 2016a/2024 por régimen térmico). **No utiliza aprendizaje automático ni constituye una caja negra** — la lógica es íntegramente auditable.
- **Efecto de las variables principales:** El VRP crece con el exceso de radiancia del píxel sobre el fondo y con el área caliente; la distancia al cráter y la geometría de la escena filtran detecciones espurias.
- **Categorías de datos:** Radiancia/temperatura de brillo de sensores MODIS (MOD14/MYD14) y VIIRS.  ·  **¿Datos personales?:** **No.**  ·  **¿Sensibles?:** **No.**
- **Datos de entrenamiento/validación/prueba:** **No aplica** (el sistema no se entrena; usa ecuaciones físicas). Validación cruzada contra valores MIROVA publicados.
- **Evaluaciones de impacto / sesgos:** Sesgos físico-instrumentales (saturación de píxel, nubosidad, contaminación por lago/nieve, falsos positivos por incendios). Mitigación: filtros de contexto, zonas de exclusión y degradación explícita a fondo regional. Límites físicos caracterizados y documentados (no errores corregibles):
  - *Sesgo topográfico en volcanes con cumbre nevada:* el gradiente térmico nocturno entre el cráter frío y el valle tibio de baja altitud puede desplazar la posición estimada del foco hasta ~1 km respecto del cráter en los métodos que usan radiancia infrarroja media (MIR) absoluta; mitigado normalizando por índice térmico (NTI).
  - *Sobre-detección difusa a la resolución MODIS (1 km):* a esa escala un foco sub-píxel débil y el gradiente topográfico difuso son físicamente indistinguibles; la detección de detalle se cubre con el sensor de mayor resolución espacial (VIIRS 375 m).
  - *Artefactos solares diurnos:* la reflexión solar sobre nubes puede simular una anomalía térmica; mitigado restringiendo la detección MIR a pasadas nocturnas.
- **Política de privacidad:** No aplica (sin datos personales).
- **Caja negra (punto 5.5):** No corresponde — sistema explicable.

---

**Actualización:** revisar esta ficha cuando cambie la lógica de detección, los umbrales de
clasificación, los sensores de entrada o las ecuaciones de régimen. El CPLT sugiere refrescar la
información mensualmente (primeros 10 días hábiles).

## Historial de versiones

| Versión | Fecha | Cambios sustantivos | Traz. interna |
|---|---|---|---|
| v1.4 | 2026-08-30 | **Corrección de alcance declarado (sin cambios de lógica).** La ficha de trazabilidad del módulo que ajusta la magnitud en régimen de muy baja energía (`single_pixel_mode.py`) declaraba entre sus limitaciones que **no se aplicaba a Villarrica**. Una verificación sistemática contra los datos publicados mostró que **sí se aplica**: en Villarrica el ajuste está activo en 3.025 registros y modifica el valor informado en 442 (10,9 %). La misma afirmación nombraba como no afectados a otros seis volcanes —Copahue, Isluga, Láscar, Lastarria, Llaima y Nevados de Chillán— y **era incorrecta para los siete**; de hecho el más afectado de toda la red es **Láscar** (33,9 % de sus registros), que figuraba como no afectado, mientras que el volcán para el cual el ajuste fue creado —Tupungatito— es hoy el **menos** afectado (7,5 %). La declaración se **retira** en lugar de reescribirse, porque el alcance depende de los datos y vuelve a desactualizarse: ahora se **mide** con un procedimiento reproducible y queda un control automático que impide volver a declararlo por escrito. Se corrige además una referencia de ubicación que apuntaba a un bloque equivocado del archivo de configuración. **La lógica de decisión no cambió**: los parámetros del ajuste (activación, umbral 5,0 MW y máximo de 3 píxeles) permanecen idénticos, verificado sobre los 51 perfiles de configuración. Se registra también una corrección interna en el cálculo de magnitud con fondo local, **sin efecto sobre la serie publicada** (la función está desactivada en producción y la equivalencia se comprobó bit a bit). Detalle: `docs/AUDIT_S127.md`. | S127 |
| v1.3 | 2026-08-09 | **Corrección de alcance:** dos de los ocho módulos secundarios que v1.2 listaba como participantes de la decisión — `path_d_intra_radio.py` y `second_pass_intra_radio.py` — **están desactivados desde S118** y ya **no intervienen** en la detección ni en la magnitud. Eran restricciones geométricas que suprimían detecciones fuera de un radio interno; un experimento controlado (A/B con reproceso real sobre 214 noches con anomalía confirmada por MIROVA) mostró que **no evitaban ningún daño medible** — la selección del foco principal, anclada al cráter, ya era robusta por sí sola — mientras que sí arriesgaban descartar anomalías térmicas reales de baja energía. Se apagaron por ese motivo (mayor sensibilidad, sin pérdida de especificidad medida). Sus cabeceras de trazabilidad se conservan en el código como registro histórico. **Sin otros cambios de lógica** desde v1.2. **Continuidad operacional:** se registra una interrupción del servicio NRT entre el 2026-07-20 y el 2026-08-04 por expiración de la credencial de acceso a los datos satelitales de NASA; los datos del período fueron recuperados retroactivamente (reproceso 21-jul → 02-ago de los 11 volcanes vigilados) y la serie no presenta vacíos. Se reforzó el sistema de avisos de interrupción para que escale por antigüedad y notifique también la recuperación. | S118-S123 |
| v1.2 | 2026-06-28 | Trazabilidad de código (pasada secundaria): se agregaron cabeceras FICHA SDA Nivel-1 a los **8 módulos de detección/clasificación secundarios** que participan en la decisión (`test1_integrated.py`, `test1_contextual_filter.py`, `test1_spatial_core.py`, `path_d_cap.py`, `path_d_intra_radio.py`, `second_pass_intra_radio.py`, `exclusion_zones.py`, `single_pixel_mode.py`). **Sin cambios de lógica** (comment-only; suite 797 passed, 0 fail). Criterio de alcance (Res.372 §4.8): se documentan los módulos que **clasifican/deciden/optimizan** la detección o la magnitud; se excluyen los de **serialización/agregación** (`anomaly_pixels.py` serializa píxeles ya calculados; `clustering.py` cuenta regiones contiguas estilo MIROVA) y los **no productivos** (`vrptir.py` diagnóstico `ENABLE_VRPTIR_AVENI=False`; `detect_tirvolch.py` sin referencias en producción). Cierra el backlog S117 #2. | S117 |
| v1.1 | 2026-06-27 | Trazabilidad de código: se agregaron las cabeceras FICHA SDA Nivel-1 a los archivos núcleo que participan en la decisión (`process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`, `store.py`, `anchor.py`, `detection_context.py`) — cierra la deuda de cabeceras detectada en AUDIT_S116 (C1; el inventario previo daba `anchor.py` por hecho, era falso). Sin cambios de lógica. Se re-confirmó (S114) que la detección MODIS es fiel a Coppola 2016a (dual-ROI 5σ/10σ, Tests 2∧3, second-run, ETI cuadrático) y que no queda gap literal accionable (GAP #A resuelto S115 como mislabel). | S116 (AUDIT_S116) |
| v1.0 | 2026-06-22 | Primera versión estampada (reemplaza el borrador `<vX.Y>` de origen). Documenta la cuantificación foco-vs-difuso (la magnitud suma sólo el foco contextualmente anómalo, no el campo difuso topográfico), la recuperación de focos sub-píxel débiles en régimen de muy baja energía (anillo de fondo intermedio condicionado), la verificación de coherencia espacial de la etiqueta "cumbre", y los tres límites físicos caracterizados (sesgo topográfico en nevados, sobre-detección difusa irreducible a 1 km en MODIS, artefacto solar diurno). | S109–S114 |
| `<vX.Y>` | (origen) | Borrador técnico inicial de la ficha. | S110 (#428) |
