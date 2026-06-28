# AUDIT_S116 — Seguimiento: 3 investigaciones read-only post-sprint

**Fecha:** 2026-06-27 · **Sesión:** S116 · **Método:** workflow read-only de 3 hilos paralelos +
síntesis (run `wf_ff8f2aa2-fb8`). **NO toca pipeline, NO revierte nada** (respeta S105). Outputs:
`experiments/_s116_followup/{c2_discriminator,new8_residual,llaima_offset}.json`.

**Origen:** Nicolás pidió investigar los hilos que el sprint dejó destapados. Los tres convergen en
el **mismo límite físico A82** y arrojan un resultado de método valioso.

---

## El fenómeno común (geología)

En un volcán de cumbre nevada, el cráter en la cima está **frío** y el valle/bosque de menor altitud
está **tibio**. Ese gradiente topográfico nocturno produce una "anomalía" térmica al N del cráter que
**no es lava**. El problema: a la resolución de VIIRS/MODIS (375 m – 1 km), el **foco volcánico real
y débil** (lava lake, domo, fumarola sub-píxel) es **espectralmente idéntico** a ese ruido
topográfico. Los tres hilos chocan con ese muro.

---

## Hilo 1 — ¿Discriminante físico que reemplace el gate geométrico de C2? **NO** (resultado negativo informativo)

Sobre los **4560 records** summit-intra que los gates preservan (37,1 % MIROVA-confirmados):

- El mejor discriminante físico es **`test1_k_observed`** (excedente MIR integrado del Test 1, Coppola
  2015 Eq.1): **AUC global 0.859**. Pero su cut óptimo **rechaza solo 69,8 % del artefacto nevado y
  pierde 15,9 % del cat-b confirmado real** — justo los focos sub-píxel tenues que VRP Chile DEBE
  preservar (A54/A82).
- El cut es **régimen-dependiente** (focales ~4-5 K, nevados ~2,8-3,9 K). Un cut global = **gate
  per-volcán disfrazado de física** — no más clon-literal que la máscara por distancia que MISSION objeta.
- En el régimen nevado el discriminante **colapsa** (AUC 0.762): el foco real raro y el artefacto se
  solapan energéticamente (Llaima n=1 TP, Copahue n=4...).
- **⚠️ Refutación A80 (corrige una regla):** la hipótesis "el artefacto está en el piso `nti_max` ~−0,9
  y el cat-b real más arriba" queda **REFUTADA** — `nti_max` AUC 0.251 (inverso): el cat-b confirmado
  se sienta **MÁS ABAJO** (mediana −0,941) que el artefacto (−0,919). **El piso `nti_max` es COMPARTIDO
  por ambas clases** (contaminación por altitud/fondo frío). `nti_max` NO sirve como discriminante real-vs-artefacto.

**Conclusión:** no existe escalar físico universal. El eje **espacial** (geometría / contexto) es la
**única** dimensión que separa las clases (refuerza A82). El A/B futuro de C2 debe ser
**estratificado focal/nevado**; **no seguir buscando un discriminante físico universal (frente agotado, anti-A8).**

## Hilo 2 — ¿Vale el A/B F2.1 de NEW-8? **Baja prioridad post-D9** (no obsoleto)

De 17 464 records Tier A, solo **832** sobreviven el filtro (path-D-dominante ∧ frío ∧ no-confirmado ∧
visible-en-dashboard), todos en 4 volcanes de baja altitud (Copahue 123, Villarrica 129, PCC 532,
Chaitén 229). Al inspeccionarlos (A62):
- ~99 % ya tienen `pc.vrp ≤ 5 MW` (D9 ya capa la magnitud).
- Re-anclados al GVP (A61) caen **SOBRE el cráter** (Villarrica 129/129, Copahue 123/123, Chaitén 227/229,
  PCC en el lacolito ~8 km). Incluso el subconjunto más frío (`t_bg<255K`, cirrus puro): 137/144 sobre el cráter.
- Son **señal cat-b real sub-umbral** (lava lake Villarrica, cráter El Agrio Copahue, domo Chaitén,
  lacolito PCC; A54), NO outliers negativos dispersos de borde.

**Conclusión:** el síntoma que NEW-8 atacaría ya lo cubren D9 + guard A46 + nadir/focal. Aplicarlo ahora
**removería señal real, no cirrus** (killer A82). Cerrar el A/B F2.1 como baja prioridad. **No declararlo
obsoleto** — sigue siendo gap de fidelidad LITERAL del pool m,σ vs SP426.5 (A48/A50). Si alguna vez se
corre, pre-registrar el criterio de éxito = "no toca los 832 cat-b". Lever real de cirrus = discriminante
NO-`t_bg` (S113), no NEW-8.

## Hilo 3 — Sesgo espacial de Llaima: **confirma A69, 2º caso documentado**

- Mismo sesgo direccional N que Villarrica (S104): VIIRS375 con **63,5 % de clusters al N**, vector
  resultante neto **1,22 km al N**, `nti_max` pegado al piso (−0,94; 96,6 % ≤ −0,9).
- **NO es el lago Conguillío:** de 338 clusters al N en la banda 2-4 km, **CERO** caen en la zona del lago
  (6-10 km NE). Es gradiente topográfico local puro.
- La **ancla honesta cura el sesgo** (78 % a ≤1 km del cráter, 81 % de los sesgados >2 km recuperados)
  cuando `final_hotspot_source=test1_roi`; **falla parcialmente** cuando hereda `ctx_cluster` (VIIRS750
  solo 49 %, porque el ctx_cluster arrastra el centroide sesgado N).
- **Método (A70):** la mediana del *bearing* es engañosa (artefacto); usar histograma cardinal + vector resultante.

**Follow-up (no urgente, A46-adyacente):** el `ctx_cluster` debería re-anclarse al cráter cuando hay
señal Test1 al cráter, igual que `test1_roi`. Toca pipeline → A/B + A45 antes de cualquier cambio.

---

## Síntesis / sorpresa convergente (A62)

Los **tres hilos terminan en el mismo límite A82**: a 1 km, el foco débil real y el ruido topográfico
son el **mismo objeto** en todos los ejes medibles (energía, NTI, magnitud). Por eso **cualquier corte
físico que limpie el ruido mata cat-b**. El gate geométrico / la ancla honesta no son elecciones de
conveniencia: son la **única dimensión (espacial)** que separa las clases. La refutación de A80 como
discriminante (el cat-b real está MÁS frío en `nti_max`, no más caliente) es la corrección concreta de
método que sale de esta ronda.

## Acciones backlog S117 (todas no-urgentes)
1. **C2**: A/B estratificado focal/nevado cuando reabra el frente Test1/fondo-local (A45). NO buscar más un escalar físico universal (anti-A8).
2. **NEW-8**: cerrado como baja prioridad (dato cuantitativo anotado en MIROVA_DIVERGENCES). 
3. **Llaima/ctx_cluster**: ~~candidato A46-adyacente~~ → **CERRADO S117 (ver addendum abajo, A84): no existe fix seguro.**
4. **Regla**: refinar A80 en CLAUDE.md — `nti_max` plano NO discrimina cat-b real de artefacto (piso compartido); el eje espacial es el único separador (refuerza A82).

---

## Addendum S117 (2026-06-28) — Hilo 3 / acción 3 CERRADA: NO existe fix seguro para el re-ancla ctx_cluster

Nicolás eligió investigar #1b a fondo ("podemos probar todo"). Antes de implementar (gate de
brainstorming + A45), se ejecutó un **probe read-only** y se cruzó con la data de S106. **Convergen en
que no hay fix seguro** → #1b cerrado (regla **A84**). No se tocó pipeline.

**Dimensionado del problema.** El sesgo es solo de POSICIÓN: los records `ctx_cluster` de Llaima V750
(57/122) reportan la posición ~1.4 km al N del cráter pero **ya están clasificados `summit`** (dentro
del inner). No afecta detección, magnitud ni summit/far — es cosmético (el punto en el mapa cae 1.4 km
al N).

**El riesgo (A82/A83).** El `ctx_cluster_anchor` es el `primary_cluster` (todos los paths del hot_mask),
por eso arrastra el sesgo topográfico. Un override global "si hay Test1 al summit → preferir cráter"
también re-anclaría offsets within-inner **reales** — **Lastarria** (campo fumarólico Lazufre) es el
caso textbook: snap-a-cráter destruye señal cat-b real.

**Evidencia convergente (dos vías independientes):**
1. **Probe read-only S117** (`scratchpad/probe_ctx_cluster_s117.py`, sobre data persistida): los
   `ctx_cluster` de Llaima (artefacto N) y Lastarria (Lazufre real) son **indistinguibles** —
   Llaima medNpx=1 / medVRP=0.043 / 83% single-pixel; Lastarria medNpx=1 / medVRP=0.051 / 93%
   single-pixel. No hay eje físico (n_pixels, VRP) que los separe (A83).
2. **Reproc real S106** (`docs/superpowers/specs/2026-06-11-ancla-espacial-honesta-design.md` §8): el
   A/B vent (A) vs nti_peak (B) ya se corrió, 5 vols × 90 d. **Brazo B (nti_peak) descartado
   formalmente**: en nevados de señal débil el campo NTI es plano → su máximo cae en ruido/lago →
   offN EMPEORA (Villarrica 884 vs 748 base; **Llaima 2263 m**). El offset NW real de Lastarria se
   **conserva vía `ctx_cluster`** (300/453 records).

**Conclusión.** Las dos únicas anclas alternativas están agotadas: snap-a-vent rompe Lastarria (cat-b
real); nti_peak es ruido en NTI plano (S106). El `ctx_cluster` es lo que preserva el cat-b real. → es
el **instance-en-posición de A82**: a 1 km, en régimen débil, foco real ≡ ruido topográfico. Cerrado
como resultado negativo con datos. Lección A50: la respuesta (el A/B de S106) ya estaba en el repo —
casi se re-corre el mismo experimento. El único "fix" restante sería un hack per-volcán (solo Llaima),
descartado por A83 (gate per-volcán disfrazado, menos clon-literal) para una mejora cosmética.
</content>
