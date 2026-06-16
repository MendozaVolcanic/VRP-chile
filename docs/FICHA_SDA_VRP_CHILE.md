# Ficha de Transparencia Algorítmica — VRP Chile

> Ficha modelo según Recomendaciones CPLT (Resolución Exenta N°372). Borrador técnico
> generado por el equipo; los campos legales/institucionales marcados `<completar>` los
> debe validar SERNAGEOMIN antes de cualquier publicación. Plantilla: `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`.

**Identificador interno:** VRP-CL  ·  **Versión:** `<vX.Y — fecha>`  ·  **Estado:** producción (NRT)

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
- **Funcionamiento/lógica:** Sobre cada escena satelital se identifican píxeles "calientes", se estima la temperatura de fondo local y se calcula la Potencia Radiada Volcánica (VRP) con ecuaciones físicas (Planck/Wooster). El VRP se compara con umbrales para clasificar el nivel de actividad térmica.
- **¿Categoriza/perfila individuos?:** **No.** Opera exclusivamente sobre datos físicos satelitales.
- **Método/modelo:** **Reglas físicas determinísticas** (Wooster MIR; ecuaciones Coppola 2016a/2024 por régimen térmico). **No utiliza aprendizaje automático ni constituye una caja negra** — la lógica es íntegramente auditable.
- **Efecto de las variables principales:** El VRP crece con el exceso de radiancia del píxel sobre el fondo y con el área caliente; la distancia al cráter y la geometría de la escena filtran detecciones espurias.
- **Categorías de datos:** Radiancia/temperatura de brillo de sensores MODIS (MOD14/MYD14) y VIIRS.  ·  **¿Datos personales?:** **No.**  ·  **¿Sensibles?:** **No.**
- **Datos de entrenamiento/validación/prueba:** **No aplica** (el sistema no se entrena; usa ecuaciones físicas). Validación cruzada contra valores MIROVA publicados.
- **Evaluaciones de impacto / sesgos:** Sesgos físico-instrumentales (saturación de píxel, nubosidad, contaminación por lago/nieve, falsos positivos por incendios). Mitigación: filtros de contexto, zonas de exclusión y degradación explícita a fondo regional.
- **Política de privacidad:** No aplica (sin datos personales).
- **Caja negra (punto 5.5):** No corresponde — sistema explicable.

---

**Actualización:** revisar esta ficha cuando cambie la lógica de detección, los umbrales de
clasificación, los sensores de entrada o las ecuaciones de régimen.
