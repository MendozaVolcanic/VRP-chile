# Laboratorio: análisis por áreas dentro de la grilla (borrador de diseño S194, espera a Nicolás)

> Estado: **BORRADOR**. Nada implementado. Responde al pedido de Nicolás del 2026-11-21 («sigue con el experimental,
> quizás ahí mismo podamos seleccionar áreas si queremos saber lo que pasa dentro»). Se apoya en
> `docs/PLAN_EXPERIMENTAL_S190.md` (decisiones D1 a D7 aceptadas el 2026-11-17) y en el perfil `laboratorio` del
> paso 1 (#1087). Lo que toque `pipeline/` es A45.

## 1. El fenómeno

Hoy cada pasada se resume en **un punto**: la regla «radiante» elige el cúmulo de mayor radiancia y el record queda
ahí, como cumbre o como lejano. Pero en la escena de 51 × 51 km pasan cosas distintas a la vez: un píxel tibio sobre
el cráter, un incendio en un valle agrícola, el reflejo o la inercia térmica de un lago, una colada que baja por un
flanco. Un solo punto esconde las demás. Las 12 alertas protegidas de MIROVA que perdemos de vista son justamente
pasadas con calor en el cráter y un cúmulo más fuerte lejos.

La idea de Nicolás es mirar **por áreas**: partir la escena en zonas con significado geológico y guardar, para cada
una, lo que pasó dentro. El volcán deja de ser «un punto por pasada» y pasa a ser «un estado por área por pasada».

## 2. Tres formas de hacerlo

| | Qué es | Toca `pipeline/` | Qué responde | Costo |
|---|---|---|---|---|
| **A. Partición posterior** | Se toman los píxeles alertados que cada record ya guarda (`anomaly_pixels`, con su posición) y se asignan a un área. Sobre la historia de producción desde 2025-02-15. | No | Dónde cae lo que **ya cruzó** el umbral: cuántas pasadas tienen calor en el cráter y a la vez en un lago o un incendio | Ninguno en Actions; un script |
| **B. Resumen por área en el laboratorio** | La vía, corriendo con el perfil `laboratorio`, escribe por área: alertados, VRP, NTI máximo, celdas válidas y nubladas. | Sí (A45) | Además, lo que **no cruzó** el umbral: si el cráter estaba tibio bajo la línea, o si el área estaba tapada | Reproceso del paso 4 del plan S190 (ya previsto) |
| **C. Umbral propio por área** | Cada área con su propio umbral de detección. | Sí (A45) | Detectar más en unas áreas y menos en otras | Es cambiar la detección; un criterio pre-registrado por área |

**Recomendación: A ahora, B en el reproceso del laboratorio, C sólo para el cráter** (que ya es la zona A del plan
S190, MEJ-5). A no cambia nada, cuesta un script y ya contesta la pregunta de Nicolás sobre lo publicado; B agrega lo
que pasa bajo la línea, que es la razón de ser del laboratorio; C en más de un área multiplica los grados de libertad
sin una vara para cada una.

**Dependencia de A:** que `anomaly_pixels` traiga todos los alertados de la pasada y no una muestra. Lo está
comprobando la medición del marcador «calor en la cumbre» (S194); si viene truncado, A se limita y B pasa a ser el
camino.

## 3. Qué áreas y cómo se definen

Un archivo de configuración por volcán, propuesto `config/areas_laboratorio.yaml` (fuera de `pipeline/profiles/`
para que A no sea A45), con áreas **excluyentes** y un orden de precedencia cuando se superponen:

| Prioridad | Área | Cómo se define | Por qué esa prioridad |
|---|---|---|---|
| 1 | **cráter** | círculo de `inner_radius_km` (`volcanoes.yaml`, KML de MIROVA) | es la zona A del plan S190; un lago cratérico (Copahue) es volcánico y queda aquí |
| 2 | **agua** | polígonos de `frontend/agua/<Volcan>.geojson` (JRC Global Surface Water, ocurrencia ≥ 50 %, los mismos que dibuja el mapa desde #1079) | un lago no es fuente térmica; lo que se alerta ahí es artefacto o geotermia |
| 3 | **incendio** | polígonos de zonas de incendio recurrente, **dibujados con Nicolás** sobre el mapa de alertas lejanas persistentes | conoce el terreno; derivarlos de FIRMS dejaría a FIRMS sin poder ser vara de esa misma área |
| 4 | **flanco** | anillo desde `inner_radius_km` hasta un radio por volcán (propuesto: el edificio volcánico; por defecto 10 km) | coladas, lahares calientes, fumarolas laterales |
| 5 | **resto** | lo que queda de la grilla de 51 × 51 km | valles, salares, todo lo demás |

Puyehue Cordón Caulle (radio interno de 20 km) queda fuera de la primera tanda, como en D6.

## 4. Qué se guarda por área y por pasada

- **En A:** número de alertados, VRP sumado (MW), distancia y radiancia del alertado más fuerte del área.
- **En B, además:** NTI máximo del área (aunque no cruce el umbral), número de celdas válidas, nubladas y sin dato.
  Sin el conteo de celdas válidas, «no hubo calor en el cráter» y «el cráter estaba tapado» se confunden.

El VRP publicado no cambia: sigue siendo la suma de todos los alertados (D32). La partición sólo reparte esa suma.

## 5. Contra qué se valida (nunca contra MIROVA, A115)

| Área | Vara | Advertencia |
|---|---|---|
| cráter | NHI de Sentinel 2 y Landsat (repo NHI-v1), episodios OVDAS (D4), persistencia | la caja de NHI es de unos 8 × 8 km centrada en el volcán (160.000 píxeles de 20 m): sólo cubre cráter y flanco cercano; NHI es diurno y cada pocos días; Lastarria no tiene serie |
| flanco | episodios OVDAS (coladas, lahares), persistencia | sin OVDAS sólo queda la persistencia |
| agua | **ninguna fuente esperada**: sirve de **control negativo** | cada alerta persistente sobre agua es un falso positivo por construcción; mide el ruido del detector (A110) |
| incendio | FIRMS (fuego activo de NASA, algoritmo distinto) y estacionalidad (verano) | FIRMS usa los mismos satélites; sirve para fuego, no para volcán |
| resto | FIRMS y persistencia | |

## 6. Cómo se vería

Nada en el tablero operacional (guard del plan S190 §4). En la pestaña Laboratorio, para cada volcán, una franja por
área y por noche: gris si el área estaba tapada, blanco si se vio y no hubo nada, color si hubo alertados (con su
VRP). Es la «vista de tres estados» de S147 §8, extendida a áreas.

## 7. Decisiones para Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| AR1 | ¿Por dónde empezar? | A (partición posterior, sin tocar `pipeline/`); B directamente; A y B juntos | **A**: contesta ya qué pasa en cada área con lo publicado, a costo cero |
| AR2 | ¿Qué áreas? | las cinco de la tabla del §3; menos (cráter, agua, resto); otras | **las cinco**, con «incendio» vacío hasta dibujarlo juntos |
| AR3 | ¿Radio del flanco? | 10 km fijo; por volcán según el edificio; el que diga Nicolás | **por volcán**, con 10 km mientras no se defina |
| AR4 | ¿Quién dibuja las zonas de incendio? | Nicolás sobre un mapa de alertas lejanas persistentes que preparamos; derivarlas de FIRMS | **Nicolás sobre el mapa**: FIRMS queda libre para validar |
| AR5 | ¿B entra en el reproceso del paso 4 del plan S190? | sí, en el mismo reproceso; en uno aparte | **sí, en el mismo**: un solo reproceso, la misma ventana |

## 8. Lo que este borrador no resuelve

- Si `anomaly_pixels` trae todos los alertados (lo mide el marcador de S194).
- Cómo guarda la vía la grilla durante el proceso, para B: no leí `pipeline/mirova_v750_codigo.py` con ese fin.
- El radio del edificio volcánico por volcán: no está en el repo.
