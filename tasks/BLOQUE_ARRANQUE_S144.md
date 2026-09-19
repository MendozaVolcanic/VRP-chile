# Bloque de arranque S144

> Cierre de S143 (2026-09-17 a 2026-09-19 16:40 UTC, hora del servidor). La S143 corrió en la
> conversación que se llamaba "vrp 141" (continuación de S141), **renombrada "vrp 143 (A/B D22 D25)"**;
> "vrp v142" es la S142 cerrada y "Retomar" (19-sep) sólo verificó, sin tocar el repo. `main` en
> `cd3c254d5` al empezar este cierre, verificado igual al remoto con `git ls-remote`. Sin PR abiertos.
> Suite local al cerrar: **1539 passed, 4 skipped, 2 xfailed**. Tags de la sesión:
> `pre-s143-ab-d22-d25` y `pre-s143-ab-d22-d25-r2` (código de pipeline idéntico, sólo cambia el workflow).
>
> **Trabajo en curso al fijar este estado**: ninguno en VRP Chile. En `mirova-tif-archive` falta ver
> la primera captura real con el arreglo de TIF vacíos (PR #3 de ese repo, 15:30 UTC): desde entonces
> MIROVA no publicó nada nuevo (su `Last-Modified` quedó en 14:57 UTC, consultado a las 16:37) y el
> poller corre en verde con `STATUS: no_changes`, sin ningún "inválido" en los logs.
>
> Bitácora completa con la evidencia de cada paso: `docs/audit_s143/BITACORA_S143.md`.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **A/B D22/D25 (VIIRS 375, 9 volcanes, jun-ago 2026, 6 brazos)** | **corrido, evaluado y verificado: NO ADOPTAR** | #703; `experiments/_s143_evaluador/RESULTADO_AB_S143.md`, `VERIFICADOR_VEREDICTO.md`; `docs/HYPOTHESIS_LOG.md` H_S143_D22_D25 |
| Brazo `literal` | cumple sobre-publicación (0,917 a 0,547) y magnitud (0,77 a 0,94); **pierde 5 noches** | idem; las 5 son "con cota", 0 sin cota |
| Atribución por ablación | todo el descenso en negativos viene de **apagar `keep_peak`** (−0,373); D22 +0,202 y D25 +0,052 en contra; D22 recupera recall sólo con `keep_peak` apagado; D25 mueve la magnitud; D2 casi nulo | recuento del verificador, `experiments/_s143_evaluador/verificador_veredicto/` |
| Probe de las 12 noches de S135 | corrido y verificado; cerró los brazos sin agregar ninguno | #685, #689, #690; `experiments/_s143_probe_12_noches/` |
| Evaluador del A/B (TDD, 36 tests, 25 de 27 mutaciones muertas) | en main; parámetros congelados en `parametros.json` | #686, #687, #691, #692, #693, #697, #698, #701 |
| Pre-registro v2 (18 hallazgos corregidos, 9 volcanes) | en main | #684, #688, #690; `docs/PREREGISTRO_AB_D22_D25_S143.md` |
| Decisiones de la cota (Nicolás, 2026-09-18) | congeladas y vigiladas por tests | #697: cota también en el brazo; posición `final_hotspot` en records `test1_roi` |
| Cobertura de credibilidad por sensor y volcán | en main | #695; `docs/audit_s143/COBERTURA_MIROVA.md`: V375 100 % de 129 pasadas con alerta; 0 alertas sin record |
| Pérdidas de VIIRS 750 | **5 de 5 son D25** (cráter detectado, magnitud 0,0 MW) | #696; `docs/audit_s143/PERDIDAS_V750.md` |
| Arreglo de TIF vacíos en `mirova-tif-archive` | en main de ese repo; 9 vacíos listados, **ninguno borrado** | mirova-tif-archive #3; `docs/TIF_VACIOS_S143.md` de ese repo |
| Disco local | lo llené yo con un `git pull` del archivo de TIF (17 GB) y lo recuperé | 0,03 GB → 9,8 GB libres; regla nueva en memoria |
| Tramo de confirmación fuera de muestra (2026-09-01 a 09-15) | **no corrido** | el pre-registro lo pide sólo para un brazo ganador, y no hubo |

### Medición de factibilidad hecha después del cierre (2026-09-19 18:30 UTC, exploratoria, sin commitear el script)

Pasadas nocturnas VIIRS 375 de producción entre 2026-09-14 y 2026-09-19 (TIF UTM de MIROVA con hora de
adquisición desde 2026-09-14 06:36): **290** nocturnas; **122** con TIF UTM a ±15 min; **58** con alerta de
MIROVA, de ellas **23** con TIF; **81** con el patrón de `keep_peak` separado (fuente `test1_roi`, cúmulo de 1
píxel a más de 0,5 km del `final_hotspot`), **34** con TIF; y sólo **2** que además tienen alerta de MIROVA y
TIF. **Consecuencia para la decisión 1**: la prueba directa sobre alertas tiene hoy 2 casos. Opciones: esperar
más días de TIF UTM, o diseñar la medida sobre las 34 pasadas con TIF (con y sin alerta: en las sin alerta,
¿hay en el TIF de MIROVA calor donde está nuestro píxel de `keep_peak`?). Repetir el conteo con script
versionado antes de usar estos números.

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **Siguiente frente: `keep_peak`.** Quitarlo es lo único que baja la sobre-publicación, y la regla de cero pérdidas le cobra 5 noches cuya "coincidencia" con MIROVA es un píxel a 2,2-2,8 km que cae por azar en el radio | (a) medir CON DIRECCIÓN: en esas 5 noches y en una muestra de negativos, ubicar en el TIF UTM de MIROVA (desde 2026-09-14, A106) dónde está el objeto que vio y ver si coincide con el píxel de `keep_peak`; (b) cambiar la regla de cota ahora; (c) dejar `keep_peak` como está | **(a)**. (b) sería mover la regla después de ver datos; (c) deja la sobre-publicación en 92 %. Ojo: el TIF UTM sólo existe desde el 14-sep, así que las 5 noches de junio-julio no tienen TIF; hace falta una muestra nueva desde el 14-sep |
| 2 | ¿Llevar D25 (fondo por vecinos) a VIIRS 750? | plan + flag V750 apagado + su propio A/B; o esperar | **plan y flag ahora, A/B después**: las 5 pasadas de V750 que no reproducimos son D25 puro (`PERDIDAS_V750.md`), y D25 no toca `keep_peak`. Toca pipeline: tag + tu confirmación (A45) |
| 3 | Los 9 TIF/PNG vacíos del archivo | borrar / dejar | **dejar**: no molestan y están documentados con el TIF bueno de cada pasada |
| 4 | Token de Earthdata: **vence 2026-10-03 07:18 UTC** (verificado 17-sep en el healthcheck) | | renovarlo esta semana (credencial, lo haces tú) |
| 5 | Cron externo del NRT y correo a Coppola | | siguen como en S142: `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md` y `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` |
| 6 | Sesión "Retomar" del panel | archivar / dejar | archivarla: no dejó nada pendiente |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| Una cota de distancia escalar no identifica el objeto: en el A/B, el control "coincidía" con MIROVA por un píxel a 2-3 km que caía por azar en su radio. Para decidir si es el mismo objeto hace falta dirección | proyecto | `CLAUDE.md` **A107** |
| 54 de 54 jobs verdes y aun así 3 de 108 quedaron cortos por cortes de NASA (`SEARCH_CMR_TIMEOUT`). El conteo de cobertura por brazo es obligatorio antes de mirar un veredicto, y se automatizó en `bajar_tramos.py` | proyecto | `CLAUDE.md` **A108** |
| Un probe barato sobre los casos que motivan un A/B caro cambia el diseño: evitó correr brazos que no podían responder la pregunta y mostró que los existentes sí la respondían | proyecto | bitácora §8 |
| El formato de los artefactos es parte del instrumento: dos desfases de nombre (prefijo y tramo) habrían dejado media ventana afuera sin error | proyecto | bitácora §8; tests en `tests/test_evaluador_ab_s143.py` |
| "Noches recuperadas" crece con cualquier publicación: sin la cota y el costo en negativos al lado, el peor brazo parece el mejor | proyecto | bitácora §8 |
| Para que nos crean hay que reproducir todo lo que MIROVA publica; lo que mejora y MIROVA no tiene va a `experimental`, separado | **principio de Nicolás** | memoria `feedback_s143_primero_igualar_a_mirova` |
| No hacer `pull` ni clonar repos de datos gigantes: leer y escribir por la API de GitHub, y normalizar a LF antes de subir | **workspace** | memoria `feedback_s143_no_pull_repo_gigante` |
| Al continuar una conversación vieja como sesión nueva, renombrarla al empezar | **workspace** | memoria `project_s143_estado` |
| Los escapes dentro de un heredoc de Python volvieron a romper archivos dos veces (bytes nulos, salto de línea literal): para ediciones con secuencias de escape, usar el editor | **workspace** | ya existía (S140 regla 4); se repitió |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| Ningún brazo del A/B cumple los tres criterios; el conflicto es `keep_peak` contra la cota escalar | **CONFIRMADO** (evaluador + verificador) |
| Con `final_hotspot` en todos los records, `literal` no perdería ninguna noche | **CONFIRMADO** por el verificador; no cambia el veredicto (la posición se congeló antes) |
| El píxel de `keep_peak` que coincide con MIROVA en esas 5 noches NO es el objeto que MIROVA vio | **SOSPECHA**: la cota no tiene dirección; se resuelve con la decisión 1 |
| El efecto casi nulo de D2 depende de la conectiva `min` | **SOSPECHA** (verificador) |
| Chaitén empeora en magnitud con `literal` (0,296 a 0,481; n < 30) | **CONFIRMADO** el número, sin interpretar por n |
| D25 en VIIRS 750 cerraría las 5 pasadas que no reproducimos | **SOSPECHA**: el mecanismo es el mismo (5 de 5), el tamaño no está medido |
| El poller de TIF sigue guardando capturas buenas con el arreglo | **SOSPECHA** hasta ver la primera captura real posterior al 19-sep 15:30 UTC |

## e. Lo que ya está cerrado y no hay que rehacer

- **El A/B D22/D25 de junio-agosto está corrido y verificado.** No relanzarlo con los mismos brazos: el resultado es firme en esa ventana.
- **No agregar el brazo "sin compuerta en la máscara contextual" ni el de "Test 1 sin filtro"** por la diferencia 11 contra 10 del probe: el verificador mostró que depende del campo de posición.
- **Las 12 noches perdidas por S135 están explicadas**: las recupera D22 con `keep_peak` apagado; el control ya las publicaba.
- **La cota y la posición están decididas** (2026-09-18) y congeladas; no se reabren sin un pre-registro nuevo.
- **La cobertura de credibilidad está medida** en el régimen actual (`COBERTURA_MIROVA.md`).
- **Las pérdidas de VIIRS 750 están explicadas** (D25, 5 de 5).
- **El arreglo de TIF vacíos está hecho**; no rehacerlo.

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S144. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main      (deben coincidir)
   gh pr list --state open
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date           (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1          (base: 1539 passed)
   Poller de TIF (NO hacer pull de ese repo, pesa 17 GB):
   gh api "repos/MendozaVolcanic/mirova-tif-archive/commits?per_page=5&since=2026-09-19T15:31:00Z"
   -> debe haber commits "new MIROVA snapshot" y ninguna fila de 0 bytes nueva en index.csv.

2. LEE EN ORDEN: CLAUDE.md del proyecto (A107 y A108 nuevas) · tasks/BLOQUE_ARRANQUE_S144.md ·
   docs/audit_s143/BITACORA_S143.md · experiments/_s143_evaluador/VERIFICADOR_VEREDICTO.md ·
   docs/HYPOTHESIS_LOG.md entrada H_S143_D22_D25.

3. TRABAJO EN ORDEN (lo que Nicolás decida en §b manda):
   a) Frente keep_peak con dirección: pre-registrar una medida que ubique, en el TIF UTM de MIROVA
      (desde 2026-09-14), el objeto que MIROVA vio, y compararlo con el píxel de keep_peak y con el
      final_hotspot. Muestra nueva desde el 14-sep (las 5 noches de junio-julio no tienen TIF UTM).
      Verificador con contexto limpio antes y después de correr.
   b) Si Nicolás lo aprueba: plan + flag apagado de D25 para VIIRS 750 (tag + confirmación, A45),
      con su propio A/B pre-registrado.

4. REGLAS DURAS: nada al pipeline ni a mirova_equivalent.yaml sin tag defensivo y confirmación
   (A45); criterio escrito antes de correr y verificador limpio antes y después; conteo de cobertura
   por brazo antes de mirar un veredicto (A108); publicar = predicado del dashboard con node (A97);
   ningún número a mano (S91); esperar el CI con conclusión antes de mergear; correr la suite tras
   editar docs que un test lee; nada de pull a repos de datos gigantes; primero igualar lo que
   MIROVA publica, lo demás al perfil experimental.

5. SI LA SESIÓN NO ALCANZA: deja el pre-registro de (a) escrito y verificado aunque no se corra, y
   cierra con /cierre.
```
