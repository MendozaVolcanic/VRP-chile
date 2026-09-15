# Fase 1, paso 1: probe por etapa del vecino del foco (VIIRS 375 m). Resultados S141

> ⚠️ **CORREGIDO tras el verificador con contexto limpio** (`VERIFICADOR.md`, 2026-09-15). Los números
> se reproducen exactos, pero **las lecturas post hoc que la primera versión de este informe daba como
> patrón por estrato no se sostienen** y quedan retiradas (§5). El veredicto pre-registrado sigue
> siendo INDETERMINADO. **Este probe no justifica ningún brazo de A/B**: justifica rehacer el
> instrumento (§6). La primera versión se conserva en la historia de git.

Corrida válida: GitHub Actions run **34929024703** (2026-09-15, 04:29 a 04:38 UTC, commit `d640e82bd`).
La corrida anterior (34928488409) salió en verde sin procesar ninguna pasada y **no se usa** (§7).
Plan y criterio pre-registrado: `docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md`;
hipótesis `H_S141_VECINO_FOCO` en `docs/HYPOTHESIS_LOG.md`.

Todos los números salen de scripts sobre los artefactos commiteados (regla S91): `juntar.py` escribe
`criterio_total.json` y `analisis_posthoc.py` escribe `posthoc.json`. Entre corchetes va la clave.

## 1. Lo que se puede decir

MIROVA suma los píxeles tibios que rodean al foco; nosotros publicamos uno. Este probe quería decir en
qué etapa del pipeline se pierden esos vecinos. **No lo logró**, por dos razones que se ven en los datos:

- **La muestra no garantiza que MIROVA y nosotros miremos el mismo foco.** El pareo con el OSF sólo exige
  que nuestro cúmulo esté en el cráter, no que el píxel caliente de MIROVA lo esté. En Nevados de Chillán
  el píxel caliente de MIROVA quedó a **13,3 a 17,2 km del cráter** en los cuatro candidatos: MIROVA estaba
  sumando otra anomalía, lejos del cono. En el resto de los volcanes queda a menos de 1,8 km (mediana
  por volcán). Medido con `volcanoes.yaml` y las coordenadas del OSF de cada pasada.
- **El instrumento ordena en fila etapas que en el pipeline corren en paralelo.** La ruta contextual
  (Tests 2 y 3, segundo pase) y la ruta del Test 1 no son una secuencia, así que "perdido en la etapa X"
  depende del orden que yo elegí y no del pipeline (`VERIFICADOR.md` §4).

Lo que sí queda en pie: la corrida procesó las 40 pasadas sin descartes; BT, coordenadas y máscaras son de
la escena completa y del mismo momento del cálculo; y el control, medido contra los vecinos alcanzables,
incluye 17 de 23 (`M1`), así que la captura del cúmulo funciona.

## 2. Veredicto pre-registrado: INDETERMINADO

[`criterio_total.json` → `criterio`]

| | total | focal | nevado |
|---|---|---|---|
| candidatos / controles | 29 / 11 | 20 / 9 | 9 / 2 |
| control | FALLA | FALLA | FALLA |
| etapa (criterio 1) | PALANCA:nunca_candidato (0,644) | PALANCA:nunca_candidato (0,607) | PALANCA:nunca_candidato (0,722) |
| fondo (criterio 2) | PARCIAL (0,411) | FONDO_LOCAL_CIERRA_BRECHA (0,544) | PARCIAL (0,347) |
| veredicto | INDETERMINADO | INDETERMINADO | INDETERMINADO |

Descartes: 0 de 40 [`descartes`]. Los criterios 1 y 2 tampoco se pueden leer como tendencia: el 1 depende
del orden de etapas (§1) y el 2 suma ruido (§3, D2).

## 3. Defectos del instrumento

Declarados por mí antes de ver el total (en las 4 pasadas de Chaitén):

- **D1, el control no podía aprobar**: exigía ≥ 50 % de los 8 vecinos incluidos; con `pc_n ≤ 4` el máximo
  alcanzable es 3 de 8.
- **D2, el aporte con fondo local incluye ruido**: sumaba el exceso positivo de vecinos que ningún test
  marcó; en un campo con ruido la mitad de los píxeles supera la media de sus vecinos.

Encontrados por el verificador (`VERIFICADOR.md` §4), que yo no vi:

- **D3, etapas en secuencia**: `ORDEN` pone en fila la ruta contextual y la del Test 1, que corren en
  paralelo. Comprobado con entradas sintéticas.
- **D4, la máscara del Test 1 no es un test por píxel**: marca cualquier píxel con exceso sobre la mediana
  del anillo dentro del disco de 3 km. Contarla como "marcado" hace que la corrección M3 no corrija D2, y
  que "perdido en el cúmulo" sea casi siempre un píxel de esa máscara.
- **D5, el pareo no filtra la posición del foco de MIROVA** (Nevados de Chillán, §1).
- **D6, la brecha mezcla dos códigos**: el VRP publicado sale del backfill y los vecinos del código de hoy.
- **D7, el control P3 compara dos magnitudes distintas**: `pub_n` cuenta el núcleo F5 y `hoy.pc_n` cuenta el
  cúmulo. "20 de 29 siguen publicando 1 píxel" no significa eso; además 36 de 40 pasadas salen hoy en modo
  de un píxel.
- **D8, el fondo local excluye el halo del Test 1** como si fueran píxeles alertados.
- **SOSPECHAS del verificador, sin verificar**: que el cúmulo capturado no sea el publicado cuando la llamada
  del Test 1 vuelve vacía, y que salga `nunca_candidato` cuando el primer pase no corrió.

## 4. Números post hoc (se conservan, sin interpretación por estrato)

[`posthoc.json`; definiciones en el encabezado de `analisis_posthoc.py`]. Se dejan porque el verificador los
reprodujo exactos, pero ninguno se lee como patrón (§5).

| | total (20, `hoy_1px`) | focal (12) | nevado (8) |
|---|---|---|---|
| M2 fracción nunca candidato, `Npix − 1` vecinos más calientes | 0,431 | 0,200 | 0,629 |
| M3 brecha, vecinos marcados y perdidos, fondo local | 0,412 | 0,602 | 0,016 |
| M5 exceso sobre fondo local (K) | 2,16 | 2,84 | 1,61 |
| M5 exceso sobre anillo (K) | 1,40 | −2,27 | 4,31 |
| M6 distancia centro a píxel OSF (km, mediana) | 0,164 | 0,161 | 0,186 |

## 5. Lecturas retiradas

| lo que decía la primera versión | por qué se retira |
|---|---|
| "En focales los vecinos pasan algún test y el ensamblado los deja fuera" | "perdido en el cúmulo" es casi siempre un píxel de la máscara del Test 1, que no es un test por píxel (D4); y la etapa depende del orden elegido (D3) |
| "En focales los vecinos son 2,3 K más fríos que el anillo" | depende de Planchón-Peteroa e Isluga (`VERIFICADOR.md` §3) |
| "En nevados los vecinos están 4,3 K sobre el anillo" | lo sostiene sólo Nevados de Chillán (27 de 35 vecinos); sin él el exceso del estrato es −8,3 K (−9,66 K según el verificador sobre su subconjunto) y el signo se invierte |
| "En nevados se pierden en el Test 1" | los 13 casos son de Nevados de Chillán y la etiqueta es un artefacto (D3, D4) |
| "El centro está a 0,16 km del píxel de MIROVA: miramos el mismo foco" | la distancia es chica por construcción, porque el centro se elige como el píxel más cercano al punto del OSF; en Nevados de Chillán ese punto está a 13 a 17 km del cráter (D5) |
| "20 de 29 candidatos siguen publicando 1 píxel hoy" | compara el núcleo F5 con el cúmulo (D7) |
| Propuesta de A/B con fondo por vecinos (D25) y cúmulo que conserve los vecinos marcados (D19) | se apoyaba en las lecturas anteriores |

## 6. Siguiente paso: instrumento v2 (no un A/B)

Lo que el v2 tiene que cambiar, según `VERIFICADOR.md` §6 (ocho puntos; el detalle y los umbrales están ahí), antes de pre-registrar un criterio nuevo:

1. Filtrar la muestra por la **posición del foco de MIROVA**: su píxel caliente a ≤ 0,75 km de nuestro píxel pico o del cráter, reportando las pasadas excluidas.
2. Rotular cada vecino **dentro de la ruta que publicó** (contextual o Test 1), no por una secuencia inventada; la máscara del Test 1 no cuenta como "marcado".
3. Guardar los índices del **cúmulo publicado** (de qué llamada vino) y un booleano por etapa que corrió, en vez de inferirlo de un `None`.
4. Tomar como centro **nuestro píxel pico del cúmulo publicado**, con la distancia al punto del OSF como variable de pareo.
5. Medir el **núcleo F5 de hoy** (`f5_core_vrp_mw`, su conteo, `single_pixel_mode`) y calcular la brecha contra lo publicado **en la misma corrida**.
6. Calcular el **fondo local con la máscara de alertas que se publicaría** (ruta ganadora), no con la unión de todas las etapas.
7. **Contraste**: medir el exceso también sobre los vecinos restantes y sobre un píxel de control lejos del foco.
8. Pre-registrar **por volcán además de por estrato**, con mínimo de pasadas por volcán y dejando uno fuera a la vez.

Muestra nueva: las 40 pasadas de esta corrida ya se miraron.

## 7. La corrida que no se usa

Run 34928488409: los 8 jobs salieron `success` en ~1 minuto sin procesar ninguna pasada. El runner
envolvía `sys.stdout` y el probe S135 lo volvía a envolver al importarse; el primer envoltorio quedó
huérfano, al recolectarse cerró la salida y `run_pipeline.py` cayó con "I/O operation on closed file".
Sin `set -o pipefail`, `tee` devolvió 0. Arreglado en PR #672 con dos tests que fallaban antes del cambio.

## 8. Reproducir

```bash
gh run download 34929024703 -R MendozaVolcanic/VRP-chile -D experiments/_s141_fase1_probe/artefactos
python experiments/_s141_fase1_probe/juntar.py
python experiments/_s141_fase1_probe/analisis_posthoc.py
```
