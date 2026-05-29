# Diseño — campo `pc.classification` (Bloque 3, reideado S88)

**Fecha**: 2026-05-29 (S88). **Estado**: DISEÑO — pendiente aprobación de Nicolás
antes de implementar (A45: toca `store.py` + frontend). **NO implementado.**

**Reconcilia**: el diseño original Bloque 3 (`tasks/BLOQUE_ARRANQUE_S87.md:130-173`)
con los hallazgos S86 (`docs/AUDIT_S86.md`) y S88
(`experiments/_s88_lascar_reselect/`).

---

## 1. Problema y objetivo

El dashboard hoy se presenta como "clon MIROVA", pero S86 probó con datos que el
**46.3% de nuestros "FPs" son features volcánicas reales que MIROVA no publica**
(categoría b: lacolito PCC, Lazufre, cráter El Agrio, Pichi-Llaima, etc.). Mostrarlas
como "sobre-detección vs MIROVA" es engañoso: es valor agregado, no ruido.

**Objetivo**: etiquetar cada detección con su naturaleza respecto a MIROVA, para que el
frontend muestre honestamente "monitoreo VRP Chile con desglose MIROVA" en vez de
"clon que sobre-detecta". El operador de OVDAS distingue de un vistazo qué confirmó
MIROVA, qué es extensión real nuestra, y qué es dudoso.

## 2. Tensión central (por qué este diseño difiere del de S87)

El diseño S87 proponía 4 categorías, pero **2 de ellas embeben reglas físicas que S86
ya refutó con datos**. Etiquetar con una regla mal calibrada no es neutral: marca
anomalías reales como artefacto, replicando el error de fondo en el NRT.

### 2.1 `artifact_candidate` con `t_bg<260K` — REFUTADO (S86 Mec 2)

El diseño S87 define artefacto como `t_bg<260K AND only_path_D AND n_pixels<=1`. Pero
S86 probó que el gate `t_bg≥260K` **pierde 3 TPs reales**, incluido el **evento
eruptivo de Lascar 2026-02-17** (cluster 12 px, 119 MW), cubierto por nube fría
(cirrus irradia desde ~-40°C → `t_bg` baja) y capturado SOLO por path D. La nube enfría
el background; el calor volcánico sigue ahí debajo. Usar `t_bg<260K` como criterio de
"artefacto" etiquetaría ese evento como dudoso. **Inaceptable.**

El residual real de artefacto (S86: 4.6%) se concentra en dos mecanismos físicos
específicos y acotados, NO en un gate `t_bg` global:
- **PCC cirrus alto** (D9): path D contextual sobre cirrus uniforme infla magnitud.
- **Tupungatito ring glaciar** (A19): vecinos del hot pixel son "warm relativo" sobre
  escena de hielo → ΔL no se reduce.

### 2.2 `vrp_chile_summit_unconfirmed` como catch-all — riesgo de absorber la categoría (b)

Si `volcanic_extension` exige una feature catalogada a ≤2 km, todo lo demás cae en
`summit_unconfirmed`. Pero gran parte de la categoría (b) de S86 (la dispersión real
del domo de Chaitén, el complejo multi-cráter PP, focos del lacolito PCC sobre 40 km)
NO está a ≤2 km de UN punto catalogado — está distribuida. Quedaría mal-etiquetada
como "sin confirmar" cuando en realidad ES extensión volcánica real.

## 3. Tres enfoques considerados

### Enfoque A — Las 4 categorías del diseño S87 (literal)
Implementar tal cual, incluyendo `artifact_candidate` con `t_bg<260K`.
- **Contra**: replica el gate refutado S86; etiqueta Lascar 02-17 eruptivo como
  artefacto. Viola el espíritu de A55 (gate por-path mal calibrado, ahora como label).
- **Veredicto**: RECHAZADO.

### Enfoque B — Solo categorías objetivas (3 categorías, sin reglas físicas)
- `mirova_confirmed`: la noche-sensor tiene ALERTA MIROVA (CONS∪OCR) que matchea
  espacialmente (gap ≤ tol). 100% verificable contra el CSV, cero física embebida.
- `volcanic_extension`: cluster dentro de `inner_radius_km` O ≤ X km de una feature
  catalogada (GVP + sub-features S86), SIN MIROVA esa noche. Es la categoría (b).
- `unclassified` (renombre honesto de summit_unconfirmed): todo lo demás. NO afirma
  "artefacto" ni "summit" — solo "no clasificado automáticamente".
- **Pro**: cero reglas refutadas; cada etiqueta es objetiva y defendible; no toca la
  detección, solo describe. Alineado con el marco S86 sin distorsionar el clon.
- **Contra**: no separa el 4.6% de artefacto real → el operador no lo ve marcado.
- **Veredicto**: RECOMENDADO como base.

### Enfoque C — B + artefacto físicamente honesto (4 categorías, reglas calibradas)
Igual que B, pero agrega `artifact_candidate` SOLO con los dos mecanismos que S86
identificó empíricamente, NO el gate `t_bg` global:
- PCC + path D contextual dominante + magnitud sobre cap D9 (mecanismo cirrus).
- Tupungatito + patrón ring glaciar (mecanismo A19).
- **Pro**: marca el artefacto real sin tocar el evento eruptivo de nube fría (que NO
  cae en estos dos mecanismos: Lascar no es PCC ni Tupungatito).
- **Contra**: más reglas per-vol → más superficie de mantenimiento; requiere validación
  pixel-level (R2) de que esos dos mecanismos no capturan TPs reales.
- **Veredicto**: deseable como Fase 2, DESPUÉS de validar B en producción.

## 4. Diseño recomendado (Enfoque B ahora, C como fase 2)

### 4.1 Campo y valores

```python
# Calculado en store.append_record, post-selección de primary_cluster.
pc["classification"] = (
    "mirova_confirmed"     if _matches_mirova_alerta(record, mirova_index, tol_km) else
    "volcanic_extension"   if _is_volcanic_extension(pc, volcano, features) else
    "unclassified"
)
```

- `mirova_confirmed` — existe ALERTA MIROVA (CONS∪OCR vía `load_mirova_alertas`, el
  loader canónico S87) para `(volcano, sensor_bucket, noche)` con `|dist_ours -
  dist_mirova| ≤ tol_km` (tol = 2 km, consistente con S87/S88).
- `volcanic_extension` — `pc.centroid_dist_km ≤ inner_radius_km` (es del cono) O
  `≤ EXT_KM` de una feature catalogada en `pipeline/volcanic_features.yaml`, y NO hay
  ALERTA MIROVA esa noche. Categoría (b) de S86.
- `unclassified` — el resto. Etiqueta neutra, NO afirma artefacto ni validez.

### 4.2 Decisión de arquitectura crítica: clasificación es POST-PROCESO, no en el pipeline

**`mirova_confirmed` depende de los CSV MIROVA, que NO deben ser un input del pipeline
NRT** (el pipeline produce nuestras detecciones; MIROVA es ground truth EXTERNO que se
cruza después). Meter la lectura del CSV en `store.append_record` acoplaría el NRT a un
artefacto de scraping de otro repo (Mirova-v1) — frágil y conceptualmente sucio.

**Por eso la clasificación se parte en dos:**
- `volcanic_extension` vs `unclassified`: SÍ es derivable solo de nuestro record
  (`pc.centroid_dist_km`, `inner_radius_km`, features YAML) → puede ir en `store.py`
  como campo `pc.geo_class` ("summit" | "extension" | "far"). Geometría pura, sin física
  refutada, sin dependencia externa.
- `mirova_confirmed`: es un cruce con ground truth externo → se calcula en el
  **frontend** (que YA carga el CSV consolidado, `index.html` + `diario.html`) o en un
  script de post-proceso, NO en el pipeline. El frontend ya tiene `mirovaEqVrp` y el
  índice de records MIROVA; agregar el match de confirmación ahí es natural.

Esto **minimiza el cambio a `store.py`** (solo geometría, bajo riesgo A45) y mantiene el
cruce con MIROVA donde corresponde (capa de presentación / auditoría).

### 4.3 Qué toca exactamente

| Componente | Cambio | A45 |
|---|---|---|
| `store.py` | agregar `pc["geo_class"]` (summit/extension/far) por geometría pura | SÍ — tag `pre-s89-geo-class` + OK Nicolás |
| `pipeline/volcanic_features.yaml` | NUEVO — coords GVP + sub-features S86 por vol | no (archivo nuevo) |
| `frontend/index.html` | calcular `mirova_confirmed` (cruce CSV) + render 3 colores por clase | no toca pipeline, pero verificar dashboard |
| `tests/test_store_geo_class.py` | NUEVO — casos sintéticos summit/extension/far | no (TDD primero) |

### 4.4 `pipeline/volcanic_features.yaml` (cartografía categoría b)

Coords Smithsonian GVP + sub-features identificadas por Subagente E (S86):
Cerro Blanco (NdC), Pichi-Llaima (Llaima), Lazufre (Lastarria), cráter El Agrio +
alineación E-W (Copahue), Planchón N + Azufre (PP), focos lacolito (PCC), lava lake
(Villarrica), cráter cumbre (Tupungatito). **Las coords son DATOS, no opiniones**
(A5) — se toman verbatim de GVP/KMZ, citando fuente por entrada. `EXT_KM` por feature
o global (default 2 km, revisable per-vol para complejos extendidos como PCC/PP).

## 5. Plan de implementación (próxima sesión, tras aprobación)

1. **TDD primero** (`test-driven-development`): `tests/test_store_geo_class.py` con
   casos sintéticos — cluster en cráter→summit, sobre feature catalogada→extension,
   lejano sin feature→far. Tests fallan (campo no existe).
2. **Tag defensivo** `pre-s89-geo-class` + push (A45).
3. Crear `pipeline/volcanic_features.yaml` (coords verificadas GVP).
4. Implementar `pc["geo_class"]` en `store.py` (geometría pura, ~15 líneas). Tests pasan.
5. Frontend: cargar features YAML, calcular `mirova_confirmed` por cruce CSV, render
   3 colores. Verificar dashboard con preview.
6. Verificación: suite verde + R2 muestra de N records clasificados vs Google Earth/KMZ.
7. Fase 2 (sesión aparte): evaluar Enfoque C (artefacto físico PCC/Tupungatito) con A/B.

## 6. Escudo anti-drift

- NO se embebe el gate `t_bg<260K` (refutado S86) en ninguna parte.
- `geo_class` es geometría pura sobre `pc.centroid_dist_km` ya calculado — NO cambia
  detección ni selección de cluster (vent_anchored intacto, validado S87).
- El cruce con MIROVA queda en la capa de presentación, NO acopla el NRT a un CSV externo.
- NO es un "gate por-path" (A55): es una etiqueta descriptiva, no filtra ni suprime nada.

## 7. Preguntas abiertas para Nicolás (antes de implementar S89)

1. ¿`geo_class` en `store.py` (3 valores geométricos) + `mirova_confirmed` en frontend
   te parece la división correcta? ¿O preferís todo en un solo lugar?
2. `EXT_KM` (distancia a feature catalogada para contar como "extension"): ¿2 km global,
   o per-vol (PCC/PP necesitarían más por ser complejos extendidos)?
3. ¿Fase 2 (artefacto físico PCC/Tupungatito) la querés en el roadmap, o el dashboard
   con 3 categorías honestas (confirmado / extensión / sin clasificar) ya cumple el
   objetivo de "monitoreo con desglose MIROVA"?

## 8. Self-review del spec

- Sin placeholders. Reglas concretas con umbrales nombrados (tol 2 km, EXT_KM 2 km).
- Contradicción potencial resuelta: por qué `mirova_confirmed` NO va en store.py (§4.2).
- Scope acotado: Enfoque B ahora (3 categorías objetivas), C diferido y gateado por A/B.
- Alineado con marco S86 (categoría b = valor) y escudo anti-drift (sin gate refutado).
