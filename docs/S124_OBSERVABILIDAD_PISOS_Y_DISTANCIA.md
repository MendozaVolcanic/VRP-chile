# Nubes, pisos VRP y filtros de distancia — cuatro preguntas de Nicolás (S124)

Las cuatro apuntaban a cosas reales. Una destapó un problema de interpretación
serio (julio), otra corrigió una hipótesis mía (el piso), y dos aclaran
arquitectura.

## 1. Nubes: el "apagón" de julio en NdC fue CEGUERA, no calma

Nicolás: *"sé que en julio tuvimos semanas enteras de nubes y lluvias"*. Confirmado,
y el dato **ya estaba en cada record** — no hay que instrumentar nada nuevo:

| mes | pasadas | pasadas CIEGAS | % ciego | nube mediana (px ROI) | noches útiles |
|---|---|---|---|---|---|
| 2026-05 | 138 | 9 | 7 % | 10 | 30 |
| 2026-06 | 132 | 19 | 14 % | 1.228 | 27 |
| **2026-07** | 131 | **60** | **46 %** | **8.002** | 23 |
| 2026-08 | 104 | 22 | 21 % | 1.811 | 21 |

- **CIEGA** = pasada sin fondo calculable (`t_bg_k is None`): la escena quedó sin
  píxeles válidos tras enmascarar nube.
- **nube** = `n_cloud_masked`, píxeles del ROI con I05 (TIR 11,45 µm) < 260 K.
  Campo ya persistido en cada record (`process_viirs.py:614`).

En julio **casi la mitad de las pasadas fueron inservibles** y la mediana de
píxeles nublados fue **800× la de mayo**. La lectura "el foco se apagó en julio"
es insostenible: en julio *no pudimos mirar*.

**Consecuencia**: un gráfico de VRP sin una banda de observabilidad induce a leer
ausencia-de-dato como ausencia-de-actividad. En monitoreo volcánico ese error
tiene un costo asimétrico: sugiere calma cuando en realidad no hay información.

**Acción**: integrar observabilidad al gráfico (banda/sombreado por noche con
% de pasadas ciegas). Complemento externo: las filas `RUTINA` del CSV MIROVA son
su propio "miré y no había nada" — permiten separar *nadie miró* de *se miró y
no había*.

**Hallazgo lateral**: el umbral de nube VIIRS está **hardcodeado en 260 K**
(`process_viirs.py:608`), independiente del `cloud_mask_bt_k` del perfil (que en
el operacional está en 0 = apagado). Son dos mecanismos distintos y el hardcodeado
corre siempre. No es un bug, pero es una constante fuera del perfil.

## 2. El "filtro de 750 m" — no existe, y no es VIIRS750

Aclaración: **750 m (mi gate de análisis) y VIIRS750 (el sensor de banda M) no
tienen relación**. Pura coincidencia de número. VIIRS750 es la banda M13 con
píxel de 750 m; el 750 m del análisis era el radio con que yo agrupé noches
alrededor de la celda del foco, **en un script descartable, no en el pipeline**.

Lo que el perfil del foco sí tiene es `inner_radius_km: 1.0` (vía
`volcano_overrides`), y **solo en el perfil experimental**.

### ¿Tiene la réplica filtros de distancia? Respuesta precisa:

| capa | qué hace | ¿es una cerca al cráter? |
|---|---|---|
| `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER` | corta a `max_hotspot_dist_km` = `radius_km` = **25 km** | **No** — es el borde de escena, la misma grilla 51×51 km de MIROVA |
| `inner_radius_km` en el pipeline | **clasifica** `summit` / `far` | **No** — no descarta nada |
| `mirovaEqVrp` en el **frontend** | pone VRP = 0 si `cdist > inner_radius_km` | **Sí** — filtro de distancia, a nivel de despliegue |

O sea: **el pipeline replica el comportamiento de MIROVA** (detecta en toda la
escena y clasifica), pero **el dashboard sí aplica una cerca**. Esa cerca es una
divergencia real respecto de MIROVA, que publica el hotspot esté donde esté y
reporta su distancia. (Las filas del CSV con distancias de 18-31 km existen; la
etiqueta `FALSO_POSITIVO` que las acompaña es del scraper de Nicolás, no de MIROVA.)

Nicolás lo formuló bien: *"mirova réplica debería detectar el píxel o los píxeles
de mayor valor como lo hace MIROVA, mientras que en experimental lo seteamos para
un área menor donde sabemos está el cráter activo"*. Eso es exactamente el diseño
del pipeline. La única capa que se sale es el frontend.

## 3. El piso VRP: existe, pero NO es lo que nos impide ver lo mínimo

**Mínimo absoluto publicado por MIROVA** (2154 ALERTAS de CONS ∪ OCR):
**0,01 MW** — Tupungatito, VIIRS375, 2026-07-21 04:30. Percentiles: p01 = 0,03;
p05 = 0,05; mediana = 0,29. Nuestro piso VIIRS375 es 0,02.

**Sólo 1 de 2154 alertas cae bajo nuestro piso.** Pero el piso sí es una
divergencia: MIROVA no tiene uno.

Tres precisiones que corrigen la hipótesis inicial:

1. **El piso está ACTIVO** (`store.py:466`), aunque `MISSION.md:128` lo dé por
   *"Removido S27"*. **Documentación desactualizada** — corregir.
2. **El piso no bloquea el dashboard.** Actúa sobre `record.vrp_mw`, y el
   dashboard lee `primary_cluster.vrp_mw`, que conserva el valor. Medido: NdC
   tiene 25 records con `pc.vrp` entre 0 y 0,02; Tupungatito, 52. **Sí vemos por
   debajo de 0,02.**
3. **La razón real de perder el 0,01 no es el piso ni la sensibilidad: fue nube.**
   El record de esa pasada (`VJ202IMG.A2026202.0430`) trae
   **`n_cloud_masked = 6892`** y todos los diagnósticos en `None`: la escena
   entera quedó enmascarada. No había con qué detectar. (Y es coherente con §1:
   el 21-jul está dentro del peor tramo nublado del año.)

El origen del piso también importa: se fijó en S12 (abril 2026) con
**n = 1-2 observaciones por sensor** — el mínimo que MIROVA había publicado hasta
esa fecha. Con 2154 alertas hoy sabemos que MIROVA baja a 0,01. El piso quedó
calibrado sobre una muestra que ya no representa la distribución.

## 4. Qué se propone

| # | acción | tipo |
|---|---|---|
| a | Banda de observabilidad en el gráfico (pasadas ciegas + nube por noche) | frontend, dato ya existe |
| b | Corregir `MISSION.md:128`: los pisos NO fueron removidos | doc |
| c | Evaluar bajar el piso VIIRS375 de 0,02 a 0,01 (el mínimo real de MIROVA) | A45, impacto medido: 1/2154 |
| d | Documentar la cerca de `inner_radius` del frontend como divergencia conocida | doc / `MIROVA_DIVERGENCES.md` |

Ninguna toca la detección. (a) y (d) son los de mayor valor: el primero evita
leer ceguera como calma; el segundo pone por escrito la única capa que se aparta
del comportamiento de MIROVA.
