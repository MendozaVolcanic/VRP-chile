# Bloque de arranque S204 (escrito por S203, 2026-11-27 ~18:20 UTC)

> El bloque anterior (S203, escrito por S202) queda como histórico en `tasks/BLOQUE_ARRANQUE_S203.md`. Detalle de S203 en
> la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S203, arriba) y en la nota viva
> `D:\vrp-trabajo\temporales\s203\s203_nota_viva.md`. S203 cerró por contexto (~553 mil tokens).
> **Estado fijado con trabajo ajeno en curso:** la corrida NRT programada de las 17:50 UTC (run 46044996773, producción,
> no de S203) seguía corriendo; sus jobs terminados ya habían commiteado (Chaitén, PlanchonPeteroa, Tupungatito, Cordón
> Caulle, Villarrica, Láscar...). Ningún agente, cadena de merge ni tanda de S203 quedó viva (vigilante detenido,
> worktrees s203-* quitados).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.120** (#1140, #1142, #1143, #1144 de S203) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| #1140 manifiesto t9 y t10 | en main v1.117: barrido del piso completo hasta el 23-nov | `experiments/_s196_lab_piso/MANIFIESTO_TANDAS.json` |
| Unión del barrido | 30.047 records por brazo, 0 problemas; escenas de validez distinta siguen 2 (Llaima 05-30 02:55, Lastarria 09-19 02:10), oct-nov 0 nuevas; R5C-103 OK en las 9 carpetas | `D:\vrp-trabajo\temporales\s203\union_t10\`, `medir_invalidas_hasta_nov.txt`, `chequeo_r5c103.txt` |
| #1142 calibrar | en main v1.118: **ELEGIDO s 3 y piso 0,0025**, tres frenos verdes; contraste con evaluador S200c igual | `experiments/_s196_lab_piso/RESULTADO_CALIBRAR_S203.md`, `resultado_calibrar_s203.json`, `salida_tasas_calibrar_s203.txt` |
| #1143 respaldo LANCE | en main v1.119 (merge d2041c9e3): si CMR falla, dice estar caído o le faltan ≥3 archivos de hoy o ayer, las pasadas NRT se buscan en el buscador propio de LANCE (mismo enlace y token). **Verificado en producción** en la NRT de las 17:50: en Láscar recuperó Terra +2, Aqua +1, NOAA-20 +1, NOAA-21 +1 (375 y 750); descargas OK con el token real; la Aqua nocturna 08:30 del 27-nov es record publicado | `pipeline/lance_respaldo.py`; log `D:\vrp-trabajo\temporales\s203\log_nrt_lascar_1750.txt`; verificador 3 pasadas `D:\vrp-trabajo\temporales\s203\verif_lance\VEREDICTO.md`; mutaciones 33/33 `D:\vrp-trabajo\temporales\s203\mut_lance\salida_mutar5.txt` |
| #1144 laboratorio encendido | en main v1.120 (67c653d2d): `laboratorio.yaml` = brazo p250 salvo nombre y carpeta (s 3, piso 0,0025, zona A encendida); tag `pre-s203-lab-piso`; ningún workflow lo corre | verificador `D:\vrp-trabajo\temporales\s203\verif_lab\VEREDICTO.md` |
| Datos del laboratorio (p250) | t11 run 46013914740 (15 al 28-feb) y t12 run 46013941632 (24 al 26-nov): 1 intento, 13/13 success, controles IDÉNTICOS; unión 15-feb a 26-nov 31.933 records, 0 problemas | `D:\vrp-trabajo\temporales\s203\lab_p250_completo\`; script `D:\vrp-trabajo\temporales\s203\unir_p250\unir_lab_p250.py` (sólo en disco) |
| **Paso 5, vara NHI (S194 sellada)** | **NO CUMPLE**: exceso NHI con p < 0,05 sólo en Planchón-Peteroa (4 de 12 noches «sólo laboratorio» con alerta NHI contra 2 de 42, p 0,017); con poder 4 volcanes (Tupungatito, PP, Chillán, Chaitén); persistencia 0,637 contra sorteo 0,695 (p 1,0, 912 extras); control ±15 días nulo (0 volcanes); cobertura desigual 3,9 a 4,6 % (bajo 5 %) | `D:\vrp-trabajo\temporales\s203\evaluar_nhi\resultado.json`, `salida.txt` (corrido desde main 67c653d2d, --fin 2026-11-26). **No está en el repo ni comunicado a Nicolás con detalle** |
| PR abiertos | sólo #913 (borrador viejo) | `gh pr list` |
| Issues | #1141 (sombra de los 34: causa caída de CMR del 26-nov, datos sí subidos; se cierra con una corrida verde), #1106 (cierra 30-nov), #943, #813 | `gh issue list` |
| Disco | C: 28 GB, D: 22 GB | `df -h` |
| Sin commitear en `loop/activo` | sólo lo de siempre, ajeno: `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/` y `data/`, `experiments/_s176_codex/` (nunca tocar) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Laboratorio NO CUMPLE: ¿qué hacemos con la zona del cráter? | (a) aceptar NO CUMPLE: no llega a cron, se anota en `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 (MEJ-5) con los números y el exceso mínimo detectable por volcán (lo que manda el pre-registro S194 §4); (b) pre-registro nuevo (segundo intento) con otra palanca; (c) mirar Planchón-Peteroa aparte | **(a)** ahora (es lo sellado, no admite re-correr con otro umbral); (c) como pregunta abierta para el experimental, sin decidir nada |
| 2 | ¿El laboratorio queda encendido (#1144) aunque NO CUMPLE? | dejarlo (no corre, no publica) / revertir a zona apagada | Dejarlo: no corre ni publica; revertir sólo si se decide otra palanca |
| 3 | Ronda 6 de Codex | sobre la cadena barrido, calibrar, evaluar y el respaldo LANCE / no por ahora | Sobre el respaldo LANCE (código de producción nuevo) y la evaluación NO CUMPLE; Nicolás dijo «sigue con lo que recomiendes» pero el lanzamiento no se hizo |
| 4 | Heredadas | #813 (VIIRS de día), NODD (no), P0 parte 4, traza `nrt_reemplazado`, clave FIRMS, PAT en settings.json | las de los bloques S201 a S203 |

**Ya decidido en S203 (no volver a preguntar):** «sigue con lo que recomiendes» (2026-11-27 ~12:40 UTC) = sí al respaldo
LANCE (decisión 2 del bloque S203) y sí a fijar el piso en el laboratorio; «continua con todo»; «cuando termine eso
inicia tú misma la siguiente sesión y continúa con todo lo necesario» (~18:00 UTC).

**Preguntas de Nicolás de S203 sin respuesta explícita:** ninguna («como vas?» respondida; la del apagón del PC
respondida: no fue la causa, el NRT corre en GitHub).

## c. Lo aprendido

- **REGLA GENERAL (reincidencia de A25):** leer `origin/main` horas después de un `fetch` da datos viejos: dije que
  faltaban las pasadas VIIRS del 27-nov y estaban. `git fetch` justo antes de cada `git show origin/...` de datos vivos.
- **REGLA GENERAL:** pasarle a pytest la lista de `grep -l` sin filtrar `test_*.py` da «no tests ran» y parece verde;
  filtrar siempre con `--include="test_*.py"` y leer el conteo.
- **REGLA GENERAL (contador de mutaciones):** `pytest.raises` que falla dice «DID NOT RAISE», no AssertionError; para que
  la mutación cuente, escribir la prueba con un `resultado(f)` que capture y una aserción explícita.
- **Proyecto:** `search/health` de CMR sano no significa catálogo completo: al volver el indexador cataloga lo nuevo y no
  rellena el hueco (MYD021KM día 331: 151 en LANCE, 84 en CMR, con health sano). En días sanos CMR lista uno más que la
  carpeta de LANCE (8 productos, 21 y 23-nov).
- **Proyecto:** el buscador por región de LANCE es laxo (devuelve gránulos a cientos de km) y su GRing de 4 esquinas no
  reproduce a CMR; con 100 km de tolerancia conserva 122 de 123 pasadas de CMR. nrt3 y nrt4 producen el mismo gránulo
  con distinta marca de producción: el enlace debe usar el host del ítem.
- **Proyecto:** cron-job.org despacha el NRT sólo de 01:10 a 12:10 UTC (ventana nocturna); en la tarde sólo el cron de
  GitHub, esporádico (13:39 y 22:48 el 26-nov). Un hueco de NRT por la tarde no es falla.
- **Proyecto:** la vara NHI (S194) invalida con más de 5 % de noches de cobertura desigual por volcán; para medir desde
  el 15-feb hubo que completar el laboratorio con el mismo workflow del barrido y 3 brazos (sin zona, control, p250).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** NO CUMPLE de la zona A con s 3 y piso 0,0025 (resultado.json).
- **CONFIRMADO:** el respaldo LANCE disparó y descargó en producción (log de Láscar 17:50).
- **SOSPECHA:** la pasada NOAA-21 05:54 del 27-nov (GRing contiene a Láscar) fue recuperada pero no dejó record; ver en
  el log si es «sin_record» por borde o si quedó descartada antes; puede ser que el gránulo recuperado haya sido otro
  (04:12).
- **SOSPECHA:** en VIIRS 750 el respaldo puede dejar records «escena_invalida» de 0 MW de gránulos de borde que CMR habría
  excluido; contar en los JSON del 27-nov.
- **SOSPECHA (del verificador):** el conteo a CMR (`CMR-Hits`) no tiene cortacircuito propio; poco probable que se cuelgue
  sin que falle antes la búsqueda.
- **CONFIRMADO:** Terra deja de observar el 2026-12-01 (registrado en #1138).

## e. Ya cerrado, no rehacer

- Manifiesto completo (#1140), calibrar (#1142, ELEGIDO 0,0025), respaldo LANCE (#1143), laboratorio encendido (#1144).
- «Sin NRT de 12:10 a 17:50 UTC» no es falla (cron-job.org sólo de noche).
- #1141: causa = caída de CMR del 26-nov (revisar_sombra: «catálogo de CMR vacío»); los datos se subieron.
- La vara NHI corrió con el instrumento sano (NHI de 9 volcanes cargado, control nulo, cobertura bajo 5 %): NO CUMPLE no
  es «falló el instrumento».

## f. Prompt para S204

```
Retomas VRP Chile como sesión dueña del loop (S204). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S203 cerró y no trabaja más.
Nicolás autorizó seguir sin preguntar cada paso, hasta 900 mil tokens por sesión (cierre preferido a los 550 mil).

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.120 o más); gh pr list; gh issue list;
   df de C: y D:. Lee tasks/BLOQUE_ARRANQUE_S204.md (rama loop/activo) y la entrada S203 de tasks/LOOP_OBJETIVOS.md §6;
   nota viva D:\vrp-trabajo\temporales\s203\s203_nota_viva.md.
2. Trabajo, en orden:
   a. Llevar a Nicolás el NO CUMPLE del laboratorio explicado como geólogo (qué es la zona del cráter, qué vio de más,
      por qué NHI no lo confirma salvo en Planchón-Peteroa, qué dice la persistencia) y la decisión 1 del bloque con la
      recomendación (a). Mientras responde: PR que guarda el resultado en experiments/_s196_lab_piso/ (resultado.json
      de D:\vrp-trabajo\temporales\s203\evaluar_nhi\, unir_lab_p250.py y su salida) con fila de ficha; si dice (a), el
      apunte en docs/BEYOND_MIROVA_EXTENSIONS.md §12 (MEJ-5) con números y exceso mínimo detectable (evaluar.py poder).
   b. Revisar el respaldo LANCE en producción: en las corridas NRT de hoy y mañana buscar LANCE_RESPALDO en los logs;
      contar records «escena_invalida» nuevos en VIIRS 750 del 27-nov; aclarar la NOAA-21 05:54 de Láscar.
      Ver que #1141 se cierre con la sombra de esta noche.
   c. Ronda 6 de Codex: proponerla a Nicolás sobre el respaldo LANCE y la evaluación; no lanzarla sola.
3. Reglas duras: A45; merges con D:\vrp-trabajo\temporales\s195\merge\uno.sh en serie (fila_<N>.txt antes; versión
   siguiente a la de main; fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python
   en heredoc con barras invertidas (Write o Edit); un vigilante por corrida; nunca pedir ni recibir tokens por el chat;
   verificador limpio en todo PR propio que toque un evaluador o el pipeline; no agregar líneas al modal de
   frontend/index.html (citas G8); git fetch antes de leer origin/... de datos vivos.
4. Cierra con /cierre al llegar al umbral de contexto y deja el prompt de S205.
```
